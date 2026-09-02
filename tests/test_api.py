import os

os.environ["APP_DEMO_MODE"] = "true"
os.environ["APP_ENV"] = "development"

from fastapi.testclient import TestClient

from backend.config import PREVIEW_COLUMNS
from backend.main import app


client = TestClient(app)


def test_health_and_metadata() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    cuerpo = health.json()
    assert cuerpo["data_connection"] == "demo"
    assert cuerpo["demo_mode"] is True
    # El health dice si el conector está instalado y qué variables faltan.
    assert set(cuerpo["snowflake"]) == {
        "connector_installed",
        "connector_version",
        "missing_variables",
        "key_sources",
        "connection_error",
        "verified",
        "verified_at",
    }
    # En modo demostración nunca se afirma que la conexión esté verificada.
    assert cuerpo["snowflake"]["verified"] is False

    metadata = client.get("/api/metadata")
    assert metadata.status_code == 200
    body = metadata.json()
    assert body["preview_columns"] == PREVIEW_COLUMNS
    assert len(body["filters"]) == 19
    assert all(definition["help"] for definition in body["filters"])
    assert body["contact_fields_included"] is True
    assert "Correo electrónico" in body["export_columns"]


def test_filter_options_are_dependent() -> None:
    everything = client.post("/api/filters/options", json={"selections": {}}).json()
    municipalities = next(item for item in everything["filters"] if item["key"] == "MUNICIPIO")
    assert len(municipalities["options"]) > 5

    narrowed = client.post("/api/filters/options", json={"selections": {"DEPARTAMENTO": ["Antioquia"]}}).json()
    municipalities = next(item for item in narrowed["filters"] if item["key"] == "MUNICIPIO")
    assert set(municipalities["options"]) == {"Medellín", "Itagüí", "Rionegro"}
    departments = next(item for item in narrowed["filters"] if item["key"] == "DEPARTAMENTO")
    assert "Antioquia" in departments["options"] and len(departments["options"]) > 1


def test_filter_search_and_pagination_contract() -> None:
    response = client.post(
        "/api/companies/search",
        json={"mode": "filters", "filters": {"DEPARTAMENTO": ["Antioquia"]}, "term": "", "nits": [], "page": 1, "page_size": 25},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["demo"] is True
    assert body["columns"] == PREVIEW_COLUMNS
    assert all(row["Departamento de la empresa"] == "Antioquia" for row in body["rows"])
    assert body["rows"][0]["Ingresos operacionales (COP)"] >= body["rows"][1]["Ingresos operacionales (COP)"]
    assert "Correo electrónico" not in body["rows"][0]


def test_export_filters_apply() -> None:
    response = client.post("/api/companies/search", json={"mode": "filters", "filters": {"PAIS_DESTINO": ["Estados Unidos"]}})
    assert response.status_code == 200
    assert response.json()["total"] == 4


def test_direct_search_validation_and_results() -> None:
    invalid = client.post("/api/companies/search", json={"mode": "business_name", "term": "A"})
    assert invalid.status_code == 422

    valid = client.post("/api/companies/search", json={"mode": "business_name", "term": "demo s.a.s."})
    assert valid.status_code == 200
    assert valid.json()["total"] >= 10

    by_nit = client.post("/api/companies/search", json={"mode": "nit", "term": "900.000.003"})
    assert by_nit.json()["total"] == 1

    batch = client.post("/api/companies/search", json={"mode": "batch_nits", "nits": ["900000001", "900000002", "1"]})
    assert batch.json()["total"] == 2


def test_company_profile() -> None:
    response = client.get("/api/companies/900000002")
    assert response.status_code == 200
    body = response.json()
    assert body["record"]["Razón social"] == "TEJIDOS DEL VALLE DEMO S.A."
    titles = [section["title"] for section in body["sections"]]
    assert titles[0] == "Identificación y ubicación"
    assert "Exportaciones por periodo (FOB USD)" in titles
    assert client.get("/api/companies/999999999").status_code == 404
    assert client.get("/api/companies/x").status_code == 422


def test_glossary_and_formatted_export() -> None:
    glossary = client.get("/api/glossary")
    assert glossary.status_code == 200
    body = glossary.json()
    assert body["institutional_count"] == 61
    assert body["supplementary_count"] == 2
    assert body["count"] == 63
    assert body["coverage"]["missing"] == []
    trajectory = next(entry for entry in body["entries"] if entry["variable"] == "Trayectoria exportadora")
    assert trajectory["filter_key"] == "TRAYECTORIA_EXPORTADORA"
    assert trajectory["in_preview"] is True

    response = client.post("/api/companies/export", json={"mode": "nit", "term": "900000001"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert response.content.startswith(b"PK")
    assert "ProColombia_TejidoEmpresarial_NIT_900000001_" in response.headers["x-export-filename"]


def test_diagnostico_en_modo_demostracion() -> None:
    respuesta = client.get("/api/diagnostico")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "demo"
    assert "demostración" in cuerpo["resumen"]
    assert "APP_DEMO_MODE" in cuerpo["siguiente_paso"]


def test_spa_fallback_and_unknown_routes() -> None:
    page = client.get("/consultar")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]

    response = client.get("/api/no-existe")
    assert response.status_code == 404
    assert response.json()["detail"] == "Ruta de API no encontrada."
    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")


def test_unknown_filters_are_rejected() -> None:
    response = client.post("/api/companies/search", json={"mode": "filters", "filters": {"NO_PERMITIDO": ["x"]}})
    assert response.status_code == 422
