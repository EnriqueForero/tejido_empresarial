"""
Generador del libro Excel de resultados.

Objetivo: que el archivo descargado se lea sin esfuerzo. Cada libro contiene:

- Resumen          → qué se consultó, cuándo, con qué criterios, cortes y fuentes; guía de hojas.
- Ficha_Empresa    → sólo cuando la consulta devuelve una empresa: lectura vertical por secciones.
- Vista_Principal  → variables de lectura rápida, congeladas, con filtros y barras de datos.
- Datos_Completos  → todas las variables entregadas por la consulta.
- Diccionario      → definición y fuente de cada columna (glosario institucional) y su uso en el aplicativo.

Convenciones de formato: encabezados azul noche con acento ámbar (identidad ProColombia
digital), tipografías Jost/Maven Pro, cebra suave, anchos calculados por contenido,
identificadores como texto (conservan ceros iniciales), montos con separador de miles,
paneles congelados, autofiltro y configuración de impresión.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from io import BytesIO
from typing import Any, Iterable

import pandas as pd
import xlsxwriter

from backend.config import (
    APP_VERSION,
    COLUMN_SECTIONS,
    DATA_SOURCES,
    EXPORT_VALUE_COLUMNS,
    FILTERS_BY_KEY,
    PERIODS,
    PREVIEW_COLUMNS,
)
from backend.models import MODE_LABELS, SearchRequest, clean_nit


NAVY = "#011627"
NAVY_2 = "#062B43"
NAVY_3 = "#0A3D5C"
AMBER = "#FFA400"
AMBER_SOFT = "#FFF4DC"
PAPER = "#F4F7FA"
WHITE = "#FFFFFF"
TEXT = "#0B2233"
MUTED = "#52667A"
BORDER = "#D5DEE5"
BLUE_LIGHT = "#EAF1FB"
GREEN_LIGHT = "#E8F4EE"
GREEN_TEXT = "#1E6B45"
RED_LIGHT = "#FBE9EC"
RED_TEXT = "#8C2638"

FONT_DISPLAY = "Jost"
FONT_BODY = "Maven Pro"

IDENTIFIER_TERMS = ("NIT", "Dígito", "Código", "ID del representante", "posición arancelaria estrella")
INTEGER_TERMS = ("Empleados", "Cantidad de mujeres", "Cantidad de establecimientos", "Servicios ", "Negocios ", "Oportunidades ")
LONG_TEXT_TERMS = ("Descripción", "Fuentes", "Dirección", "Correo", "Razón social", "Representante", "Teléfono", "Empresa gemela")
YES_NO_COLUMNS = (
    "¿La empresa ha exportado?",
    "Inversión extranjera",
    "Empresa exportadora NME según actividad económica",
    "Empresa atendida por ProColombia",
    "Servicios prestados por ProColombia",
    "Negocios facilitados por ProColombia",
    "Oportunidades 20",
)

TYPE_LABELS = {
    "filters": "Segmentacion",
    "business_name": "RazonSocial",
    "nit": "NIT",
    "batch_nits": "LoteNIT",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _slug(value: str, limit: int = 40) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-")
    return (safe or "consulta")[:limit].strip("-")


def filename_for(request: SearchRequest, total: int, now: datetime | None = None) -> str:
    """Nombre descriptivo: institución, aplicativo, tipo de consulta, criterio, fecha y tamaño."""
    if request.mode == "filters":
        first_value = next((values[0] for values in request.filters.values() if values), "")
        active = sum(len(values) for values in request.filters.values())
        criterion = _slug(first_value) if first_value else "BaseCompleta"
        if active > 1:
            criterion = f"{criterion}_y-{active - 1}-mas"
    elif request.mode == "business_name":
        criterion = _slug(request.term)
    elif request.mode == "nit":
        criterion = clean_nit(request.term) or "NIT"
    else:
        criterion = f"{len(request.nits)}-NIT"
    stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H%M")
    noun = "empresa" if total == 1 else "empresas"
    return f"ProColombia_TejidoEmpresarial_{TYPE_LABELS[request.mode]}_{criterion}_{stamp}_{total}-{noun}.xlsx"


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass
    if isinstance(value, str):
        value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", value)
        value = value[:32760]
        if value.startswith(("=", "+", "-", "@")) and not re.fullmatch(r"-?\d+([.,]\d+)?", value):
            return "'" + value
    return value


def _is_identifier(header: str) -> bool:
    return any(term.casefold() in header.casefold() for term in IDENTIFIER_TERMS)


def _excel_value(header: str, value: Any) -> Any:
    safe = _safe_value(value)
    if safe is None:
        return None
    if _is_identifier(header):
        if isinstance(safe, float) and safe.is_integer():
            safe = int(safe)
        return str(safe)
    return safe


def _number_format(header: str) -> str:
    if _is_identifier(header):
        return "@"
    if "(COP)" in header:
        return "#,##0;[Red]-#,##0"
    if "FOB USD" in header:
        return "#,##0.00;[Red]-#,##0.00"
    if header == "Antigüedad de la empresa (años)":
        return "0.0"
    if any(term in header for term in INTEGER_TERMS):
        return "#,##0"
    if "Índice" in header:
        return "0.00"
    if "Distancia" in header:
        return "0.0000"
    return "General"


def _is_numeric_header(header: str) -> bool:
    return _number_format(header) not in {"@", "General"}


def _preferred_width(header: str, values: Iterable[Any]) -> float:
    longest = 0
    for value in values:
        if value is not None:
            longest = max(longest, len(str(value)))
    if any(term in header for term in LONG_TEXT_TERMS):
        return float(min(max(24, longest + 2), 48))
    if _is_numeric_header(header):
        return float(min(max(14, longest + 4), 22))
    header_words = max((len(word) for word in header.split()), default=8)
    return float(min(max(12, header_words + 2, longest + 2), 30))


# ---------------------------------------------------------------------------
# Formatos
# ---------------------------------------------------------------------------
class Styles:
    def __init__(self, workbook: xlsxwriter.Workbook) -> None:
        self.workbook = workbook
        self._body_cache: dict[tuple[str, bool, bool], Any] = {}
        base = {"font_name": FONT_BODY, "font_size": 10, "font_color": TEXT}
        self.title = workbook.add_format({"font_name": FONT_DISPLAY, "font_size": 20, "bold": True, "font_color": WHITE, "bg_color": NAVY, "valign": "vcenter", "indent": 1})
        self.subtitle = workbook.add_format({"font_name": FONT_BODY, "font_size": 10.5, "font_color": "#D8E2E9", "bg_color": NAVY_2, "valign": "vcenter", "indent": 1})
        self.ribbon = workbook.add_format({"bg_color": AMBER})
        self.kicker = workbook.add_format({"font_name": "IBM Plex Mono", "font_size": 9, "font_color": "#B97A00", "bold": True})
        self.header = workbook.add_format({
            "font_name": FONT_BODY, "font_size": 10, "bold": True, "font_color": WHITE, "bg_color": NAVY,
            "align": "center", "valign": "vcenter", "text_wrap": True,
            "bottom": 5, "bottom_color": AMBER, "right": 1, "right_color": "#284258",
        })
        self.section = workbook.add_format({"font_name": FONT_DISPLAY, "font_size": 12, "bold": True, "font_color": WHITE, "bg_color": NAVY_3, "valign": "vcenter", "indent": 1})
        self.label = workbook.add_format({**base, "bold": True, "font_color": NAVY, "bg_color": BLUE_LIGHT, "valign": "top", "text_wrap": True, "bottom": 1, "bottom_color": BORDER, "indent": 1})
        self.value = workbook.add_format({**base, "valign": "top", "text_wrap": True, "bottom": 1, "bottom_color": BORDER, "indent": 1})
        self.value_numeric_cache: dict[str, Any] = {}
        self.note = workbook.add_format({**base, "font_color": "#6B5010", "bg_color": AMBER_SOFT, "valign": "top", "text_wrap": True, "indent": 1})
        self.muted = workbook.add_format({**base, "font_color": MUTED, "italic": True, "text_wrap": True, "valign": "top"})
        self.heading = workbook.add_format({"font_name": FONT_DISPLAY, "font_size": 13, "bold": True, "font_color": NAVY})
        self.pending = workbook.add_format({"bg_color": RED_LIGHT, "font_color": RED_TEXT})
        self.validated = workbook.add_format({"bg_color": GREEN_LIGHT, "font_color": GREEN_TEXT})
        self.yes = workbook.add_format({"bg_color": GREEN_LIGHT, "font_color": GREEN_TEXT, "bold": True})
        self.no = workbook.add_format({"font_color": MUTED})

    def body(self, number_format: str, wrap: bool, alternate: bool):
        key = (number_format, wrap, alternate)
        if key not in self._body_cache:
            numeric = number_format not in {"@", "General"}
            self._body_cache[key] = self.workbook.add_format({
                "font_name": FONT_BODY, "font_size": 9.5, "font_color": TEXT,
                "bg_color": PAPER if alternate else WHITE,
                "valign": "top", "text_wrap": wrap,
                "align": "right" if numeric else "left",
                "bottom": 1, "bottom_color": BORDER, "right": 1, "right_color": BORDER,
                "num_format": number_format,
            })
        return self._body_cache[key]

    def value_numeric(self, number_format: str):
        if number_format not in self.value_numeric_cache:
            self.value_numeric_cache[number_format] = self.workbook.add_format({
                "font_name": FONT_BODY, "font_size": 10, "font_color": TEXT, "valign": "top",
                "align": "left" if number_format in {"@", "General"} else "right",
                "text_wrap": number_format in {"@", "General"},
                "bottom": 1, "bottom_color": BORDER, "indent": 1, "num_format": number_format,
            })
        return self.value_numeric_cache[number_format]


def _title_block(sheet, styles: Styles, title: str, subtitle: str, column_count: int) -> None:
    last_column = max(1, column_count - 1)
    sheet.merge_range(0, 0, 0, last_column, _safe_value(title), styles.title)
    sheet.set_row(0, 38)
    sheet.merge_range(1, 0, 1, last_column, _safe_value(subtitle), styles.subtitle)
    sheet.set_row(1, 24)
    sheet.set_row(2, 4, styles.ribbon)
    sheet.set_row(3, 10)
    sheet.set_row(4, 10)


def _print_setup(sheet, header_row: int | None = None) -> None:
    sheet.set_landscape()
    sheet.set_paper(9)  # A4
    sheet.fit_to_pages(1, 0)
    sheet.set_margins(left=0.4, right=0.4, top=0.6, bottom=0.6)
    sheet.set_header("&L&\"Jost,Bold\"Tejido Empresarial · ProColombia&R&D")
    sheet.set_footer("&L&A&RPágina &P de &N")
    if header_row is not None:
        sheet.repeat_rows(header_row, header_row)
    sheet.hide_gridlines(2)
    sheet.set_tab_color(AMBER)


# ---------------------------------------------------------------------------
# Hojas
# ---------------------------------------------------------------------------
def _write_table(
    workbook: xlsxwriter.Workbook,
    sheet,
    styles: Styles,
    frame: pd.DataFrame,
    title: str,
    subtitle: str,
    freeze_columns: int = 0,
    data_bars: bool = False,
    zoom: int = 90,
) -> tuple[int, int]:
    headers = [str(column) for column in frame.columns]
    _title_block(sheet, styles, title, subtitle, len(headers))
    header_row = 5
    sheet.write_row(header_row, 0, headers, styles.header)
    sheet.set_row(header_row, 48)
    number_formats = [_number_format(header) for header in headers]
    wrapped = [any(term in header for term in LONG_TEXT_TERMS) for header in headers]

    for row_offset, row in enumerate(frame.itertuples(index=False, name=None), start=1):
        sheet_row = header_row + row_offset
        alternate = row_offset % 2 == 0
        for column_index, raw_value in enumerate(row):
            header = headers[column_index]
            value = _excel_value(header, raw_value)
            cell_format = styles.body(number_formats[column_index], wrapped[column_index], alternate)
            if value is None:
                sheet.write_blank(sheet_row, column_index, None, cell_format)
            else:
                sheet.write(sheet_row, column_index, value, cell_format)

    sample_rows = frame.iloc[:300] if not frame.empty else frame
    for column_index, header in enumerate(headers):
        sample = sample_rows.iloc[:, column_index].tolist() if not frame.empty else []
        sheet.set_column(column_index, column_index, _preferred_width(header, sample))

    last_row = header_row + max(0, len(frame))
    if headers:
        sheet.autofilter(header_row, 0, last_row, len(headers) - 1)
        if last_row > header_row:
            for column_index, header in enumerate(headers):
                if header.startswith(YES_NO_COLUMNS):
                    sheet.conditional_format(header_row + 1, column_index, last_row, column_index, {"type": "cell", "criteria": "==", "value": '"Sí"', "format": styles.yes})
                    sheet.conditional_format(header_row + 1, column_index, last_row, column_index, {"type": "cell", "criteria": "==", "value": '"No"', "format": styles.no})
                if data_bars and "FOB USD" in header:
                    sheet.conditional_format(header_row + 1, column_index, last_row, column_index, {"type": "data_bar", "bar_color": "#FFD27A", "bar_border_color": AMBER, "bar_solid": False, "min_type": "num", "min_value": 0})
    sheet.freeze_panes(header_row + 1, freeze_columns)
    sheet.set_zoom(zoom)
    _print_setup(sheet, header_row)
    return header_row, last_row


def _summary_sheet(workbook: xlsxwriter.Workbook, styles: Styles, request: SearchRequest, total: int, exported: int, columns: int, has_profile: bool, generated: datetime) -> None:
    sheet = workbook.add_worksheet("Resumen")
    _title_block(sheet, styles, "Tejido Empresarial · ProColombia", "Resultado de consulta · ejes de Exportaciones, Inversión y Turismo", 6)

    rows: list[tuple[str, Any]] = [
        ("Tipo de consulta", MODE_LABELS[request.mode]),
        ("Criterio", request.summary()),
        ("Fecha y hora de generación", generated.strftime("%d/%m/%Y %H:%M")),
        ("Empresas encontradas", total),
        ("Empresas incluidas en este archivo", exported),
        ("Variables por empresa", columns),
    ]
    if request.mode == "batch_nits":
        rows.append(("NIT válidos consultados", len(request.nits)))
    for key, values in request.filters.items():
        if values and key in FILTERS_BY_KEY:
            rows.append((FILTERS_BY_KEY[key]["label"], "; ".join(values)))

    row = 5
    sheet.write(row, 0, "CONSULTA", styles.kicker)
    row += 1
    for label, value in rows:
        sheet.write(row, 0, label, styles.label)
        sheet.merge_range(row, 1, row, 5, _safe_value(value), styles.value)
        sheet.set_row(row, 24 if len(str(value)) < 70 else 40)
        row += 1

    row += 1
    sheet.write(row, 0, "CORTES DE INFORMACIÓN Y FUENTES", styles.kicker)
    row += 1
    for source in DATA_SOURCES:
        sheet.write(row, 0, source["name"], styles.label)
        sheet.merge_range(row, 1, row, 5, f"{source['detail']} · {source['cut']}", styles.value)
        sheet.set_row(row, 22)
        row += 1

    row += 1
    sheet.write(row, 0, "CONTENIDO DEL LIBRO", styles.kicker)
    row += 1
    guide = [
        ("Resumen", "Esta hoja: qué se consultó, con qué criterios, cortes y fuentes."),
    ]
    if has_profile:
        guide.append(("Ficha_Empresa", "Lectura vertical de la empresa encontrada, agrupada por secciones."))
    guide.extend([
        ("Vista_Principal", f"{len(PREVIEW_COLUMNS)} variables de lectura rápida por empresa. Ideal para revisar y compartir."),
        ("Datos_Completos", "Todas las variables entregadas por la consulta, con filtros y paneles congelados."),
        ("Diccionario", "Definición, fuente y uso de cada variable, según el glosario institucional."),
    ])
    for name, detail in guide:
        sheet.write(row, 0, name, styles.label)
        sheet.merge_range(row, 1, row, 5, detail, styles.value)
        sheet.set_row(row, 22)
        row += 1

    row += 1
    note = (
        "Cómo leer este archivo: los identificadores (NIT, códigos) están guardados como texto para conservar ceros iniciales; "
        "los montos en COP no tienen decimales y los valores FOB USD tienen dos. Las columnas «Sí/No» se resaltan en verde cuando "
        "el valor es «Sí». Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y no representan "
        "el total nacional. Los datos de contacto son de uso interno institucional."
    )
    sheet.merge_range(row, 0, row + 3, 5, note, styles.note)
    row += 5
    sheet.write(row, 0, f"Generado por el Aplicativo de Tejido Empresarial · versión {APP_VERSION} · Gerencia de Inteligencia Comercial · ProColombia", styles.muted)

    sheet.set_column(0, 0, 36)
    sheet.set_column(1, 5, 19)
    sheet.set_zoom(100)
    _print_setup(sheet)


def _profile_sheet(workbook: xlsxwriter.Workbook, styles: Styles, frame: pd.DataFrame) -> None:
    sheet = workbook.add_worksheet("Ficha_Empresa")
    record = frame.iloc[0].to_dict()
    _title_block(
        sheet,
        styles,
        str(record.get("Razón social") or "Ficha de empresa"),
        f"NIT {_excel_value('NIT', record.get('NIT')) or '—'} · {record.get('Municipio de la empresa') or ''}, {record.get('Departamento de la empresa') or ''} · lectura vertical por secciones",
        4,
    )
    placed: set[str] = set()
    row = 5
    sections = [*COLUMN_SECTIONS]
    leftovers = [column for column in frame.columns if not any(column in cols for _, cols in COLUMN_SECTIONS)]
    if leftovers:
        sections.append(("Otras variables", leftovers))
    for section, fields in sections:
        present = [field for field in fields if field in record and field not in placed]
        if not present:
            continue
        sheet.merge_range(row, 0, row, 3, section, styles.section)
        sheet.set_row(row, 24)
        row += 1
        for field in present:
            placed.add(field)
            value = _excel_value(field, record.get(field))
            sheet.write(row, 0, field, styles.label)
            cell_format = styles.value_numeric(_number_format(field))
            if value is None:
                sheet.merge_range(row, 1, row, 3, "—", styles.muted)
            else:
                sheet.merge_range(row, 1, row, 3, value, cell_format)
            sheet.set_row(row, 30 if len(str(value or "")) > 60 else 22)
            row += 1
        row += 1
    sheet.set_column(0, 0, 44)
    sheet.set_column(1, 3, 26)
    sheet.freeze_panes(5, 0)
    sheet.set_zoom(100)
    _print_setup(sheet)


def _glossary_sheet(workbook: xlsxwriter.Workbook, styles: Styles, entries: list[dict[str, Any]], columns: list[str]) -> None:
    by_variable = {entry["variable"]: entry for entry in entries}
    rows: list[dict[str, str]] = []
    defined = 0
    for column in columns:
        entry = by_variable.get(column)
        uses: list[str] = ["Descarga"]
        if column in PREVIEW_COLUMNS:
            uses.insert(0, "Vista previa")
        if entry and entry.get("filter_label"):
            uses.insert(0, "Filtro")
        if entry:
            defined += 1
            rows.append({
                "Variable": column,
                "Sección": entry.get("category", ""),
                "Descripción": str(entry["description"]),
                "Fuentes": str(entry["sources"]),
                "Uso en el aplicativo": " · ".join(uses),
                "Estado": "Definición validada en el glosario institucional" if entry.get("origin", "glosario") == "glosario" else "Definición complementaria del aplicativo (rango derivado)",
            })
        else:
            rows.append({
                "Variable": column,
                "Sección": "Otras variables",
                "Descripción": "Definición no incluida en el glosario institucional vigente. Requiere validación del equipo de negocio y datos.",
                "Fuentes": "Pendiente de validación",
                "Uso en el aplicativo": " · ".join(uses),
                "Estado": "Pendiente de definición",
            })
    frame = pd.DataFrame(rows, columns=["Variable", "Sección", "Descripción", "Fuentes", "Uso en el aplicativo", "Estado"])
    sheet = workbook.add_worksheet("Diccionario")
    header_row, last_row = _write_table(
        workbook, sheet, styles, frame,
        "Diccionario de variables",
        f"{defined} de {len(columns)} columnas cuentan con definición validada en el glosario institucional ({PERIODS['glossary']})",
        freeze_columns=1, zoom=100,
    )
    sheet.set_column(0, 0, 40)
    sheet.set_column(1, 1, 26)
    sheet.set_column(2, 2, 72)
    sheet.set_column(3, 3, 46)
    sheet.set_column(4, 4, 26)
    sheet.set_column(5, 5, 34)
    if last_row > header_row:
        sheet.conditional_format(header_row + 1, 5, last_row, 5, {"type": "text", "criteria": "containing", "value": "Pendiente", "format": styles.pending})
        sheet.conditional_format(header_row + 1, 5, last_row, 5, {"type": "text", "criteria": "containing", "value": "validada", "format": styles.validated})


def create_export(
    frame: pd.DataFrame,
    request: SearchRequest,
    total: int,
    glossary: list[dict[str, Any]],
    generated: datetime | None = None,
) -> BytesIO:
    """Construye el libro completo en memoria y devuelve el buffer listo para enviar."""
    generated = generated or datetime.now()
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {
        "constant_memory": True,
        "strings_to_formulas": False,
        "strings_to_urls": False,
        "nan_inf_to_errors": True,
        "default_date_format": "dd/mm/yyyy",
    })
    workbook.set_properties({
        "title": "Tejido Empresarial · ProColombia",
        "subject": f"{MODE_LABELS[request.mode]} · {request.summary()}",
        "author": "ProColombia · Gerencia de Inteligencia Comercial",
        "company": "ProColombia",
        "category": "Tejido empresarial",
        "keywords": "ProColombia, tejido empresarial, exportaciones, inversión, turismo",
        "comments": f"Generado por el Aplicativo de Tejido Empresarial v{APP_VERSION}.",
    })
    styles = Styles(workbook)
    has_profile = len(frame) == 1
    _summary_sheet(workbook, styles, request, total, len(frame), len(frame.columns), has_profile, generated)
    if has_profile:
        _profile_sheet(workbook, styles, frame)

    principal = frame[[column for column in PREVIEW_COLUMNS if column in frame.columns]].copy()
    _write_table(
        workbook, workbook.add_worksheet("Vista_Principal"), styles, principal,
        "Vista principal",
        f"{len(frame):,} empresa(s) · {len(principal.columns)} variables de lectura rápida · ordenadas por ingresos operacionales".replace(",", "."),
        freeze_columns=2, data_bars=True,
    )
    _write_table(
        workbook, workbook.add_worksheet("Datos_Completos"), styles, frame,
        "Datos completos",
        f"{len(frame):,} empresa(s) · {len(frame.columns)} variables · {MODE_LABELS[request.mode]}".replace(",", "."),
        freeze_columns=3, zoom=85,
    )
    _glossary_sheet(workbook, styles, glossary, list(frame.columns))
    workbook.close()
    output.seek(0)
    return output


__all__ = ["create_export", "filename_for", "EXPORT_VALUE_COLUMNS"]
