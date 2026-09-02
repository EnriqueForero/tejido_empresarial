from backend.models import SearchRequest
from backend.queries import build_base_query, build_company_query, build_count_query, build_preview_query, sql_literal


def test_sql_literals_escape_quotes() -> None:
    assert sql_literal("O'Brien") == "'O''Brien'"


def test_filter_query_uses_allowlisted_columns() -> None:
    request = SearchRequest(mode="filters", filters={"DEPARTAMENTO": ["Valle del Cauca"], "PAIS_DESTINO": ["Estados Unidos"]})
    query = build_base_query(request)
    assert "A.DEPARTAMENTO_EMP IN ('Valle del Cauca')" in query
    assert "B.PAIS_DESTINO IN ('Estados Unidos')" in query
    assert "APP_SEGMENTACION_EXPORTACIONES.PUBLIC.BIENES_Y_SERVICIOS_P AS B" in query
    assert "TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P AS A" in query


def test_preview_pagination_is_bounded_and_escaped() -> None:
    request = SearchRequest(mode="business_name", term="O'Brien", page=3, page_size=25)
    query = build_preview_query(request)
    assert "LIKE UPPER('%O''Brien%')" in query
    assert "LIMIT 25 OFFSET 50" in query
    assert "ORDER BY A.INGRESOS_OPERACIONALES DESC NULLS LAST" in query


def test_nit_queries_only_use_digits() -> None:
    request = SearchRequest(mode="nit", term="900.409-346 ' OR x")
    assert "LIKE '%900409346%'" in build_base_query(request)
    assert "CAST(A.NIT AS VARCHAR) = '900409346'" in build_company_query("900.409.346")
    count = build_count_query(SearchRequest(mode="batch_nits", nits=["1234567", "  8901234 "]))
    assert "IN ('1234567', '8901234')" in count
