from __future__ import annotations

import base64
import os
import threading
import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

try:  # El conector sólo se necesita con datos reales.
    from snowflake.snowpark import Session
except ImportError:  # pragma: no cover - el modo demostración no lo requiere
    Session = None  # type: ignore[assignment]


class SnowflakeService:
    def __init__(self) -> None:
        load_dotenv()
        self._session: "Session | None" = None
        self._lock = threading.Lock()
        self._last_working_key = 1

    @property
    def configured(self) -> bool:
        required = ["SF_ACCOUNT", "SF_USER", "SF_DATABASE", "SF_SCHEMA", "SF_WAREHOUSE", "SF_ROLE"]
        has_key = any(
            os.getenv(name)
            for name in (
                "SF_PRIVATE_KEY_B64_1",
                "SF_PRIVATE_KEY_PATH_1",
                "SF_PRIVATE_KEY_B64_2",
                "SF_PRIVATE_KEY_PATH_2",
            )
        )
        return Session is not None and has_key and all(bool(os.getenv(key)) for key in required)

    def _private_key(self, key_number: int) -> bytes | None:
        encoded = os.getenv(f"SF_PRIVATE_KEY_B64_{key_number}")
        if encoded:
            return base64.b64decode(encoded, validate=True)
        raw_path = os.getenv(f"SF_PRIVATE_KEY_PATH_{key_number}")
        if raw_path:
            path = Path(raw_path).expanduser().resolve()
            if not path.is_file():
                raise ValueError(f"No se encontró SF_PRIVATE_KEY_PATH_{key_number}.")
            return path.read_bytes()
        return None

    def _session_config(self, key_number: int) -> dict[str, Any]:
        private_key = self._private_key(key_number)
        passphrase = os.getenv(f"SF_PRIVATE_KEY_PASSPHRASE_{key_number}")
        if not private_key:
            raise ValueError(f"No se configuró la llave privada {key_number}.")
        config: dict[str, Any] = {
            "account": os.getenv("SF_ACCOUNT"),
            "user": os.getenv("SF_USER"),
            "private_key": private_key,
            "database": os.getenv("SF_DATABASE"),
            "schema": os.getenv("SF_SCHEMA"),
            "warehouse": os.getenv("SF_WAREHOUSE"),
            "role": os.getenv("SF_ROLE"),
            "query_tag": "TEJIDO_EMPRESARIAL_REACT",
        }
        if passphrase:
            config["private_key_passphrase"] = passphrase
        if any(value is None or value == "" for value in config.values()):
            raise ValueError("La configuración de Snowflake está incompleta.")
        return config

    def session(self) -> "Session":
        if Session is None:
            raise RuntimeError(
                "El conector de Snowflake no está instalado en este entorno. "
                "Instale snowflake-snowpark-python (requirements-api.txt) o use APP_DEMO_MODE=true."
            )
        if not self.configured:
            raise RuntimeError("Snowflake no está configurado en este entorno.")
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
                for attempt in range(3):
                    try:
                        self._session = Session.builder.configs(self._session_config(key_number)).create()
                        self._last_working_key = key_number
                        return self._session
                    except Exception as exc:  # Snowflake expone excepciones heterogéneas
                        last_error = exc
                        if "JWT token is invalid" in str(exc):
                            break
                        if attempt < 2:
                            time.sleep(2 ** attempt)
            raise RuntimeError("No fue posible establecer la conexión con Snowflake.") from last_error

    def dataframe(self, query: str) -> pd.DataFrame:
        try:
            return self.session().sql(query).to_pandas()
        except Exception:
            self._reset_session()
            return self.session().sql(query).to_pandas()

    def scalar(self, query: str, key: str = "TOTAL") -> int:
        try:
            rows = self.session().sql(query).collect()
        except Exception:
            self._reset_session()
            rows = self.session().sql(query).collect()
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


snowflake = SnowflakeService()
