"""
Conexión a Snowflake (misma lógica del aplicativo Streamlit original).

Autenticación con llave RSA, rotación entre dos llaves y reintentos. Además:

- La llave se **normaliza** antes de usarla: se aceptan Base64 de DER (con o sin
  espacios y saltos de línea), PEM pegado directamente y archivos .der/.p8. Si
  la llave está cifrada, se descifra aquí con la frase configurada. Esto elimina
  la causa más frecuente de «no conecta» tras pegar variables en Railway.
- `diagnostico()` recorre paso a paso entorno → conector → llave → sesión →
  consulta → tablas, y devuelve el error real de cada paso (sin secretos), para
  que el endpoint /api/diagnostico diga exactamente dónde se rompe.
"""
from __future__ import annotations

import base64
import binascii
import os
import re
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

# El conector sólo sabe devolver DataFrames si tiene el extra «pandas» (pyarrow).
# Sin él, `to_pandas()` falla aunque la conexión y los permisos estén bien; por eso
# se detecta aquí y las consultas usan la vía alterna (`collect()`).
try:
    from snowflake.connector.options import installed_pandas as PANDAS_ARROW
except Exception:  # pragma: no cover - el conector puede no estar instalado
    PANDAS_ARROW = False

try:  # El conector sólo se necesita con datos reales.
    from snowflake.snowpark import Session
except ImportError:  # pragma: no cover - el modo demostración no lo requiere
    Session = None  # type: ignore[assignment]

try:
    from cryptography.hazmat.primitives import serialization
except ImportError:  # pragma: no cover - viene con el conector
    serialization = None  # type: ignore[assignment]


VARIABLES_REQUERIDAS = ["SF_ACCOUNT", "SF_USER", "SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE"]
VARIABLES_LLAVE = [
    "SF_PRIVATE_KEY_B64_1",
    "SF_PRIVATE_KEY_PATH_1",
    "SF_PRIVATE_KEY_B64_2",
    "SF_PRIVATE_KEY_PATH_2",
]


def _entero(nombre: str, por_defecto: int) -> int:
    try:
        return max(5, int(os.getenv(nombre, str(por_defecto))))
    except (TypeError, ValueError):
        return por_defecto


def _valores_sensibles() -> list[str]:
    """Valores que nunca deben aparecer en un mensaje de error."""
    nombres = [
        "SF_PRIVATE_KEY_B64_1", "SF_PRIVATE_KEY_B64_2",
        "SF_PRIVATE_KEY_PASSPHRASE_1", "SF_PRIVATE_KEY_PASSPHRASE_2",
        "APP_BASIC_PASSWORD", "APP_DIAG_TOKEN",
    ]
    return [valor for valor in (os.getenv(nombre) for nombre in nombres) if valor and len(valor) > 3]


def redactar(texto: str, limite: int = 500) -> str:
    """Quita secretos y recorta un mensaje para poder mostrarlo con seguridad."""
    mensaje = str(texto)
    for secreto in _valores_sensibles():
        mensaje = mensaje.replace(secreto, "***")
    # Cualquier bloque largo que parezca material criptográfico.
    mensaje = re.sub(r"-----BEGIN[\s\S]+?-----END[^-]*-----", "«llave omitida»", mensaje)
    mensaje = mensaje.strip().replace("\n", " · ")
    return mensaje[:limite] + ("…" if len(mensaje) > limite else "")


class ErrorLlave(ValueError):
    """La llave privada no pudo interpretarse."""


def normalizar_llave(material: bytes | str, passphrase: str | None) -> tuple[bytes, str]:
    """Devuelve (DER PKCS8 sin cifrar, descripción del formato detectado).

    Acepta: Base64 de un DER (con espacios o saltos de línea), bytes DER, texto
    PEM pegado tal cual, y Base64 de un PEM. Si la llave está cifrada, la
    descifra con `passphrase`. Si `cryptography` no está disponible, devuelve el
    material tal cual para que el conector lo intente.
    """
    texto = material.decode("utf-8", "ignore") if isinstance(material, bytes) else material
    crudo: bytes
    formato: str

    if "-----BEGIN" in texto:
        crudo, formato = texto.encode("utf-8"), "PEM"
    elif isinstance(material, bytes) and not re.fullmatch(r"[A-Za-z0-9+/=\s]*", texto or ""):
        crudo, formato = material, "DER (archivo)"
    else:
        limpio = re.sub(r"\s+", "", texto)
        try:
            crudo = base64.b64decode(limpio, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ErrorLlave(
                "El valor no es Base64 válido. Genérelo con "
                "[Convert]::ToBase64String([IO.File]::ReadAllBytes(\"rsa_key_1.der\")) en PowerShell "
                "o base64 -w 0 rsa_key_1.der en Linux, y péguelo en UNA sola línea."
            ) from exc
        if crudo[:11] == b"-----BEGIN ":
            formato = "Base64 de un PEM"
        else:
            formato = "Base64 de un DER"

    if serialization is None:  # sin cryptography: que lo resuelva el conector
        return crudo, f"{formato} (sin normalizar)"

    clave_bytes = passphrase.encode("utf-8") if passphrase else None
    cargadores = (
        (serialization.load_pem_private_key, "PEM")
        if crudo[:11] == b"-----BEGIN "
        else (serialization.load_der_private_key, "DER")
    )
    cargador, tipo = cargadores
    try:
        llave = cargador(crudo, password=clave_bytes)
        cifrada = bool(clave_bytes)
    except TypeError:
        # La llave estaba cifrada y no se entregó frase (o al revés).
        try:
            llave = cargador(crudo, password=None)
            cifrada = False
        except Exception as exc:
            raise ErrorLlave(
                f"La llave ({tipo}) parece cifrada y no se pudo abrir. Configure "
                "SF_PRIVATE_KEY_PASSPHRASE_N con la frase correcta."
            ) from exc
    except ValueError as exc:
        detalle = redactar(exc, 160)
        raise ErrorLlave(
            f"No se pudo interpretar la llave ({tipo}): {detalle}. "
            "Verifique que el Base64 corresponda al archivo .der del usuario de servicio "
            "y que la frase (SF_PRIVATE_KEY_PASSPHRASE_N) sea la vigente."
        ) from exc

    der = llave.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return der, f"{formato}{' cifrado' if cifrada else ''} → DER PKCS8"


class SnowflakeService:
    def __init__(self) -> None:
        load_dotenv()
        self._session: "Session | None" = None
        self._lock = threading.Lock()
        self._last_working_key = 1
        self.ultimo_error: str | None = None      # causa real del último fallo de conexión
        # Marca de tiempo del último apretón de manos correcto con Snowflake. Sin
        # ella la interfaz no puede afirmar «está conectado»: sólo «está configurado».
        self.ultima_conexion_ok: float | None = None
        # Causa real del último fallo de una consulta (no de la conexión). Sirve
        # para que el mensaje al usuario diga qué pasó en vez de «no se pudo».
        self.ultimo_error_consulta: str | None = None

    # ── Estado de la configuración ──────────────────────────────────────
    @property
    def connector_installed(self) -> bool:
        return Session is not None

    @property
    def missing_variables(self) -> list[str]:
        return [nombre for nombre in VARIABLES_REQUERIDAS if not os.getenv(nombre)]

    @property
    def key_sources(self) -> list[str]:
        return [nombre for nombre in VARIABLES_LLAVE if os.getenv(nombre)]

    @property
    def configured(self) -> bool:
        return self.connector_installed and not self.missing_variables and bool(self.key_sources)

    def configuration_report(self) -> dict[str, Any]:
        """Resumen sin secretos: sirve para /api/health y para el diagnóstico."""
        version = None
        if Session is not None:
            try:
                from snowflake.snowpark.version import VERSION as SNOWPARK_VERSION

                version = ".".join(str(parte) for parte in SNOWPARK_VERSION)
            except Exception:
                version = "desconocida"
        return {
            "connector_installed": self.connector_installed,
            "connector_version": version,
            "pandas_arrow": bool(PANDAS_ARROW),
            "missing_variables": self.missing_variables,
            "key_sources": self.key_sources,
            "configured": self.configured,
            "last_error": self.ultimo_error,
            "verified": self.ultima_conexion_ok is not None,
            "verified_at": (
                datetime.fromtimestamp(self.ultima_conexion_ok, tz=timezone.utc).isoformat(timespec="seconds")
                if self.ultima_conexion_ok is not None
                else None
            ),
        }

    # ── Llave privada ───────────────────────────────────────────────────
    def _material_llave(self, key_number: int) -> tuple[bytes | str, str] | None:
        """Material crudo de la llave y de dónde salió."""
        encoded = os.getenv(f"SF_PRIVATE_KEY_B64_{key_number}")
        if encoded:
            return encoded, f"SF_PRIVATE_KEY_B64_{key_number}"
        raw_path = os.getenv(f"SF_PRIVATE_KEY_PATH_{key_number}")
        if raw_path:
            path = Path(raw_path).expanduser().resolve()
            if not path.is_file():
                raise ErrorLlave(f"No se encontró el archivo de SF_PRIVATE_KEY_PATH_{key_number}: {path}")
            return path.read_bytes(), f"SF_PRIVATE_KEY_PATH_{key_number}"
        return None

    def _private_key(self, key_number: int) -> tuple[bytes, str] | None:
        """Llave lista para el conector (DER PKCS8 sin cifrar) y su descripción."""
        material = self._material_llave(key_number)
        if material is None:
            return None
        crudo, origen = material
        passphrase = os.getenv(f"SF_PRIVATE_KEY_PASSPHRASE_{key_number}")
        der, formato = normalizar_llave(crudo, passphrase)
        return der, f"{origen} · {formato} · {len(der)} bytes"

    def _session_config(self, key_number: int) -> dict[str, Any]:
        llave = self._private_key(key_number)
        if llave is None:
            raise ErrorLlave(f"No se configuró la llave privada {key_number}.")
        faltantes = self.missing_variables
        if faltantes:
            raise ValueError("Faltan variables de Snowflake: " + ", ".join(faltantes))
        return {
            "account": os.getenv("SF_ACCOUNT"),
            "user": os.getenv("SF_USER"),
            "private_key": llave[0],
            "database": os.getenv("SF_DATABASE"),
            "schema": os.getenv("SF_SCHEMA"),
            "warehouse": os.getenv("SF_WAREHOUSE"),
            "role": os.getenv("SF_ROLE"),
            "query_tag": "TEJIDO_EMPRESARIAL_REACT",
            # Acota el intento de conexión: sin esto un fallo puede tardar minutos.
            "login_timeout": _entero("SF_LOGIN_TIMEOUT", 30),
            "network_timeout": _entero("SF_NETWORK_TIMEOUT", 60),
        }

    # ── Sesión ──────────────────────────────────────────────────────────
    def session(self, intentos: int = 3) -> "Session":
        # Se reportan TODOS los problemas de configuración de una vez: así el
        # mensaje es accionable sin tener que corregir de a uno.
        problemas: list[str] = []
        if Session is None:
            problemas.append(
                "el conector snowflake-snowpark-python no está instalado "
                "(la imagen debe construirse con requirements-api.txt)"
            )
        if self.missing_variables:
            problemas.append("faltan variables: " + ", ".join(self.missing_variables))
        if not self.key_sources:
            problemas.append("no hay llave privada (SF_PRIVATE_KEY_B64_1 o SF_PRIVATE_KEY_PATH_1)")
        if problemas:
            raise RuntimeError("No se puede conectar con Snowflake: " + "; ".join(problemas) + ".")
        if self._session is not None:
            return self._session
        with self._lock:
            if self._session is not None:
                return self._session
            primary = self._last_working_key
            fallback = 2 if primary == 1 else 1
            last_error: Exception | None = None
            for key_number in (primary, fallback):
                if not (os.getenv(f"SF_PRIVATE_KEY_B64_{key_number}") or os.getenv(f"SF_PRIVATE_KEY_PATH_{key_number}")):
                    continue
                for attempt in range(max(1, intentos)):
                    try:
                        self._session = Session.builder.configs(self._session_config(key_number)).create()
                        self._last_working_key = key_number
                        self.ultimo_error = None
                        self.ultima_conexion_ok = time.time()
                        return self._session
                    except Exception as exc:  # Snowflake expone excepciones heterogéneas
                        last_error = exc
                        # Sin sentido reintentar: la llave o las credenciales no sirven.
                        if isinstance(exc, ErrorLlave) or "JWT token is invalid" in str(exc):
                            break
                        if attempt < intentos - 1:
                            time.sleep(2 ** attempt)
            self.ultimo_error = redactar(last_error or "causa desconocida")
            raise RuntimeError(
                f"No fue posible establecer la conexión con Snowflake: {self.ultimo_error}"
            ) from last_error

    def verificar(self) -> None:
        """Un solo intento contra Snowflake, para responder rápido en /api/health.

        Las consultas normales reintentan; aquí no tiene sentido: quien abre la
        página de estado espera una respuesta, no tres esperas encadenadas.
        """
        self.session(intentos=1).sql("SELECT 1 AS TOTAL").collect()

    def _a_pandas(self, consulta) -> pd.DataFrame:
        """Resultado de Snowpark como DataFrame, con o sin pyarrow.

        Con el extra «pandas» instalado se usa `to_pandas()`, que es la vía
        rápida. Sin él se arma el marco con las filas, como hacía el aplicativo
        Streamlit: más lento, pero el aplicativo sigue funcionando.
        """
        if PANDAS_ARROW:
            return consulta.to_pandas()
        filas = consulta.collect()
        if not filas:
            return pd.DataFrame(columns=[campo.name.strip('"') for campo in consulta.schema.fields])
        marco = pd.DataFrame([fila.as_dict() for fila in filas])
        # `collect()` devuelve Decimal donde Arrow devolvería números; se convierten
        # para que el Excel y la vista previa apliquen los formatos numéricos.
        for columna in marco.columns:
            if marco[columna].dtype == object and marco[columna].map(lambda valor: isinstance(valor, Decimal)).any():
                marco[columna] = pd.to_numeric(marco[columna], errors="coerce")
        return marco

    def _ejecutar(self, query: str, accion):
        """Ejecuta la consulta y, si falla, reintenta una vez con sesión nueva."""
        try:
            resultado = accion(self.session().sql(query))
        except Exception as primero:
            self._reset_session()
            try:
                resultado = accion(self.session().sql(query))
            except Exception as segundo:
                self.ultimo_error_consulta = redactar(segundo or primero)
                raise
        self.ultimo_error_consulta = None
        return resultado

    def dataframe(self, query: str) -> pd.DataFrame:
        return self._ejecutar(query, self._a_pandas)

    def scalar(self, query: str, key: str = "TOTAL") -> int:
        rows = self._ejecutar(query, lambda consulta: consulta.collect())
        if not rows:
            return 0
        row = rows[0]
        try:
            return int(row[key])
        except Exception:
            return int(row[0])

    def _reset_session(self) -> None:
        with self._lock:
            session = self._session
            self._session = None
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass

    def log_event(self, event_type: str, page: str, detail: str, filters: str) -> None:
        try:
            from backend.config import EVENT_TABLE

            safe = lambda value: str(value).replace("'", "''")
            query = (
                f"INSERT INTO {EVENT_TABLE} (TIPO_EVENTO, PAGINA, DETALLE_EVENTO, FILTROS, FECHA_HORA) "
                f"VALUES ('{safe(event_type)}', '{safe(page)}', '{safe(detail)}', '{safe(filters)}', "
                "CONVERT_TIMEZONE('America/Los_Angeles', 'America/Bogota', CURRENT_TIMESTAMP))"
            )
            self.session().sql(query).collect()
        except Exception:
            # La analítica nunca debe impedir que el usuario consulte o descargue.
            return

    # ── Diagnóstico paso a paso ─────────────────────────────────────────
    def diagnostico(self) -> list[dict[str, Any]]:
        """Recorre la cadena completa y reporta dónde se rompe (sin secretos)."""
        from backend.config import (
            COMPANY_TABLE,
            EVENT_TABLE,
            EXPORT_FILTER_TABLE,
            EXPORT_TABLE,
            GENERAL_FILTER_TABLE,
        )

        pasos: list[dict[str, Any]] = []

        def paso(nombre: str, descripcion: str, funcion) -> bool:
            inicio = time.perf_counter()
            try:
                detalle = funcion()
                pasos.append({
                    "paso": nombre, "descripcion": descripcion, "ok": True,
                    "detalle": detalle, "segundos": round(time.perf_counter() - inicio, 2),
                })
                return True
            except Exception as exc:
                pasos.append({
                    "paso": nombre, "descripcion": descripcion, "ok": False,
                    "detalle": None, "error": redactar(exc),
                    "tipo_error": type(exc).__name__,
                    "segundos": round(time.perf_counter() - inicio, 2),
                })
                return False

        # 1. Variables de entorno (sólo nombres y longitudes, nunca valores).
        def _entorno():
            presentes = {nombre: len(os.getenv(nombre) or "") for nombre in VARIABLES_REQUERIDAS}
            faltantes = self.missing_variables
            if faltantes:
                raise ValueError("Faltan variables obligatorias: " + ", ".join(faltantes))
            if not self.key_sources:
                raise ValueError("No hay llave configurada (SF_PRIVATE_KEY_B64_1 o SF_PRIVATE_KEY_PATH_1).")
            return {
                "longitudes": presentes,
                "llaves_configuradas": self.key_sources,
                "frases_configuradas": [
                    n for n in ("SF_PRIVATE_KEY_PASSPHRASE_1", "SF_PRIVATE_KEY_PASSPHRASE_2") if os.getenv(n)
                ],
            }

        if not paso("entorno", "Variables de Snowflake presentes", _entorno):
            return pasos

        # 2. Conector instalado y capaz de devolver tablas.
        def _conector():
            if Session is None:
                raise RuntimeError("snowflake-snowpark-python no está instalado en la imagen.")
            reporte = self.configuration_report()
            return {
                "snowpark": reporte["connector_version"],
                "cryptography": serialization is not None,
                "pyarrow_para_tablas": bool(PANDAS_ARROW),
                "modo_de_lectura": "Arrow (rápido)" if PANDAS_ARROW else "filas (sin pyarrow)",
            }

        if not paso("conector", "Conector snowflake-snowpark-python disponible", _conector):
            return pasos

        # 3. Llaves privadas (cada una por separado).
        alguna_llave = False
        for numero in (1, 2):
            if not (os.getenv(f"SF_PRIVATE_KEY_B64_{numero}") or os.getenv(f"SF_PRIVATE_KEY_PATH_{numero}")):
                continue
            alguna_llave = paso(
                f"llave_{numero}", f"Llave privada {numero} interpretable",
                lambda n=numero: (self._private_key(n) or (b"", ""))[1],
            ) or alguna_llave
        if not alguna_llave:
            return pasos

        # 4. Sesión con Snowflake.
        def _sesion():
            self._reset_session()
            sesion = self.session(intentos=1)
            return {
                "llave_usada": self._last_working_key,
                "cuenta": sesion.get_current_account(),
                "usuario": sesion.get_current_user(),
                "rol": sesion.get_current_role(),
                "warehouse": sesion.get_current_warehouse(),
                "base_de_datos": sesion.get_current_database(),
                "esquema": sesion.get_current_schema(),
            }

        if not paso("sesion", "Sesión establecida con Snowflake", _sesion):
            return pasos

        paso("consulta_simple", "SELECT 1 ejecutado", lambda: self.scalar("SELECT 1 AS TOTAL"))

        # 5. Acceso a cada tabla que usa el aplicativo.
        tablas = [
            ("tabla_filtros_generales", "Filtros generales (panel de segmentación)", GENERAL_FILTER_TABLE),
            ("tabla_filtros_exportadoras", "Filtros de exportaciones", EXPORT_FILTER_TABLE),
            ("tabla_empresas", "Tabla de empresas (consultas y descargas)", COMPANY_TABLE),
            ("tabla_bienes", "Tabla de bienes y servicios (filtros de exportación)", EXPORT_TABLE),
            ("tabla_eventos", "Tabla de auditoría de eventos", EVENT_TABLE),
        ]
        for nombre, descripcion, tabla in tablas:
            paso(
                nombre, f"{descripcion} · {tabla}",
                lambda t=tabla: {"filas_de_prueba": len(self.session().sql(f"SELECT * FROM {t} LIMIT 1").collect())},
            )

        # 6. La consulta real de la vista previa, sin filtros.
        def _vista_previa():
            from backend.models import SearchRequest
            from backend.queries import build_preview_query

            consulta = build_preview_query(SearchRequest(mode="filters", page=1, page_size=10))
            marco = self.dataframe(consulta)
            return {"filas": int(len(marco)), "columnas": int(len(marco.columns))}

        paso("consulta_vista_previa", "Consulta real de la vista previa (sin filtros)", _vista_previa)
        return pasos


snowflake = SnowflakeService()
