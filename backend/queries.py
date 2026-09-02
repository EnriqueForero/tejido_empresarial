"""
Generación de SQL para Snowflake.

Se conserva la lógica del aplicativo original (`segmentacion_utils.py`):
- filtros generales sobre la tabla de empresas (alias A);
- filtros de exportación como sub-consulta sobre BIENES_Y_SERVICIOS_P (alias B);
- búsqueda por razón social con LIKE sin distinguir mayúsculas;
- búsqueda por NIT con coincidencia parcial;
- búsqueda masiva por lista de NIT.
Todos los valores se escapan como literales SQL y las columnas provienen de listas blancas.
"""
from __future__ import annotations

from backend.config import (
    COMPANY_TABLE,
    EXPORT_FILTER_KEYS,
    EXPORT_TABLE,
    FILTERS_BY_KEY,
    GENERAL_FILTER_KEYS,
    PREVIEW_COLUMNS,
    QUERY_COLUMNS,
)
from backend.models import SearchRequest, clean_nit


def sql_literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _active_filters(request: SearchRequest, allowed: set[str]) -> list[str]:
    conditions: list[str] = []
    for key, values in request.filters.items():
        if key not in allowed or key not in FILTERS_BY_KEY or not values:
            continue
        column = FILTERS_BY_KEY[key]["query_column"]
        serialized = ", ".join(sql_literal(value) for value in values)
        conditions.append(f"{column} IN ({serialized})")
    return conditions


def _select_clause(columns: dict[str, str]) -> str:
    return ", ".join(f'A.{column} AS "{alias}"' for column, alias in columns.items())


def build_base_query(request: SearchRequest, columns: dict[str, str] | None = None) -> str:
    selected_columns = columns or QUERY_COLUMNS
    conditions: list[str] = []

    if request.mode == "filters":
        conditions.extend(f"A.{condition}" for condition in _active_filters(request, GENERAL_FILTER_KEYS))
        export_conditions = [f"B.{condition}" for condition in _active_filters(request, EXPORT_FILTER_KEYS)]
        if export_conditions:
            conditions.append(
                "A.NIT IN (SELECT DISTINCT B.NIT FROM "
                f"{EXPORT_TABLE} AS B WHERE {' AND '.join(export_conditions)})"
            )
    elif request.mode == "business_name":
        conditions.append(f"UPPER(A.RAZON_SOCIAL) LIKE UPPER({sql_literal('%' + request.term + '%')})")
    elif request.mode == "nit":
        conditions.append(f"CAST(A.NIT AS VARCHAR) LIKE {sql_literal('%' + clean_nit(request.term) + '%')}")
    elif request.mode == "batch_nits":
        conditions.append("CAST(A.NIT AS VARCHAR) IN (" + ", ".join(sql_literal(nit) for nit in request.nits) + ")")

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return f"SELECT {_select_clause(selected_columns)} FROM {COMPANY_TABLE} AS A WHERE {where_clause}"


def build_preview_query(request: SearchRequest) -> str:
    offset = (request.page - 1) * request.page_size
    preview_columns = {column: alias for column, alias in QUERY_COLUMNS.items() if alias in PREVIEW_COLUMNS}
    return (
        f"{build_base_query(request, preview_columns)} "
        "ORDER BY A.INGRESOS_OPERACIONALES DESC NULLS LAST, A.NIT "
        f"LIMIT {request.page_size} OFFSET {offset}"
    )


def build_count_query(request: SearchRequest) -> str:
    return f"SELECT COUNT(*) AS TOTAL FROM ({build_base_query(request)}) AS RESULTADOS"


def build_export_query(request: SearchRequest, limit: int) -> str:
    return (
        f"{build_base_query(request)} "
        "ORDER BY A.INGRESOS_OPERACIONALES DESC NULLS LAST, A.NIT "
        f"LIMIT {limit}"
    )


def build_company_query(nit: str) -> str:
    """Ficha completa de una empresa por NIT exacto."""
    return (
        f"SELECT {_select_clause(QUERY_COLUMNS)} FROM {COMPANY_TABLE} AS A "
        f"WHERE CAST(A.NIT AS VARCHAR) = {sql_literal(clean_nit(nit))} "
        "ORDER BY A.INGRESOS_OPERACIONALES DESC NULLS LAST LIMIT 5"
    )
