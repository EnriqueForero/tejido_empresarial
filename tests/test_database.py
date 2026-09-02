"""Normalización de la llave privada y reporte de configuración.

La causa más común de «no conecta» es el valor pegado en la variable de
entorno: Base64 con saltos de línea, el PEM pegado tal cual, o la frase de la
llave equivocada. Estas pruebas fijan ese comportamiento.
"""
import base64

import pytest

# «cryptography» llega con el conector de Snowflake. Si el entorno no la trae
# (por ejemplo un Colab recién instalado), estas pruebas se omiten en lugar de
# romper la ejecución completa.
serialization = pytest.importorskip(
    "cryptography.hazmat.primitives.serialization",
    reason="Se requiere cryptography para probar la normalización de llaves.",
)
rsa = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.rsa")

from backend.database import ErrorLlave, SnowflakeService, normalizar_llave, redactar


@pytest.fixture(scope="module")
def llave():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def der_plano(llave):
    return llave.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


@pytest.fixture(scope="module")
def der_cifrado(llave):
    return llave.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(b"clave-de-prueba"),
    )


@pytest.fixture(scope="module")
def pem_plano(llave):
    return llave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def test_base64_de_der_con_espacios_y_saltos(der_plano):
    """Railway suele agregar un salto de línea al pegar: no debe romper nada."""
    b64 = base64.b64encode(der_plano).decode()
    for variante in (b64, b64 + "\n", f"  {b64}  ", b64[:40] + "\n" + b64[40:]):
        normalizada, formato = normalizar_llave(variante, None)
        assert normalizada == der_plano
        assert "DER" in formato


def test_der_cifrado_se_descifra_con_la_frase(der_cifrado, der_plano):
    normalizada, formato = normalizar_llave(base64.b64encode(der_cifrado).decode(), "clave-de-prueba")
    assert normalizada == der_plano       # queda listo para el conector, sin cifrar
    assert "cifrado" in formato


def test_der_cifrado_sin_frase_avisa_con_claridad(der_cifrado):
    with pytest.raises(ErrorLlave) as error:
        normalizar_llave(base64.b64encode(der_cifrado).decode(), None)
    assert "PASSPHRASE" in str(error.value)


def test_frase_equivocada_avisa_con_claridad(der_cifrado):
    with pytest.raises(ErrorLlave) as error:
        normalizar_llave(base64.b64encode(der_cifrado).decode(), "otra-frase")
    assert "frase" in str(error.value).casefold()


def test_pem_pegado_directamente(pem_plano, der_plano):
    normalizada, formato = normalizar_llave(pem_plano.decode(), None)
    assert normalizada == der_plano
    assert "PEM" in formato


def test_base64_de_un_pem(pem_plano, der_plano):
    normalizada, formato = normalizar_llave(base64.b64encode(pem_plano).decode(), None)
    assert normalizada == der_plano
    assert "PEM" in formato


def test_valor_que_no_es_base64_explica_como_generarlo():
    with pytest.raises(ErrorLlave) as error:
        normalizar_llave("esto no es una llave", None)
    assert "Base64" in str(error.value)


def test_redactar_oculta_secretos_y_llaves(monkeypatch, pem_plano):
    monkeypatch.setenv("SF_PRIVATE_KEY_PASSPHRASE_1", "frase-secreta-larga")
    assert "frase-secreta-larga" not in redactar("falló con frase-secreta-larga dentro")
    assert "BEGIN PRIVATE KEY" not in redactar(pem_plano.decode())


def test_reporte_de_configuracion_lista_lo_que_falta(monkeypatch):
    for nombre in ("SF_ACCOUNT", "SF_USER", "SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE",
                   "SF_PRIVATE_KEY_B64_1", "SF_PRIVATE_KEY_PATH_1",
                   "SF_PRIVATE_KEY_B64_2", "SF_PRIVATE_KEY_PATH_2"):
        monkeypatch.delenv(nombre, raising=False)
    servicio = SnowflakeService()
    reporte = servicio.configuration_report()
    assert reporte["configured"] is False
    assert reporte["missing_variables"] == ["SF_ACCOUNT", "SF_USER", "SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE"]
    assert reporte["key_sources"] == []

    monkeypatch.setenv("SF_ACCOUNT", "cuenta")
    monkeypatch.setenv("SF_USER", "usuario")
    monkeypatch.setenv("SF_DATABASE", "base")
    monkeypatch.setenv("SF_SCHEMA", "esquema")
    monkeypatch.setenv("SF_WAREHOUSE", "wh")
    monkeypatch.setenv("SF_ROLE", "rol")
    monkeypatch.setenv("SF_PRIVATE_KEY_B64_1", "AAAA")
    reporte = servicio.configuration_report()
    assert reporte["missing_variables"] == []
    assert reporte["key_sources"] == ["SF_PRIVATE_KEY_B64_1"]
    assert reporte["configured"] is servicio.connector_installed


def test_sin_variables_la_sesion_dice_cuales_faltan(monkeypatch):
    for nombre in ("SF_ACCOUNT", "SF_USER", "SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE"):
        monkeypatch.delenv(nombre, raising=False)
    servicio = SnowflakeService()
    with pytest.raises(RuntimeError) as error:
        servicio.session()
    assert "SF_ACCOUNT" in str(error.value)
