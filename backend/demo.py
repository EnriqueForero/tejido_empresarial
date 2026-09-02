"""
Modo de demostración (APP_DEMO_MODE=true).

Registros 100 % sintéticos para probar la experiencia completa sin Snowflake:
filtros dependientes, búsqueda por razón social, NIT y lote, ficha y descarga.
Ninguna empresa aquí es real.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from backend.config import EXPORT_FILTERS, EXPORT_VALUE_COLUMNS, GENERAL_FILTERS, QUERY_COLUMNS
from backend.models import SearchRequest, clean_nit


_EXPORT_KEYS = list(EXPORT_VALUE_COLUMNS.values())

# Columna del resultado que alimenta cada filtro en modo demo.
FILTER_SOURCE_COLUMN = {
    "DEPARTAMENTO": "Departamento de la empresa",
    "MUNICIPIO": "Municipio de la empresa",
    "TAMANO": "Tamaño de la empresa",
    "RANGO_ANTIGUEDAD": "Rango de antigüedad de la empresa (años)",
    "RANGO_INGRESOS": "Rango de ingresos operacionales (COP)",
    "INVERSION_EXTRANJERA": "Inversión extranjera",
    "COD_CIIU_1": "Código CIIU Rev 4 - Actividad principal",
    "DESCRIPCION_CIIU_1": "Descripción CIIU Rev 4 - Actividad principal",
    "CADENA_CIIU_1": "Cadena CIIU Rev 4 - Actividad principal",
    "VALOR_AGREGADO_CIIU_1": "Valor Agregado - Actividad principal",
    "CADENA_SEGMENTACION": "Cadena de segmentación",
    "TRAYECTORIA_EXPORTADORA": "Trayectoria exportadora",
    "HA_EXPORTADO": "¿La empresa ha exportado?",
    "SECTOR": "Sector estrella",
    "SUBSECTOR": "Subsector estrella",
    "COD_POSICION_ARANCELARIA": "Código de posición arancelaria estrella",
    "DESC_POSICION_ARANCELARIA": "Descripción de posición arancelaria estrella",
    "HUB": "HUB estrella",
    "PAIS_DESTINO": "País destino estrella",
}


def _record(**fields: Any) -> dict[str, Any]:
    row: dict[str, Any] = {alias: None for alias in QUERY_COLUMNS.values()}
    exports = fields.pop("exports", [0, 0, 0, 0, 0, 0, 0])
    for alias, value in zip(_EXPORT_KEYS, exports):
        row[alias] = value
    row.update(fields)
    row.setdefault("Fuentes", "Registro sintético para demostración")
    row.setdefault("Organización jurídica", "SOCIEDAD POR ACCIONES SIMPLIFICADA")
    row.setdefault("Categoría de matrícula", "SOCIEDAD o PERSONA JURÍDICA PRINCIPAL")
    row.setdefault("Macrorregión de la empresa", "Demostración")
    row.setdefault("Dirección", "Dirección de demostración")
    row.setdefault("Teléfono", "6010000000")
    row.setdefault("Correo electrónico", "contacto@ejemplo.invalid")
    row.setdefault("ID del representante legal", "10000000")
    row.setdefault("Representante legal", "REPRESENTANTE DE DEMOSTRACIÓN")
    row.setdefault("Cantidad de establecimientos", 1)
    return row


def _company(
    index: int, name: str, dept: str, city: str, dept_code: str, city_code: str, size: str,
    ciiu: str, ciiu_desc: str, ciiu_chain: str, value_added: str, chain: str, trajectory: str,
    exported: str, foreign: str, age: float, revenue: int, employees: int, women: int,
    sector: str | None, subsector: str | None, tariff: str | None, tariff_desc: str | None,
    country: str | None, hub: str | None, exports: list[float],
) -> dict[str, Any]:
    age_range = "A. 0 - 5 años" if age <= 5 else "B. 6 - 10 años" if age <= 10 else "C. 11 - 15 años" if age <= 15 else "D. 16 - 20 años" if age <= 20 else "E. Más de 20 años"
    revenue_range = "K. Más de COP 2.099,3 millones" if revenue > 2_099_300_000 else "H. COP 500 - 2.099,3 millones" if revenue > 500_000_000 else "E. COP 100 - 500 millones"
    exporter = exported == "Sí"
    return _record(
        **{
            "NIT": f"9000000{index:02d}",
            "Dígito de verificación": str((index * 7) % 10),
            "Razón social": name,
            "Tamaño de la empresa": size,
            "Código del departamento de la empresa": dept_code,
            "Departamento de la empresa": dept,
            "Código del municipio de la empresa": city_code,
            "Municipio de la empresa": city,
            "Código CIIU Rev 4 - Actividad principal": ciiu,
            "Descripción CIIU Rev 4 - Actividad principal": ciiu_desc,
            "Cadena CIIU Rev 4 - Actividad principal": ciiu_chain,
            "Valor Agregado - Actividad principal": value_added,
            "Rango de antigüedad de la empresa (años)": age_range,
            "Antigüedad de la empresa (años)": age,
            "Inversión extranjera": foreign,
            "Activos (COP)": int(revenue * 1.6),
            "Rango de ingresos operacionales (COP)": revenue_range,
            "Ingresos operacionales (COP)": revenue,
            "Utilidad (COP)": int(revenue * 0.07),
            "Empleados": employees,
            "Cantidad de mujeres empleadas": women,
            "Cantidad de mujeres en cargos directivos": max(1, women // 12),
            "Tipo estrella": "No Mineras" if exporter else "No exportó ult. 5 años",
            "Cadena estrella": chain if exporter else "No exportó ult. 5 años",
            "Sector estrella": sector if exporter else "No exportó ult. 5 años",
            "Subsector estrella": subsector if exporter else "No exportó ult. 5 años",
            "Código de posición arancelaria estrella": tariff if exporter else "No exportó ult. 5 años",
            "Descripción de posición arancelaria estrella": tariff_desc if exporter else "No exportó ult. 5 años",
            "Valor agregado exportaciones estrella": ("Manufacturas de baja tecnología" if "Moda" in chain or "Agro" in chain else "Servicios de alta tecnología intensivos en conocimiento") if exporter else "No exportó ult. 5 años",
            "Código de departamento exportaciones estrella": dept_code if exporter else "No exportó ult. 5 años",
            "Departamento exportaciones estrella": dept if exporter else "No exportó ult. 5 años",
            "País destino estrella": country if exporter else "No exportó ult. 5 años",
            "HUB estrella": hub if exporter else "No exportó ult. 5 años",
            "Trayectoria exportadora": trajectory,
            "¿La empresa ha exportado?": exported,
            "Empresa exportadora NME según actividad económica": "Sí" if exporter else "No",
            "Cadena de segmentación": chain,
            "exports": exports,
        }
    )


DEMO_ROWS: list[dict[str, Any]] = [
    _company(1, "CONFECCIONES ANDINAS DEMO S.A.S.", "Antioquia", "Medellín", "05", "05001", "Grande", "1410", "Confección de prendas de vestir, excepto prendas de piel", "Sistema Moda", "Bienes tecnología baja", "Sistema Moda", "Pymex", "Sí", "No", 27.4, 225_116_000_000, 877, 591, "Textiles y confecciones", "Ropa interior y pijamas", "6212100000", "Sostenes (corpiños), incluso de punto", "Ecuador", "Latinoamérica", [156_936.88, 326_862.27, 225_666.93, 493_383.75, 657_088.53, 251_330.96, 310_004.10]),
    _company(2, "TEJIDOS DEL VALLE DEMO S.A.", "Valle del Cauca", "Cali", "76", "76001", "Grande", "1311", "Preparación e hilatura de fibras textiles", "Sistema Moda", "Bienes tecnología baja", "Sistema Moda", "Top Exportadora", "Sí", "Sí", 46.3, 257_715_669_000, 662, 428, "Textiles y confecciones", "Telas y tejidos", "6006220000", "Los demás tejidos de punto, de algodón, teñidos", "Perú", "Alianza Pacífico", [997_627.87, 882_996.72, 616_911.81, 877_632.36, 8_365_610.45, 3_061_980.87, 3_409_082.36]),
    _company(3, "CAFÉ DE ORIGEN DEMO S.A.S.", "Huila", "Pitalito", "41", "41551", "Mediana", "1061", "Trilla de café", "Agroalimentos", "Bienes tecnología baja", "Agroalimentos", "Pymex", "Sí", "No", 12.1, 64_800_000_000, 210, 96, "Agroindustria", "Café", "0901119000", "Café sin tostar, sin descafeinar, los demás", "Estados Unidos", "Norteamérica", [410_200.0, 455_900.0, 502_300.0, 610_800.0, 745_000.0, 301_000.0, 355_400.0]),
    _company(4, "SOFTWARE CARIBE DEMO S.A.S.", "Atlántico", "Barranquilla", "08", "08001", "Mediana", "6201", "Actividades de desarrollo de sistemas informáticos", "Industrias 4.0", "Servicios de alta tecnología intensivos en conocimiento", "Industrias 4.0", "No constantes", "Sí", "No", 8.5, 86_000_000_000, 340, 150, "Servicios", "Software y TI", "SOFTWARE", "Software y servicios TI", "México", "Latinoamérica", [0, 120_000.0, 0, 940_000.0, 380_000.0, 120_000.0, 394_800.0]),
    _company(5, "TURISMO RESPONSABLE DEMO S.A.S.", "Bolívar", "Cartagena de Indias", "13", "13001", "Pequeña", "7911", "Actividades de las agencias de viaje", "Turismo", "Servicios menos intensivos en conocimiento", "Turismo", "Futuros exportadores", "No", "No", 15.2, 18_500_000_000, 41, 27, None, None, None, None, None, None, [0, 0, 0, 0, 0, 0, 0]),
    _company(6, "ALIMENTOS DEL TERRITORIO DEMO S.A.S.", "Valle del Cauca", "Palmira", "76", "76520", "Mediana", "1081", "Elaboración de productos de panadería", "Agroalimentos", "Bienes tecnología baja", "Agroalimentos", "Pymex", "Sí", "No", 19.8, 47_000_000_000, 190, 122, "Agroindustria", "Panadería y molinería", "1905310000", "Galletas dulces (con adición de edulcorante)", "Estados Unidos", "Norteamérica", [212_000.0, 244_000.0, 268_000.0, 290_000.0, 510_000.0, 201_000.0, 214_200.0]),
    _company(7, "METALMECÁNICA DEL EJE DEMO S.A.S.", "Risaralda", "Pereira", "66", "66001", "Mediana", "2511", "Fabricación de productos metálicos para uso estructural", "Metalmecánica", "Bienes tecnología media-baja", "Metalmecánica", "No constantes", "Sí", "No", 22.0, 39_000_000_000, 160, 38, "Metalmecánica", "Estructuras metálicas", "7308909000", "Las demás construcciones y sus partes, de hierro o acero", "Panamá", "Centroamérica y Caribe", [0, 88_000.0, 0, 0, 285_000.0, 90_000.0, 119_700.0]),
    _company(8, "COSMÉTICA NATURAL DEMO S.A.S.", "Cundinamarca", "Chía", "25", "25175", "Pequeña", "2023", "Fabricación de jabones y detergentes, perfumes y preparados de tocador", "Químicos y ciencias de la vida", "Bienes tecnología media-alta", "Químicos y ciencias de la vida", "Futuros exportadores", "Sí", "No", 4.5, 9_800_000_000, 36, 29, "Químicos", "Cosméticos y aseo", "3304990000", "Las demás preparaciones de belleza, maquillaje y cuidado de la piel", "Chile", "Alianza Pacífico", [0, 0, 0, 0, 18_400.0, 0, 6_200.0]),
    _company(9, "FLORES DE LA SABANA DEMO S.A.", "Cundinamarca", "Madrid", "25", "25430", "Grande", "0119", "Otros cultivos transitorios n.c.p.", "Agroalimentos", "Bienes primarios", "Agroalimentos", "Top Exportadora", "Sí", "Sí", 31.7, 310_000_000_000, 1_450, 940, "Agroindustria", "Flores frescas", "0603110000", "Rosas frescas, cortadas para ramos o adornos", "Estados Unidos", "Norteamérica", [9_100_000.0, 9_650_000.0, 10_200_000.0, 10_900_000.0, 11_800_000.0, 5_100_000.0, 5_460_000.0]),
    _company(10, "HOTELES DEL PACÍFICO DEMO S.A.S.", "Valle del Cauca", "Buenaventura", "76", "76109", "Micro", "5511", "Alojamiento en hoteles", "Turismo", "Servicios menos intensivos en conocimiento", "Turismo", "Futuros exportadores", "No", "No", 3.2, 620_000_000, 9, 6, None, None, None, None, None, None, [0, 0, 0, 0, 0, 0, 0]),
    _company(11, "PLÁSTICOS INDUSTRIALES DEMO S.A.S.", "Antioquia", "Itagüí", "05", "05360", "Mediana", "2229", "Fabricación de artículos de plástico n.c.p.", "Metalmecánica", "Bienes tecnología media-baja", "Metalmecánica", "Pymex", "Sí", "No", 18.3, 58_400_000_000, 240, 70, "Metalmecánica", "Plásticos", "3923309000", "Bombonas, botellas, frascos y artículos similares, de plástico", "Ecuador", "Latinoamérica", [140_000.0, 152_000.0, 160_000.0, 175_000.0, 190_000.0, 80_000.0, 84_000.0]),
    _company(12, "ANIMACIÓN DIGITAL DEMO S.A.S.", "Bogotá D.C.", "Bogotá D.C.", "11", "11001", "Pequeña", "5911", "Actividades de producción de películas cinematográficas, videos, programas, anuncios y comerciales de televisión", "Industrias 4.0", "Servicios de alta tecnología intensivos en conocimiento", "Industrias 4.0", "No constantes", "Sí", "Sí", 6.7, 12_400_000_000, 58, 31, "Servicios", "Audiovisual y animación", "AUDIOVISUAL", "Servicios audiovisuales y animación", "España", "Europa", [0, 45_000.0, 0, 210_000.0, 0, 0, 96_000.0]),
    _company(13, "MADERAS SOSTENIBLES DEMO S.A.S.", "Bogotá D.C.", "Bogotá D.C.", "11", "11001", "Grande", "1690", "Fabricación de otros productos de madera", "Sistema Moda", "Bienes tecnología baja", "Metalmecánica", "Pymex", "Sí", "No", 25.0, 120_000_000_000, 520, 180, "Metalmecánica", "Materiales de construcción", "4418200000", "Puertas y sus marcos, contramarcos y umbrales, de madera", "Estados Unidos", "Norteamérica", [620_000.0, 700_000.0, 745_000.0, 810_000.0, 905_000.0, 380_000.0, 402_000.0]),
    _company(14, "BIOTECNOLOGÍA ANDINA DEMO S.A.S.", "Antioquia", "Rionegro", "05", "05615", "Pequeña", "7210", "Investigaciones y desarrollo experimental en ciencias naturales e ingeniería", "Químicos y ciencias de la vida", "Servicios de alta tecnología intensivos en conocimiento", "Químicos y ciencias de la vida", "Futuros exportadores", "No", "Sí", 2.9, 4_300_000_000, 22, 14, None, None, None, None, None, None, [0, 0, 0, 0, 0, 0, 0]),
]


def _matches(row: dict[str, Any], request: SearchRequest) -> bool:
    for key, values in request.filters.items():
        column = FILTER_SOURCE_COLUMN.get(key)
        if values and column and str(row.get(column)) not in values:
            return False
    return True


def filter_options(selections: dict[str, list[str]] | None = None) -> dict[str, Any]:
    """Opciones dependientes: cada filtro ofrece los valores compatibles con las demás selecciones."""
    selections = selections or {}
    definitions = [*GENERAL_FILTERS, *EXPORT_FILTERS]
    output: list[dict[str, Any]] = []
    for definition in definitions:
        key = definition["key"]
        column = FILTER_SOURCE_COLUMN[key]
        others = {k: v for k, v in selections.items() if k != key and v}
        candidates = [row for row in DEMO_ROWS if all(str(row.get(FILTER_SOURCE_COLUMN[k])) in v for k, v in others.items() if k in FILTER_SOURCE_COLUMN)]
        values = sorted({str(row[column]) for row in candidates if row.get(column) not in (None, "") and not str(row[column]).startswith("No exportó")}, key=str.casefold)
        output.append({**definition, "options": values, "truncated": False})
    return {"filters": output, "demo": True}


def search(request: SearchRequest) -> tuple[pd.DataFrame, int]:
    rows = DEMO_ROWS
    if request.mode == "business_name":
        term = request.term.casefold()
        rows = [row for row in rows if term in str(row["Razón social"]).casefold()]
    elif request.mode == "nit":
        term = clean_nit(request.term)
        rows = [row for row in rows if term in str(row["NIT"])]
    elif request.mode == "batch_nits":
        allowed = set(request.nits)
        rows = [row for row in rows if str(row["NIT"]) in allowed]
    elif request.mode == "filters":
        rows = [row for row in rows if _matches(row, request)]
    rows = sorted(rows, key=lambda row: -(row.get("Ingresos operacionales (COP)") or 0))
    total = len(rows)
    start = (request.page - 1) * request.page_size
    return pd.DataFrame(rows[start:start + request.page_size], columns=list(QUERY_COLUMNS.values())), total


def all_rows(request: SearchRequest, limit: int) -> pd.DataFrame:
    export_request = request.model_copy(update={"page": 1, "page_size": 100})
    frame, _ = search(export_request)
    return frame.head(limit)


def company(nit: str) -> pd.DataFrame:
    target = clean_nit(nit)
    rows = [row for row in DEMO_ROWS if str(row["NIT"]) == target]
    return pd.DataFrame(rows, columns=list(QUERY_COLUMNS.values()))


__all__ = ["DEMO_ROWS", "filter_options", "search", "all_rows", "company"]
