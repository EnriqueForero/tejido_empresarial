"""El endpoint /api/diagnostico en un despliegue de producción.

Comprueba la puerta de acceso (para que no quede abierto en un dominio público)
y que, con datos reales mal configurados, señale el primer paso que falla con
una instrucción concreta.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from backend.database import Session as _SesionSnowpark

# Sin el conector el servicio nunca se considera «configurado»: el diagnóstico se
# detiene en el paso «conector» y el health reporta configuración incompleta. Las
# pruebas que dependen de eso sólo tienen sentido si el conector está instalado.
CONECTOR_INSTALADO = _SesionSnowpark is not None

VARIABLES_SNOWFLAKE = [
    "SF_ACCOUNT", "SF_USER", "SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE",
    "SF_PRIVATE_KEY_B64_1", "SF_PRIVATE_KEY_B64_2",
    "SF_PRIVATE_KEY_PATH_1", "SF_PRIVATE_KEY_PATH_2",
    "SF_PRIVATE_KEY_PASSPHRASE_1", "SF_PRIVATE_KEY_PASSPHRASE_2",
]


def _app_en_produccion(monkeypatch, **variables: str):
    """Recarga la API como si estuviera en Railway (sin modo demostración)."""
    monkeypatch.setenv("APP_DEMO_MODE", "false")
    monkeypatch.setenv("APP_ENV", "production")
    for nombre in ("APP_BASIC_USER", "APP_BASIC_PASSWORD", "APP_DIAG_TOKEN", *VARIABLES_SNOWFLAKE):
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in variables.items():
        monkeypatch.setenv(nombre, valor)
    import backend.database
    import backend.main

    importlib.reload(backend.database)
    modulo = importlib.reload(backend.main)
    return modulo, TestClient(modulo.app)


@pytest.fixture(autouse=True)
def restaurar_modo_demostracion():
    """Deja los módulos como los esperan las demás pruebas."""
    yield
    import os

    os.environ["APP_DEMO_MODE"] = "true"
    os.environ["APP_ENV"] = "development"
    import backend.database
    import backend.main

    importlib.reload(backend.database)
    importlib.reload(backend.main)


def test_cerrado_si_el_despliegue_no_esta_protegido(monkeypatch) -> None:
    _, cliente = _app_en_produccion(monkeypatch)
    respuesta = cliente.get("/api/diagnostico")
    assert respuesta.status_code == 403
    detalle = respuesta.json()["detail"]
    assert "APP_BASIC_USER" in detalle and "APP_DIAG_TOKEN" in detalle


def test_abierto_con_token_y_señala_las_variables_que_faltan(monkeypatch) -> None:
    _, cliente = _app_en_produccion(monkeypatch, APP_DIAG_TOKEN="token-de-prueba")
    assert cliente.get("/api/diagnostico").status_code == 403          # sin token
    assert cliente.get("/api/diagnostico?token=otro").status_code == 403

    respuesta = cliente.get("/api/diagnostico?token=token-de-prueba")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "snowflake"
    assert cuerpo["todo_ok"] is False
    primer_paso = cuerpo["pasos"][0]
    assert primer_paso["paso"] == "entorno" and primer_paso["ok"] is False
    assert "SF_ACCOUNT" in primer_paso["error"]
    assert "Railway" in cuerpo["siguiente_paso"]


def test_abierto_con_autenticacion_basica(monkeypatch) -> None:
    _, cliente = _app_en_produccion(monkeypatch, APP_BASIC_USER="pro", APP_BASIC_PASSWORD="clave-larga")
    assert cliente.get("/api/diagnostico").status_code == 401          # el middleware exige credenciales
    respuesta = cliente.get("/api/diagnostico", auth=("pro", "clave-larga"))
    assert respuesta.status_code == 200
    assert respuesta.json()["modo"] == "snowflake"


@pytest.mark.skipif(not CONECTOR_INSTALADO, reason="Requiere snowflake-snowpark-python instalado.")
def test_llave_ilegible_se_reporta_en_su_propio_paso(monkeypatch) -> None:
    _, cliente = _app_en_produccion(
        monkeypatch,
        APP_DIAG_TOKEN="t",
        SF_ACCOUNT="cuenta", SF_USER="usuario", SF_DATABASE="base",
        SF_SCHEMA="esquema", SF_WAREHOUSE="wh", SF_ROLE="rol",
        SF_PRIVATE_KEY_B64_1="esto-no-es-una-llave",
    )
    cuerpo = cliente.get("/api/diagnostico?token=t").json()
    pasos = {paso["paso"]: paso for paso in cuerpo["pasos"]}
    assert pasos["entorno"]["ok"] is True          # las variables sí están
    assert pasos["llave_1"]["ok"] is False         # pero la llave no sirve
    assert "Base64" in pasos["llave_1"]["error"]
    assert "ReadAllBytes" in cuerpo["siguiente_paso"]


def test_health_reporta_variables_faltantes_sin_exponer_valores(monkeypatch) -> None:
    _, cliente = _app_en_produccion(monkeypatch, SF_ACCOUNT="cuenta", SF_USER="usuario")
    cuerpo = cliente.get("/api/health").json()
    assert cuerpo["data_connection"] == "missing_configuration"
    assert cuerpo["snowflake"]["missing_variables"] == ["SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE"]
    assert "cuenta" not in str(cuerpo)             # nunca se devuelven valores


@pytest.mark.skipif(not CONECTOR_INSTALADO, reason="requiere snowflake-snowpark-python")
def test_health_no_afirma_conexion_sin_haberla_probado(monkeypatch) -> None:
    """Con toda la configuración presente, el estado es «configured», no «connected».

    Es la diferencia que ve el usuario entre «Sin verificar» y «Datos reales»:
    el aplicativo no dice que está conectado hasta que Snowflake responde.
    """
    _, cliente = _app_en_produccion(
        monkeypatch,
        SF_ACCOUNT="cuenta", SF_USER="usuario", SF_DATABASE="base",
        SF_SCHEMA="esquema", SF_WAREHOUSE="wh", SF_ROLE="rol",
        SF_PRIVATE_KEY_B64_1="bWF0ZXJpYWw=",
    )
    cuerpo = cliente.get("/api/health").json()
    assert cuerpo["data_connection"] == "configured"
    assert cuerpo["snowflake"]["verified"] is False
    assert cuerpo["snowflake"]["verified_at"] is None


@pytest.mark.skipif(not CONECTOR_INSTALADO, reason="requiere snowflake-snowpark-python")
def test_health_reporta_error_despues_de_un_fallo_de_conexion(monkeypatch) -> None:
    """Tras un intento fallido el estado pasa a «error» sin filtrar secretos."""
    modulo, cliente = _app_en_produccion(
        monkeypatch,
        SF_ACCOUNT="cuenta", SF_USER="usuario", SF_DATABASE="base",
        SF_SCHEMA="esquema", SF_WAREHOUSE="wh", SF_ROLE="rol",
        SF_PRIVATE_KEY_B64_1="bWF0ZXJpYWw=",
    )
    assert cliente.get("/api/health").json()["data_connection"] == "configured"

    # Se simula el fallo que registraría un intento real contra Snowflake.
    modulo.snowflake.ultimo_error = "290404 (08001): 404 Not Found"
    cuerpo = cliente.get("/api/health").json()
    assert cuerpo["data_connection"] == "error"
    assert cuerpo["snowflake"]["connection_error"] is True
    assert "404" not in str(cuerpo)                # el detalle vive en /api/diagnostico
