"""
Configuración central del aplicativo Tejido Empresarial (API).

Este archivo es el ÚNICO lugar que debe editarse cuando llega un nuevo corte
de información. Sigue la misma convención del aplicativo Streamlit original
(`legado_streamlit/src/pages_utils/config.py`):

1. PASO 1 · Periodos disponibles: ajustar las tuplas de años/corridos.
2. PASO 2 · Columnas de exportaciones: reemplazar el corrido anterior por el
   nuevo o, al cerrar el año, eliminar el corrido y agregar el año cerrado.
3. Nada más. Etiquetas de filtros, metadatos, glosario y Excel se derivan de
   estos parámetros automáticamente.
"""
from __future__ import annotations

from collections import OrderedDict

APP_VERSION = "3.3.0"
APP_TITLE = "Tejido Empresarial · ProColombia"

# ==============================================================================
# PASO 1 · PERIODOS DISPONIBLES
# ==============================================================================
# Formato del corrido: "Enero YYYY", "Enero a Febrero YYYY", ... "Enero a Mayo YYYY".
# Cuando el año esté cerrado, reemplazar el corrido por el año completo: (2021, 2026).
EXPORTACIONES_ANIOS_DISPONIBLES: tuple[int | str, int | str] = (2021, "Enero a Mayo 2026")
RUES_CORTE = "30 de junio de 2026"
SUPERSOCIEDADES_ANIO = 2025
GLOSARIO_FECHA = "2026-09-01"

# ==============================================================================
# PASO 2 · COLUMNAS DE EXPORTACIONES (FOB USD)
# ==============================================================================
# Cuando llegue un nuevo mes: REEMPLAZAR la entrada del corrido anterior por la nueva.
#   Ejemplo: 'EXPO_ENE_MAY_2026' → 'EXPO_ENE_JUN_2026' con alias
#            'Exportaciones totales de la empresa Enero - Junio 2026 (FOB USD)'.
# Cuando el año cierre: ELIMINAR la entrada del corrido y agregar el año cerrado
#   'EXPO_2026': 'Exportaciones totales de la empresa 2026 (FOB USD)'.
# Los alias deben coincidir con los nombres del glosario para que el Excel los documente.
EXPORT_VALUE_COLUMNS = OrderedDict([
    ("EXPO_2021", "Exportaciones totales de la empresa 2021 (FOB USD)"),
    ("EXPO_2022", "Exportaciones totales de la empresa 2022 (FOB USD)"),
    ("EXPO_2023", "Exportaciones totales de la empresa 2023 (FOB USD)"),
    ("EXPO_2024", "Exportaciones totales de la empresa 2024 (FOB USD)"),
    ("EXPO_2025", "Exportaciones totales de la empresa 2025 (FOB USD)"),
    ("EXPO_ENE_MAY_2025", "Exportaciones totales de la empresa Enero - Mayo 2025 (FOB USD)"),
    ("EXPO_ENE_MAY_2026", "Exportaciones totales de la empresa Enero - Mayo 2026 (FOB USD)"),  # <-- REEMPLAZAR cuando haya nuevo mes
])

# Las dos columnas de exportación más recientes (año cerrado y corrido) se usan en la vista previa.
LATEST_CLOSED_EXPORT_COLUMN = "Exportaciones totales de la empresa 2025 (FOB USD)"
LATEST_RUNNING_EXPORT_COLUMN = list(EXPORT_VALUE_COLUMNS.values())[-1]

PERIODO_EXPORTACIONES = f"{EXPORTACIONES_ANIOS_DISPONIBLES[0]} - {EXPORTACIONES_ANIOS_DISPONIBLES[1]}"

# ==============================================================================
# FILTROS
# ==============================================================================
# `key`            : nombre en la tabla de filtros precalculada (FILTROS_*).
# `query_column`   : columna real en la tabla de empresas (alias A) o de bienes (alias B).
# `label`          : etiqueta que ve el usuario.
# `group`          : agrupación visual en el panel de filtros.
# `help`           : nota metodológica (tomada del aplicativo original) mostrada como ayuda.
GENERAL_FILTERS: list[dict[str, str]] = [
    {"key": "DEPARTAMENTO", "query_column": "DEPARTAMENTO_EMP", "label": "Departamento de la sede principal", "group": "Ubicación",
     "help": "Departamento donde está registrada la sede principal (HQ) de la empresa."},
    {"key": "MUNICIPIO", "query_column": "MUNICIPIO_EMP", "label": "Municipio de la sede principal", "group": "Ubicación",
     "help": "Municipio donde está registrada la sede principal (HQ) de la empresa."},
    {"key": "TAMANO", "query_column": "TAMANO", "label": "Tamaño de la empresa", "group": "Perfil empresarial",
     "help": "Tamaño según Decreto 957 de 2019 (Supersociedades para las 10.000 más grandes; RUES para el resto)."},
    {"key": "RANGO_ANTIGUEDAD", "query_column": "RANGO_ANTIGUEDAD", "label": "Antigüedad de la empresa (años)", "group": "Perfil empresarial",
     "help": "Rango de años desde la constitución de la empresa a la fecha de corte."},
    {"key": "RANGO_INGRESOS", "query_column": "RANGO_INGRESOS", "label": "Ingresos operacionales (COP)", "group": "Perfil empresarial",
     "help": "Rango de ingresos por la actividad ordinaria de la empresa, en pesos colombianos."},
    {"key": "INVERSION_EXTRANJERA", "query_column": "INVERSION_EXTRANJERA", "label": "Inversión extranjera", "group": "Perfil empresarial",
     "help": "Indica «Sí» cuando la empresa está identificada como sucursal de sociedad extranjera o cuando reporta un porcentaje de capital social extranjero."},
    {"key": "COD_CIIU_1", "query_column": "COD_CIIU_1", "label": "Código CIIU Rev. 4 · Actividad principal", "group": "Actividad económica",
     "help": "Código CIIU Revisión 4 de la principal actividad económica de la empresa."},
    {"key": "DESCRIPCION_CIIU_1", "query_column": "DESCRIPCION_CIIU_1", "label": "Descripción CIIU Rev. 4 · Actividad principal", "group": "Actividad económica",
     "help": "Descripción del CIIU principal."},
    {"key": "CADENA_CIIU_1", "query_column": "CADENA_CIIU_1", "label": "Cadena CIIU Rev. 4 · Actividad principal", "group": "Actividad económica",
     "help": "Cadena ProColombia correspondiente al CIIU principal. La correlativa fue construida por la Gerencia de Inteligencia Comercial y la Vicepresidencia de Exportaciones."},
    {"key": "VALOR_AGREGADO_CIIU_1", "query_column": "VALOR_AGREGADO_CIIU_1", "label": "Valor agregado · Actividad principal", "group": "Actividad económica",
     "help": "Intensidad tecnológica (bienes) o intensidad en conocimiento (servicios) de la actividad principal."},
    {"key": "CADENA_SEGMENTACION", "query_column": "CADENA_SEGMENTACION", "label": "Cadena de segmentación", "group": "Perfil exportador",
     "help": "Para exportadoras: cadena que más ha exportado la empresa en los últimos 5 años. Para no exportadoras: cadena asociada al CIIU principal."},
    {"key": "TRAYECTORIA_EXPORTADORA", "query_column": "TRAYECTORIA_EXPORTADORA", "label": "Trayectoria exportadora", "group": "Perfil exportador",
     "help": "Top Exportadora, PYMEX, No constantes, Futuros exportadores o Mineras, chatarra, otros (ver glosario)."},
    {"key": "HA_EXPORTADO", "query_column": "HA_EXPORTADO", "label": f"¿La empresa ha exportado? ({PERIODO_EXPORTACIONES})", "group": "Perfil exportador",
     "help": "«Sí» cuando la empresa exportó al menos una vez en los últimos 5 años y lo corrido del año, sin importar el monto."},
]

EXPORT_FILTERS: list[dict[str, str]] = [
    {"key": "SECTOR", "query_column": "SECTOR", "label": "Sector exportado", "group": "Exportaciones de bienes",
     "help": f"Sector de los bienes exportados por la empresa entre {PERIODO_EXPORTACIONES}."},
    {"key": "SUBSECTOR", "query_column": "SUBSECTOR", "label": "Subsector exportado", "group": "Exportaciones de bienes",
     "help": f"Subsector de los bienes exportados por la empresa entre {PERIODO_EXPORTACIONES}."},
    {"key": "COD_POSICION_ARANCELARIA", "query_column": "COD_POSICION_ARANCELARIA", "label": "Código de posición arancelaria", "group": "Exportaciones de bienes",
     "help": "Posición arancelaria a 10 dígitos de los bienes exportados."},
    {"key": "DESC_POSICION_ARANCELARIA", "query_column": "DESC_POSICION_ARANCELARIA", "label": "Descripción de posición arancelaria", "group": "Exportaciones de bienes",
     "help": "Descripción de la posición arancelaria a 10 dígitos."},
    {"key": "HUB", "query_column": "HUB", "label": "HUB de destino", "group": "Mercados de destino",
     "help": "Agrupación regional de destino definida por ProColombia."},
    {"key": "PAIS_DESTINO", "query_column": "PAIS_DESTINO", "label": "País de destino", "group": "Mercados de destino",
     "help": "País hacia donde la empresa ha exportado bienes."},
]

FILTER_GROUP_ORDER = [
    "Ubicación",
    "Perfil empresarial",
    "Actividad económica",
    "Perfil exportador",
    "Exportaciones de bienes",
    "Mercados de destino",
]

FILTERS_BY_KEY = {item["key"]: item for item in [*GENERAL_FILTERS, *EXPORT_FILTERS]}
GENERAL_FILTER_KEYS = {item["key"] for item in GENERAL_FILTERS}
EXPORT_FILTER_KEYS = {item["key"] for item in EXPORT_FILTERS}

# ==============================================================================
# COLUMNAS DE LA CONSULTA (idénticas al aplicativo original)
# ==============================================================================
QUERY_COLUMNS: "OrderedDict[str, str]" = OrderedDict([
    ("NIT", "NIT"),
    ("DIGITO_VERIFICACION", "Dígito de verificación"),
    ("RAZON_SOCIAL", "Razón social"),
    ("TAMANO", "Tamaño de la empresa"),
    ("MACRORREGION_EMP", "Macrorregión de la empresa"),
    ("COD_DEPARTAMENTO_EMP", "Código del departamento de la empresa"),
    ("DEPARTAMENTO_EMP", "Departamento de la empresa"),
    ("COD_MUNICIPIO_EMP", "Código del municipio de la empresa"),
    ("MUNICIPIO_EMP", "Municipio de la empresa"),
    ("COD_CIIU_1", "Código CIIU Rev 4 - Actividad principal"),
    ("DESCRIPCION_CIIU_1", "Descripción CIIU Rev 4 - Actividad principal"),
    ("CADENA_CIIU_1", "Cadena CIIU Rev 4 - Actividad principal"),
    ("VALOR_AGREGADO_CIIU_1", "Valor Agregado - Actividad principal"),
    ("CIIU_2", "Código CIIU Rev 4 - Actividad 2"),
    ("DESCRIPCION_CIIU_2", "Descripción CIIU Rev 4 - Actividad 2"),
    ("CADENA_CIIU_2", "Cadena CIIU Rev 4 - Actividad 2"),
    ("CIIU_3", "Código CIIU Rev 4 - Actividad 3"),
    ("DESCRIPCION_CIIU_3", "Descripción CIIU Rev 4 - Actividad 3"),
    ("CADENA_CIIU_3", "Cadena CIIU Rev 4 - Actividad 3"),
    ("CIIU_4", "Código CIIU Rev 4 - Actividad 4"),
    ("DESCRIPCION_CIIU_4", "Descripción CIIU Rev 4 - Actividad 4"),
    ("CADENA_CIIU_4", "Cadena CIIU Rev 4 - Actividad 4"),
    ("RANGO_ANTIGUEDAD", "Rango de antigüedad de la empresa (años)"),
    ("ANOS_EMPRESA", "Antigüedad de la empresa (años)"),
    ("INVERSION_EXTRANJERA", "Inversión extranjera"),
    ("ACTIVOS", "Activos (COP)"),
    ("RANGO_INGRESOS", "Rango de ingresos operacionales (COP)"),
    ("INGRESOS_OPERACIONALES", "Ingresos operacionales (COP)"),
    ("UTILIDAD", "Utilidad (COP)"),
    ("EMPLEADOS", "Empleados"),
    ("CANTIDAD_MUJERES_EMPLEADAS", "Cantidad de mujeres empleadas"),
    ("CANTIDAD_MUJERES_EN_CARGOS_DIRECTIVOS", "Cantidad de mujeres en cargos directivos"),
    ("CANTIDAD_ESTABLECIMIENTOS", "Cantidad de establecimientos"),
    ("DIRECCION", "Dirección"),
    ("TELEFONO", "Teléfono"),
    ("EMAIL", "Correo electrónico"),
    ("ID_REPRESENTANTE_LEGAL", "ID del representante legal"),
    ("REPRESENTANTE_LEGAL", "Representante legal"),
    ("ORGANIZACION_JURIDICA", "Organización jurídica"),
    ("CATEGORIA_MATRICULA", "Categoría de matrícula"),
    ("TIPO", "Tipo estrella"),
    ("CADENA", "Cadena estrella"),
    ("SECTOR", "Sector estrella"),
    ("SUBSECTOR", "Subsector estrella"),
    ("COD_POSICION_ARANCELARIA", "Código de posición arancelaria estrella"),
    ("DESC_POSICION_ARANCELARIA", "Descripción de posición arancelaria estrella"),
    ("VALOR_AGREGADO_EXPO", "Valor agregado exportaciones estrella"),
    ("COD_DEPARTAMENTO_EXPO", "Código de departamento exportaciones estrella"),
    ("DEPARTAMENTO_EXPO", "Departamento exportaciones estrella"),
    ("PAIS_DESTINO", "País destino estrella"),
    ("HUB", "HUB estrella"),
    ("TRAYECTORIA_EXPORTADORA", "Trayectoria exportadora"),
    ("HA_EXPORTADO", "¿La empresa ha exportado?"),
    *EXPORT_VALUE_COLUMNS.items(),
    ("EXPORTADORA_NME_ACTIVIDAD", "Empresa exportadora NME según actividad económica"),
    ("CADENA_SEGMENTACION", "Cadena de segmentación"),
    ("FUENTES", "Fuentes"),
])

# Columnas de lectura rápida (vista previa en pantalla y hoja Vista_Principal del Excel).
PREVIEW_COLUMNS = [
    "NIT",
    "Razón social",
    "Tamaño de la empresa",
    "Departamento de la empresa",
    "Municipio de la empresa",
    "Código CIIU Rev 4 - Actividad principal",
    "Descripción CIIU Rev 4 - Actividad principal",
    "Cadena de segmentación",
    "Trayectoria exportadora",
    "¿La empresa ha exportado?",
    "Inversión extranjera",
    "Ingresos operacionales (COP)",
    "Empleados",
    LATEST_CLOSED_EXPORT_COLUMN,
    LATEST_RUNNING_EXPORT_COLUMN,
]

# Columnas de contacto. Se incluyen en la descarga como en el aplicativo original;
# pueden excluirse con EXPORT_INCLUDE_CONTACT_FIELDS=false.
CONTACT_COLUMNS = ["Dirección", "Teléfono", "Correo electrónico", "ID del representante legal", "Representante legal"]

# Secciones para la ficha de empresa (pantalla y hoja Ficha_Empresa del Excel).
# Toda columna no listada aquí se muestra en la sección «Otras variables».
COLUMN_SECTIONS: list[tuple[str, list[str]]] = [
    ("Identificación y ubicación", [
        "NIT", "Dígito de verificación", "Razón social", "Tamaño de la empresa", "Organización jurídica", "Categoría de matrícula",
        "Macrorregión de la empresa", "Código del departamento de la empresa", "Departamento de la empresa",
        "Código del municipio de la empresa", "Municipio de la empresa",
    ]),
    ("Actividad económica", [
        "Código CIIU Rev 4 - Actividad principal", "Descripción CIIU Rev 4 - Actividad principal", "Cadena CIIU Rev 4 - Actividad principal",
        "Valor Agregado - Actividad principal", "Cadena de segmentación", "Empresa exportadora NME según actividad económica",
        "Código CIIU Rev 4 - Actividad 2", "Descripción CIIU Rev 4 - Actividad 2", "Cadena CIIU Rev 4 - Actividad 2",
        "Código CIIU Rev 4 - Actividad 3", "Descripción CIIU Rev 4 - Actividad 3", "Cadena CIIU Rev 4 - Actividad 3",
        "Código CIIU Rev 4 - Actividad 4", "Descripción CIIU Rev 4 - Actividad 4", "Cadena CIIU Rev 4 - Actividad 4",
    ]),
    ("Finanzas, antigüedad y empleo", [
        "Rango de antigüedad de la empresa (años)", "Antigüedad de la empresa (años)", "Inversión extranjera",
        "Activos (COP)", "Rango de ingresos operacionales (COP)", "Ingresos operacionales (COP)", "Utilidad (COP)",
        "Empleados", "Cantidad de mujeres empleadas", "Cantidad de mujeres en cargos directivos", "Cantidad de establecimientos",
    ]),
    ("Perfil exportador", [
        "Trayectoria exportadora", "¿La empresa ha exportado?", "Tipo estrella", "Cadena estrella", "Sector estrella", "Subsector estrella",
        "Código de posición arancelaria estrella", "Descripción de posición arancelaria estrella", "Valor agregado exportaciones estrella",
        "Código de departamento exportaciones estrella", "Departamento exportaciones estrella", "País destino estrella", "HUB estrella",
    ]),
    ("Exportaciones por periodo (FOB USD)", list(EXPORT_VALUE_COLUMNS.values())),
    ("Contacto y representación", CONTACT_COLUMNS),
    ("Trazabilidad", ["Fuentes"]),
]

DATA_SOURCES = [
    {"name": "RUES", "detail": "Registro Único Empresarial y Social", "cut": f"corte {RUES_CORTE}"},
    {"name": "Supersociedades", "detail": f"Las 10.000 empresas más grandes de Colombia", "cut": str(SUPERSOCIEDADES_ANIO)},
    {"name": "DANE – DIAN", "detail": "Exportaciones de bienes", "cut": PERIODO_EXPORTACIONES},
    {"name": "CRM ProColombia", "detail": "Negocios de Industrias 4.0 y relación institucional", "cut": PERIODO_EXPORTACIONES},
]

PERIODS = {
    "companies": f"RUES · corte {RUES_CORTE}",
    "exports": f"Exportaciones · {PERIODO_EXPORTACIONES}",
    "supersociedades": f"Supersociedades · {SUPERSOCIEDADES_ANIO}",
    "glossary": GLOSARIO_FECHA,
}

# Notas metodológicas que acompañan a la consulta (tomadas del aplicativo original).
METHOD_NOTES = [
    "Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.",
    "Cadena de segmentación: para las empresas exportadoras corresponde a la cadena que más ha exportado la empresa en los últimos 5 años; para las no exportadoras, a la cadena asociada al CIIU principal.",
    "Inversión extranjera: indica «Sí» cuando la empresa está identificada como sucursal de sociedad extranjera o cuando reporta un porcentaje de capital social extranjero.",
]

# ==============================================================================
# TABLAS DE SNOWFLAKE
# ==============================================================================
GENERAL_FILTER_TABLE = "APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_GENERALES_TEJIDO_EMPRESARIAL_COMPLETO"
EXPORT_FILTER_TABLE = "APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_EXPORTADORAS"
COMPANY_TABLE = "APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P"
EXPORT_TABLE = "APP_SEGMENTACION_EXPORTACIONES.PUBLIC.BIENES_Y_SERVICIOS_P"
EVENT_TABLE = "APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO.EVENTOS"
