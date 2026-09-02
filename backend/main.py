"""
API del aplicativo Tejido Empresarial (FastAPI).

Un único proceso sirve la API (/api/*) y el frontend React compilado (frontend/dist).
La conexión a Snowflake, las consultas y la auditoría conservan la lógica del
aplicativo Streamlit original; el navegador nunca recibe credenciales ni SQL.
"""
from __future__ import annotations

import base64
import logging
import os
import secrets
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi import Request as FastAPIRequest
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend import demo
from backend.config import (
    APP_TITLE,
    APP_VERSION,
    COLUMN_SECTIONS,
    CONTACT_COLUMNS,
    DATA_SOURCES,
    EXPORT_FILTER_TABLE,
    EXPORT_FILTERS,
    FILTER_GROUP_ORDER,
    GENERAL_FILTER_TABLE,
    GENERAL_FILTERS,
    METHOD_NOTES,
    PERIODS,
    PREVIEW_COLUMNS,
    QUERY_COLUMNS,
)
from backend.database import snowflake
from backend.exporter import create_export, filename_for
from backend.glossary import GLOSSARY_PATH, METHODOLOGY_PATH, load_glossary
from backend.models import FilterOptionsRequest, SearchRequest, clean_nit
from backend.queries import build_company_query, build_count_query, build_export_query, build_preview_query

# Los mensajes van a stdout para que aparezcan en los registros de Railway.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s · %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("tejido")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _integer_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).replace("_", ""))
    except (TypeError, ValueError):
        value = default
    return min(max(value, minimum), maximum)


DEMO_MODE = _flag("APP_DEMO_MODE")
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
EXPORT_MAX_ROWS = _integer_env("EXPORT_MAX_ROWS", 5000, 1, 20000)
PREVIEW_MAX_ROWS = 10_000
MAX_REQUEST_BYTES = _integer_env("MAX_REQUEST_BYTES", 2_000_000, 50_000, 10_000_000)
PUBLIC_ORIGIN = os.getenv("PUBLIC_ORIGIN", "").rstrip("/")
ACCESS_USER = os.getenv("APP_BASIC_USER", "")
ACCESS_PASSWORD = os.getenv("APP_BASIC_PASSWORD", "")
ACCESS_CONTROL_ACTIVE = bool(ACCESS_USER and ACCESS_PASSWORD)
ACCESS_CONTROL_PARTIAL = bool(ACCESS_USER) != bool(ACCESS_PASSWORD)
# Igual que el aplicativo Streamlit original, el acceso es abierto salvo que se configure
# APP_BASIC_USER y APP_BASIC_PASSWORD. Los campos de contacto se incluyen en la descarga
# como en el original; pueden retirarse con EXPORT_INCLUDE_CONTACT_FIELDS=false.
EXPORT_INCLUDE_CONTACT_FIELDS = _flag("EXPORT_INCLUDE_CONTACT_FIELDS", "true")
DIAG_TOKEN = os.getenv("APP_DIAG_TOKEN", "").strip()

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    docs_url="/api/docs" if APP_ENV != "production" else None,
    redoc_url=None,
)

if ACCESS_CONTROL_PARTIAL:
    logger.warning("APP_BASIC_USER y APP_BASIC_PASSWORD deben configurarse juntos; el servicio responderá 503.")
elif not ACCESS_CONTROL_ACTIVE and not DEMO_MODE:
    logger.warning("El aplicativo se sirve sin autenticación HTTP (igual que la versión Streamlit). Configure APP_BASIC_USER y APP_BASIC_PASSWORD para protegerlo.")


# ---------------------------------------------------------------------------
# Middleware: límites, autenticación opcional y cabeceras de seguridad
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_layer(request: FastAPIRequest, call_next):
    content_length = request.headers.get("content-length")
    is_health = request.url.path == "/api/health"
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
        response = JSONResponse({"detail": "La solicitud supera el tamaño permitido."}, status_code=413)
    elif ACCESS_CONTROL_PARTIAL and not is_health:
        response = JSONResponse({"detail": "El control de acceso está configurado de forma incompleta."}, status_code=503)
    elif ACCESS_CONTROL_ACTIVE and not is_health and not _valid_basic_credentials(request):
        response = JSONResponse(
            {"detail": "Autenticación requerida."},
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Tejido Empresarial", charset="UTF-8"'},
        )
    else:
        response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; "
        "form-action 'self'; img-src 'self' data: blob:; font-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'"
    )
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


def _valid_basic_credentials(request: FastAPIRequest) -> bool:
    authorization = request.headers.get("authorization", "")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.casefold() != "basic":
            return False
        decoded = base64.b64decode(token, validate=True).decode("utf-8")
        username, separator, password = decoded.partition(":")
        return (
            bool(separator)
            and secrets.compare_digest(username.encode("utf-8"), ACCESS_USER.encode("utf-8"))
            and secrets.compare_digest(password.encode("utf-8"), ACCESS_PASSWORD.encode("utf-8"))
        )
    except (TypeError, ValueError, UnicodeDecodeError):
        return False


# ---------------------------------------------------------------------------
# Utilidades de datos
# ---------------------------------------------------------------------------
def _identifier_columns(columns: Iterable[str]) -> list[str]:
    return [column for column in columns if column == "NIT" or column.startswith(("Código ", "Dígito ", "ID "))]


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.astype(object).where(pd.notnull(frame), None)
    for column in _identifier_columns(clean.columns):
        clean[column] = clean[column].map(
            lambda value: None
            if value is None
            else str(int(value))
            if isinstance(value, float) and float(value).is_integer()
            else str(value)
        )
    records = clean.to_dict(orient="records")
    for record in records:
        for key, value in record.items():
            if hasattr(value, "item"):
                try:
                    record[key] = value.item()
                except (TypeError, ValueError):
                    record[key] = str(value)
    return records


def _drop_contact_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if EXPORT_INCLUDE_CONTACT_FIELDS:
        return frame
    return frame.drop(columns=[column for column in CONTACT_COLUMNS if column in frame.columns])


@lru_cache(maxsize=2)
def _cached_filter_frame(kind: str) -> pd.DataFrame:
    table = GENERAL_FILTER_TABLE if kind == "general" else EXPORT_FILTER_TABLE
    frame = snowflake.dataframe(f"SELECT * FROM {table}")
    return frame.astype(str).replace({"None": None, "nan": None})


def _options_for(definitions: list[dict[str, str]], frame: pd.DataFrame, selections: dict[str, list[str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for definition in definitions:
        key = definition["key"]
        if key not in frame.columns:
            output.append({**definition, "options": [], "truncated": False})
            continue
        filtered = frame
        for other_key, values in selections.items():
            if other_key == key or other_key not in frame.columns or not values:
                continue
            filtered = filtered[filtered[other_key].isin(values)]
        values = sorted({str(value).strip() for value in filtered[key].dropna().tolist() if str(value).strip()}, key=str.casefold)
        output.append({**definition, "options": values[:3000], "truncated": len(values) > 3000})
    return output


def _log_event(kind: str, detail: str, payload: str) -> None:
    if DEMO_MODE:
        return
    snowflake.log_event(kind, "Tejido Empresarial", detail, payload)


def _error_consulta(mensaje: str) -> str:
    """Mensaje para el usuario; en datos reales apunta al diagnóstico y a los registros."""
    if DEMO_MODE:
        return f"{mensaje} Intenta nuevamente en unos segundos."
    ultimo = snowflake.ultimo_error
    if ultimo:
        return f"{mensaje} Snowflake reportó: {ultimo}. Revise /api/diagnostico."
    return (
        f"{mensaje} Si vuelve a ocurrir, abra /api/diagnostico para ver en qué paso falla "
        "la conexión con Snowflake, o revise los registros del servicio."
    )


def _require_connection() -> None:
    if not DEMO_MODE and not snowflake.configured:
        raise HTTPException(status_code=503, detail="La conexión de datos aún no está configurada en este entorno.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health(request: FastAPIRequest, deep: bool = False) -> dict[str, Any]:
    if ACCESS_CONTROL_PARTIAL:
        raise HTTPException(status_code=503, detail="Configure APP_BASIC_USER y APP_BASIC_PASSWORD juntos.")
    if deep and ACCESS_CONTROL_ACTIVE and not _valid_basic_credentials(request):
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida para el health profundo.",
            headers={"WWW-Authenticate": 'Basic realm="Tejido Empresarial", charset="UTF-8"'},
        )
    reporte = snowflake.configuration_report()
    if DEMO_MODE:
        connection = "demo"
    elif not snowflake.configured:
        connection = "missing_configuration"
    elif reporte["last_error"]:
        connection = "error"
    elif reporte["verified"]:
        # Ya hubo un apretón de manos correcto en este proceso.
        connection = "connected"
    else:
        # Configuración completa, pero todavía sin ninguna consulta: no se puede
        # afirmar que esté conectado. La página /estado resuelve esto con ?deep=true.
        connection = "configured"
    if deep and not DEMO_MODE and snowflake.configured:
        try:
            snowflake.verificar()
            connection = "connected"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Health profundo: Snowflake no respondió")
            raise HTTPException(
                status_code=503,
                detail=(
                    "Snowflake está configurado, pero no respondió. "
                    "Consulte /api/diagnostico para ver en qué paso falla."
                ),
            ) from exc
        reporte = snowflake.configuration_report()
    return {
        "status": "ok",
        "version": APP_VERSION,
        "data_connection": connection,
        "access_control": "basic" if ACCESS_CONTROL_ACTIVE else "open",
        "frontend_built": (FRONTEND_DIST / "index.html").is_file(),
        "demo_mode": DEMO_MODE,
        "snowflake": {
            "connector_installed": reporte["connector_installed"],
            "connector_version": reporte["connector_version"],
            "missing_variables": reporte["missing_variables"],
            "key_sources": reporte["key_sources"],
            # Sólo si hubo un fallo de conexión; el detalle vive en /api/diagnostico.
            "connection_error": bool(reporte["last_error"]),
            "verified": reporte["verified"],
            "verified_at": reporte["verified_at"],
        },
    }


@app.get("/api/diagnostico")
def diagnostico(request: FastAPIRequest, token: str = "") -> dict[str, Any]:
    """Revisa paso a paso entorno → conector → llave → sesión → tablas.

    Devuelve el error real de cada paso, sin secretos. Para que no quede abierto
    en un despliegue público exige una de tres condiciones: autenticación HTTP
    Basic activa (el middleware ya la valida), APP_DIAG_TOKEN correcto, o
    APP_ENV=development.
    """
    autorizado = (
        ACCESS_CONTROL_ACTIVE
        or APP_ENV != "production"
        or (DIAG_TOKEN and secrets.compare_digest(token, DIAG_TOKEN))
    )
    if not autorizado:
        raise HTTPException(
            status_code=403,
            detail=(
                "El diagnóstico está cerrado en producción. Active una de estas opciones en "
                "Railway y vuelva a intentarlo: (1) APP_BASIC_USER y APP_BASIC_PASSWORD "
                "—recomendado, protege todo el aplicativo—, o (2) APP_DIAG_TOKEN y llame a "
                "/api/diagnostico?token=EL_MISMO_VALOR."
            ),
        )
    if DEMO_MODE:
        return {
            "modo": "demo",
            "resumen": "El aplicativo está en modo demostración: no consulta Snowflake.",
            "siguiente_paso": "Quite APP_DEMO_MODE (o póngala en false) para usar datos reales.",
            "pasos": [],
        }

    pasos = snowflake.diagnostico()
    fallo = next((paso for paso in pasos if not paso["ok"]), None)
    if fallo:
        logger.error("Diagnóstico: falló el paso '%s' — %s", fallo["paso"], fallo.get("error"))
    return {
        "modo": "snowflake",
        "version": APP_VERSION,
        "todo_ok": fallo is None,
        "resumen": (
            "Todos los pasos respondieron correctamente."
            if fallo is None
            else f"Primer fallo en el paso «{fallo['paso']}»: {fallo.get('error')}"
        ),
        "siguiente_paso": _sugerencia(fallo),
        "pasos": pasos,
    }


def _sugerencia(fallo: dict[str, Any] | None) -> str:
    """Qué hacer según el paso que falló (lenguaje operativo, no técnico)."""
    if fallo is None:
        return "Nada pendiente: la conexión y las tablas responden."
    consejos = {
        "entorno": "Complete en Railway las variables que aparecen como faltantes y redespliegue.",
        "conector": "La imagen no trae el conector: revise que el build usara requirements-api.txt.",
        "llave_1": "Regenere el valor con [Convert]::ToBase64String([IO.File]::ReadAllBytes(\"rsa_key_1.der\")) "
                   "y péguelo en UNA sola línea, sin comillas ni saltos. Verifique la frase en SF_PRIVATE_KEY_PASSPHRASE_1.",
        "llave_2": "Misma revisión para la llave de respaldo, o retire SF_PRIVATE_KEY_B64_2 si no la usa.",
        "sesion": "Snowflake rechazó la conexión. Causas típicas: la llave pública no está registrada en el "
                  "usuario (ALTER USER … SET RSA_PUBLIC_KEY), el rol o el warehouse no existen, o una política "
                  "de red bloquea la IP de Railway. El texto del error lo precisa.",
        "consulta_simple": "La sesión abre pero no ejecuta consultas: revise que el warehouse esté activo y con crédito.",
        "tabla_filtros_generales": "El rol no ve la tabla de filtros: conceda SELECT sobre el esquema SEGMENTACION.",
        "tabla_filtros_exportadoras": "El rol no ve FILTROS_EXPORTADORAS: conceda SELECT sobre el esquema.",
        "tabla_empresas": "El rol no ve la tabla de empresas: conceda SELECT sobre TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P.",
        "tabla_bienes": "El rol no ve PUBLIC.BIENES_Y_SERVICIOS_P: sin ella fallan los filtros de exportación.",
        "tabla_eventos": "Sólo afecta la auditoría; el aplicativo funciona igual. Conceda INSERT en SEGUIMIENTO.EVENTOS.",
        "consulta_vista_previa": "La consulta real falló: revise el mensaje; suele ser una columna o tabla sin permisos.",
    }
    return consejos.get(fallo["paso"], "Revise el mensaje de error del paso indicado.")


@app.get("/api/metadata")
def metadata() -> dict[str, Any]:
    export_columns = [column for column in QUERY_COLUMNS.values() if EXPORT_INCLUDE_CONTACT_FIELDS or column not in CONTACT_COLUMNS]
    return {
        "title": APP_TITLE,
        "version": APP_VERSION,
        "demo": DEMO_MODE,
        "data_connection": "demo" if DEMO_MODE else ("configured" if snowflake.configured else "missing_configuration"),
        "preview_columns": PREVIEW_COLUMNS,
        "export_columns": export_columns,
        "column_sections": [{"title": title, "columns": [c for c in columns if c in export_columns]} for title, columns in COLUMN_SECTIONS],
        "sources": DATA_SOURCES,
        "periods": PERIODS,
        "notes": METHOD_NOTES,
        "filters": [*GENERAL_FILTERS, *EXPORT_FILTERS],
        "filter_groups": FILTER_GROUP_ORDER,
        "export_max_rows": EXPORT_MAX_ROWS,
        "preview_max_rows": PREVIEW_MAX_ROWS,
        "batch_max_nits": 5000,
        "contact_fields_included": EXPORT_INCLUDE_CONTACT_FIELDS,
    }


@app.post("/api/filters/options")
def filter_options(request: FilterOptionsRequest) -> dict[str, Any]:
    if DEMO_MODE:
        return demo.filter_options(request.selections)
    _require_connection()
    try:
        general = _options_for(GENERAL_FILTERS, _cached_filter_frame("general"), request.selections)
        exports = _options_for(EXPORT_FILTERS, _cached_filter_frame("export"), request.selections)
        return {"filters": [*general, *exports], "demo": False}
    except Exception as exc:  # noqa: BLE001
        logger.exception("No fue posible cargar los filtros")
        raise HTTPException(status_code=502, detail=_error_consulta("No fue posible cargar los filtros.")) from exc


@app.post("/api/companies/search")
def search_companies(request: SearchRequest, background: BackgroundTasks) -> dict[str, Any]:
    try:
        if DEMO_MODE:
            frame, total = demo.search(request)
        else:
            _require_connection()
            total = snowflake.scalar(build_count_query(request))
            frame = snowflake.dataframe(build_preview_query(request)) if total else pd.DataFrame(columns=list(QUERY_COLUMNS.values()))
            background.add_task(_log_event, "Búsqueda", f"Consulta {request.mode}", request.model_dump_json())
        columns = [column for column in PREVIEW_COLUMNS if column in frame.columns]
        preview = frame[columns] if columns else frame.iloc[:, 0:0]
        raw_page_count = (total + request.page_size - 1) // request.page_size if total else 0
        max_pages = max(1, PREVIEW_MAX_ROWS // request.page_size)
        return {
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "page_count": min(raw_page_count, max_pages),
            "preview_truncated": raw_page_count > max_pages,
            "columns": columns,
            "rows": _records(preview),
            "summary": request.summary(),
            "demo": DEMO_MODE,
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("La consulta falló")
        raise HTTPException(status_code=502, detail=_error_consulta("La consulta no pudo completarse.")) from exc


@app.get("/api/companies/{nit}")
def company_detail(nit: str, background: BackgroundTasks) -> dict[str, Any]:
    clean = clean_nit(nit)
    if not 2 <= len(clean) <= 12:
        raise HTTPException(status_code=422, detail="El NIT debe tener entre 2 y 12 dígitos.")
    try:
        if DEMO_MODE:
            frame = demo.company(clean)
        else:
            _require_connection()
            frame = snowflake.dataframe(build_company_query(clean))
            background.add_task(_log_event, "Consulta", "Ficha de empresa", f'{{"nit": "{clean}"}}')
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("La ficha falló")
        raise HTTPException(status_code=502, detail=_error_consulta("No fue posible consultar la ficha de la empresa.")) from exc
    if frame.empty:
        raise HTTPException(status_code=404, detail="No encontramos una empresa con ese NIT.")
    frame = _drop_contact_columns(frame)
    record = _records(frame.head(1))[0]
    sections = []
    placed: set[str] = set()
    for title, columns in COLUMN_SECTIONS:
        fields = [{"name": column, "value": record.get(column)} for column in columns if column in record]
        placed.update(column for column in columns if column in record)
        if fields:
            sections.append({"title": title, "fields": fields})
    leftovers = [{"name": column, "value": value} for column, value in record.items() if column not in placed]
    if leftovers:
        sections.append({"title": "Otras variables", "fields": leftovers})
    return {"nit": clean, "record": record, "sections": sections, "matches": int(len(frame)), "demo": DEMO_MODE}


@app.post("/api/companies/export")
def export_companies(request: SearchRequest, background: BackgroundTasks) -> StreamingResponse:
    try:
        if DEMO_MODE:
            frame = demo.all_rows(request, EXPORT_MAX_ROWS)
            total = len(frame)
        else:
            _require_connection()
            total = snowflake.scalar(build_count_query(request))
            if total > EXPORT_MAX_ROWS:
                raise HTTPException(
                    status_code=413,
                    detail=f"La consulta supera las {EXPORT_MAX_ROWS:,} empresas permitidas por archivo. Agrega filtros antes de descargar.".replace(",", "."),
                )
            frame = snowflake.dataframe(build_export_query(request, EXPORT_MAX_ROWS)) if total else pd.DataFrame(columns=list(QUERY_COLUMNS.values()))
            background.add_task(_log_event, "Descarga", "Descarga Excel formateado", request.model_dump_json())
        if frame.empty:
            raise HTTPException(status_code=404, detail="No hay resultados para descargar.")
        frame = _drop_contact_columns(frame)
        glossary = load_glossary()["entries"]
        file_buffer = create_export(frame, request, total, glossary)
        file_name = filename_for(request, total)
        encoded = quote(file_name)
        return StreamingResponse(
            file_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
                "X-Export-Filename": encoded,
                "Cache-Control": "no-store",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("La exportación falló")
        raise HTTPException(status_code=502, detail=_error_consulta("No fue posible preparar el Excel.")) from exc


@app.get("/api/glossary")
def glossary() -> dict[str, Any]:
    return load_glossary()


@app.get("/api/resources/glossary.xlsx")
def glossary_file() -> FileResponse:
    return FileResponse(
        GLOSSARY_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"ProColombia_Glosario_Tejido_Empresarial_{PERIODS['glossary']}.xlsx",
    )


@app.get("/api/resources/methodology.docx")
def methodology_file() -> FileResponse:
    return FileResponse(
        METHODOLOGY_PATH,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="ProColombia_Metodologia_Tejido_Empresarial.docx",
    )


@app.api_route("/api/{unknown_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], include_in_schema=False)
def unknown_api_route(unknown_path: str) -> JSONResponse:
    return JSONResponse({"detail": "Ruta de API no encontrada."}, status_code=404)


# ---------------------------------------------------------------------------
# Frontend compilado (SPA)
# ---------------------------------------------------------------------------
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


def _index_html() -> str:
    index_path = FRONTEND_DIST / "index.html"
    if not index_path.is_file():
        return "<!doctype html><meta charset='utf-8'><h1>Frontend no compilado</h1><p>Ejecute <code>npm run build</code> en <code>frontend/</code>.</p>"
    html = index_path.read_text(encoding="utf-8")
    if PUBLIC_ORIGIN.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        return html.replace("__PUBLIC_ORIGIN__", PUBLIC_ORIGIN)
    return (
        html.replace('<meta property="og:image" content="__PUBLIC_ORIGIN__/og.png" />', "")
        .replace('<meta name="twitter:image" content="__PUBLIC_ORIGIN__/og.png" />', "")
    )


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
def spa(full_path: str) -> Response:
    if full_path:
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
    return HTMLResponse(_index_html())

