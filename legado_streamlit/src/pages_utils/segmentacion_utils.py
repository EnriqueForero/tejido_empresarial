# Librerías
import streamlit as st
from src.pages_utils.utils import read_file_content

# ==================== PARÁMETROS PARA PÁGINA SEGMENTACIÓN ===================

from .config import (
    exportaciones_anios_disponibles,
    servicios_anios_disponibles,
    negocios_anios_disponibles,
    exportaciones_bienes_servicios_anios_disponibles,
    COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_EXPORTACIONES,
    COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_PC
)

# ==================== LISTA DE COLUMNAS Y DICCIONARIO DE NOMBRES PARA FILTROS ===================

ls_filtros_generales_empresas = [
                                 'DEPARTAMENTO',
                                 'MUNICIPIO',
                                 'TAMANO',
                                 'CADENA_SEGMENTACION',
                                 'TRAYECTORIA_EXPORTADORA',
                                 'INVERSION_EXTRANJERA',
                                 'COD_CIIU_1',
                                 'DESCRIPCION_CIIU_1',
                                 'VALOR_AGREGADO_CIIU_1',
                                 'CADENA_CIIU_1',
                                 'RANGO_ANTIGUEDAD',
                                 'RANGO_INGRESOS',
                                 'HA_EXPORTADO']

dict_filtros_generales_empresas = {'DEPARTAMENTO' : 'Departamento de la ubicación del HQ',
                                 'MUNICIPIO' : 'Municipio de la ubicación del HQ',
                                 'TAMANO' : 'Tamaño empresa',
                                 'CADENA_SEGMENTACION' : 'Cadena de segmentación',
                                 'TRAYECTORIA_EXPORTADORA' : 'Trayectoria exportadora',
                                 'INVERSION_EXTRANJERA' : 'Inversión extranjera',
                                 'COD_CIIU_1' : 'Código CIIU Rev 4 - Actividad principal',
                                 'DESCRIPCION_CIIU_1' : 'Descripción CIIU Rev 4 - Actividad principal',
                                 'VALOR_AGREGADO_CIIU_1' : 'Valor Agregado - Actividad principal',
                                 'CADENA_CIIU_1' : 'Cadena CIIU Rev 4 - Actividad principal',
                                 'RANGO_ANTIGUEDAD' : 'Antiguedad de la empresa (años)', 
                                 'RANGO_INGRESOS' : 'Ingreso operacional (COP)',
                                 'HA_EXPORTADO' : f'¿La empresa ha exportado {exportaciones_anios_disponibles[0]} - {exportaciones_anios_disponibles[1]}?'}

ls_filtros_exportadoras = ['SECTOR',
                           'SUBSECTOR',
                           'COD_POSICION_ARANCELARIA',
                           'DESC_POSICION_ARANCELARIA',
                           'HUB',
                           'PAIS_DESTINO']

dict_filtros_exportadoras = {'SECTOR' : f'Sector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                           'SUBSECTOR' : f'Subsector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                           'COD_POSICION_ARANCELARIA' : f'Código de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                           'DESC_POSICION_ARANCELARIA' : f'Descripción de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                           'HUB' : f'HUB de destino {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                           'PAIS_DESTINO' : f'País de destino {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}'}

# ==================== DICCIONARIO DE COLUMNAS PARA LA CONSULTA DE RESULTADOS ===================

dict_query_segmentacion = ({
                           # Columnas tejido
                           'NIT' : 'NIT', 
                           'DIGITO_VERIFICACION' : 'Dígito de verificación', 
                           'RAZON_SOCIAL' : 'Razón social', 
                           'TAMANO' : 'Tamaño de la empresa',
                           'MACRORREGION_EMP' : 'Macrorregión de la empresa', 
                           'COD_DEPARTAMENTO_EMP' : 'Código del departamento de la empresa', 
                           'DEPARTAMENTO_EMP' : 'Departamento de la empresa',
                           'COD_MUNICIPIO_EMP' : 'Código del municipio de la empresa', 
                           'MUNICIPIO_EMP' : 'Municipio de la empresa', 
                           'COD_CIIU_1' : 'Código CIIU Rev 4 - Actividad principal',
                           'DESCRIPCION_CIIU_1' : 'Descripción CIIU Rev 4 - Actividad principal', 
                           'CADENA_CIIU_1' : 'Cadena CIIU Rev 4 - Actividad principal', 
                           'VALOR_AGREGADO_CIIU_1' : 'Valor Agregado - Actividad principal',
                           'CIIU_2' : 'Código CIIU Rev 4 - Actividad 2', 
                           'DESCRIPCION_CIIU_2' : 'Descripción CIIU Rev 4 - Actividad 2', 
                           'CADENA_CIIU_2' : 'Cadena CIIU Rev 4 - Actividad 2', 
                           'CIIU_3' : 'Código CIIU Rev 4 - Actividad 3',
                           'DESCRIPCION_CIIU_3' : 'Descripción CIIU Rev 4 - Actividad 3', 
                           'CADENA_CIIU_3' : 'Cadena CIIU Rev 4 - Actividad 3', 
                           'CIIU_4' : 'Código CIIU Rev 4 - Actividad 4',
                           'DESCRIPCION_CIIU_4' : 'Descripción CIIU Rev 4 - Actividad 4',
                           'CADENA_CIIU_4' : 'Cadena CIIU Rev 4 - Actividad 4', 
                           'RANGO_ANTIGUEDAD' : 'Rango de antigüedad de la empresa (años)',
                           'ANOS_EMPRESA' : 'Antigüedad de la empresa (años)', 
                           'INVERSION_EXTRANJERA' : 'Inversión extranjera', 
                           'ACTIVOS' : 'Activos (COP)',
                           'RANGO_INGRESOS' : 'Rango de ingresos operacionales (COP)',
                           'INGRESOS_OPERACIONALES' : 'Ingresos operacionales (COP)', 
                           'UTILIDAD' : 'Utilidad (COP)', 
                           'EMPLEADOS' : 'Empleados',
                           'CANTIDAD_MUJERES_EMPLEADAS' : 'Cantidad de mujeres empleadas', 
                           'CANTIDAD_MUJERES_EN_CARGOS_DIRECTIVOS' : 'Cantidad de mujeres en cargos directivos',
                           'CANTIDAD_ESTABLECIMIENTOS' : 'Cantidad de establecimientos', 
                           'DIRECCION' : 'Dirección', 
                           'TELEFONO' : 'Teléfono', 
                           'EMAIL' : 'Correo electrónico',
                           'ID_REPRESENTANTE_LEGAL' : 'ID del representante legal', 
                           'REPRESENTANTE_LEGAL' : 'Representante legal',
                           'ORGANIZACION_JURIDICA' : 'Organización jurídica', 
                           'CATEGORIA_MATRICULA' : 'Categoría de matrícula', 
                           'TIPO' : 'Tipo estrella', 
                           'CADENA' : 'Cadena estrella',
                           'SECTOR' : 'Sector estrella', 
                           'SUBSECTOR' : 'Subsector estrella', 
                           'COD_POSICION_ARANCELARIA' : 'Código de posición arancelaria estrella',
                           'DESC_POSICION_ARANCELARIA' : 'Descripción de posición arancelaria estrella', 
                           'VALOR_AGREGADO_EXPO' : 'Valor agregado exportaciones estrella',
                           'COD_DEPARTAMENTO_EXPO' : 'Código de departamento exportaciones estrella',
                           'DEPARTAMENTO_EXPO' : 'Departamento exportaciones estrella',
                           'PAIS_DESTINO' : 'País destino estrella',
                           'HUB' : 'HUB estrella',
                           'TRAYECTORIA_EXPORTADORA' : 'Trayectoria exportadora',
                           'HA_EXPORTADO' : f'¿La empresa ha exportado?' 
                           }
                           # Columnas de exportaciones
                           | COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_EXPORTACIONES
                           # Negocios, servicios y oportunidades
                           # | COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_PC
                           # Columnas tejido
                           | {'EXPORTADORA_NME_ACTIVIDAD' : 'Empresa exportadora NME según actividad económica', 
                           'CADENA_SEGMENTACION' : 'Cadena de segmentación',
                           'FUENTES' : 'Fuentes'
                           #, 
                        #    'POTENCIAL_ATENCION' : 'Potencial de atención', 
                        #    'INDICE_POTENCIAL_ATENCION' : 'Índice de potencial de atención',
                        #    'GEMELA_1' : 'Empresa gemela 1', 
                        #    'DISTANCIA_GEMELA_1' : 'Distancia empresa gemela 1', 
                        #    'GEMELA_2' : 'Empresa gemela 2', 
                        #    'DISTANCIA_GEMELA_2' : 'Distancia empresa gemela 2',
                        #    'GEMELA_3' : 'Empresa gemela 3', 
                        #    'DISTANCIA_GEMELA_3' : 'Distancia empresa gemela 3',
                           # Municipios
                        #    'MENOR_200K_HABITANTES': 'Ubicación del HQ en municipio menor 200k habitantes',
                        #    'PDET': 'Ubicación del HQ en municipio PDET',
                        #    'ZOMAC' : 'Ubicación del HQ en municipio ZOMAC'
                           }
)

# ==================== LISTA DE COLUMNAS PARA MOSTRAR AL USUARIO ===================

# Deben ser iguales a los elementos del AS en el diccionario anterior

ls_columnas_usuario_segmentacion = [
    'NIT',
    'Razón social', 
    'Trayectoria exportadora',
    'Cadena de segmentación',
    'Ingresos operacionales (COP)',
    # Datos de exportaciones
    *list(COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_SEGMENTACION_EXPORTACIONES.values())
]

# ==================== GENERADOR DE CONSULTA ===================

def query_data_segmentacion(
    dict_columnas: dict,
    filtros_generales: dict,
    filtros_emp_export: dict
) -> str:
    """
    Devuelve una consulta SQL dinámica para la vista **Segmentación** en la página de Segmentación.

    El resultado:
    - Selecciona las columnas definidas en ``dict_columnas`` con alias legibles.
    - Aplica filtros sobre la tabla principal **A** mediante ``filtros_generales``.
    - Incluye, solo cuando corresponde, un sub‑query que restringe los NIT
      a los presentes en la tabla **B** usando ``filtros_emp_export``.

    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula
        ``SELECT``.
    filtros_generales : dict
        Mapeo ``{columna_A : [valores]}`` aplicado sobre la tabla
        ``TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P`` (alias **A**).
        Si la lista de valores está vacía, el filtro se omite.
    filtros_emp_export : dict
        Mapeo ``{columna_B : [valores]}`` aplicado sobre la tabla
        ``BIENES_Y_SERVICIOS_P`` (alias **B**).  
        Cuando todas las listas están vacías, el sub‑query sobre **B** no se
        añade y la consulta se ejecuta únicamente sobre la tabla **A**.

    Retorna
    -------
    str
        Cadena con la consulta SQL final.
    """

    # SELECT ------------------------------------------------------------------
    columnas_str = ", ".join(f'{col} AS "{alias}"'
                             for col, alias in dict_columnas.items())

    # WHERE para tabla A ------------------------------------------------------
    condiciones_A = []
    for col, vals in filtros_generales.items():
        if vals:
            inner = ", ".join(f"'{v}'" for v in vals)
            condiciones_A.append(f"A.{col} IN ({inner})")
    filtros_A = " AND ".join(condiciones_A) or "1=1"

    # WHERE para tabla B (opcional) ------------------------------------------
    condiciones_B = []
    for col, vals in filtros_emp_export.items():
        if vals:
            inner = ", ".join(f"'{v}'" for v in vals)
            condiciones_B.append(f"B.{col} IN ({inner})")

    if condiciones_B:
        filtros_B = " AND ".join(condiciones_B)
        subquery_nits = (
            "AND A.NIT IN (\n"
            "    SELECT DISTINCT B.NIT\n"
            "    FROM APP_SEGMENTACION_EXPORTACIONES.PUBLIC.BIENES_Y_SERVICIOS_P AS B\n"
            f"    WHERE {filtros_B}\n"
            ")"
        )
    else:
        subquery_nits = ""

    # QUERY completa ----------------------------------------------------------
    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P AS A\n"
        f"WHERE {filtros_A}\n"
        f"{subquery_nits}"
        #f"ORDER BY A.INDICE_POTENCIAL_ATENCION DESC"
    )

    return query


# ==================== BUSCADOR DE NITS ===================

@st.dialog("Búsqueda por NIT")
def buscar_nits():
    """
    Carga un archivo de NITs, los guarda en st.session_state y marca que debe
    ejecutarse la búsqueda automáticamente al recargarse la app.

    Flujo:
    1. El usuario pulsa el botón «Buscar NITs» → se abre este diálogo.
    2. Sube un archivo .txt con un NIT por línea y pulsa «Filtrar».
    3. La función:
       • Lee los NITs, los limpia y los guarda en st.session_state['NITS']  
       • Establece st.session_state['BUSCAR_NITS'] = True  
       • Llama a st.rerun() para recargar la aplicación.
    4. En el rerun, el script principal detecta BUSCAR_NITS y lanza la consulta.
    """
    # Subir archivo .txt
    file = st.file_uploader(
        "Archivo",
        type="txt",
        label_visibility="collapsed",
        help="Sube un archivo de texto con un NIT por línea."
    )

    # Ejemplo para orientar al usuario si no ha subido nada
    example_text = (
        "901067966\n"
        "760459043\n"
        "890905456\n"
        "860035996\n"
        "900409346\n"
        "860044105"
    )

    if file is not None:
        # Leer y limpiar contenido
        file_content = read_file_content(file)
        nits = [
            nit.strip()
            for nit in file_content.splitlines()
            if 1 < len(nit.strip()) <= 9 and nit.strip().isdigit()
        ]
        nits = set(nits)  # únicos

        # Guardar en estado de sesión
        st.session_state['NITS'] = nits

        # Mostrar pre‑visualización
        st.write(f"Se encontraron :red[{len(nits)}] NIT(s) únicos")
        height = 300 if len(nits) > 15 else None
        with st.container(height=height, border=False):
            st.code("\n".join(sorted(nits)), language="plaintext")

        # Botón que dispara el filtrado
        if st.button("Filtrar", key="filtrar_nits"):
            st.session_state['BUSCAR_NITS'] = True  # <- marca para búsqueda automática
            st.rerun()

    else:
        st.subheader("Ejemplo del formato esperado:")
        st.code(example_text, language="plaintext")


# ==================== CONSULTA POR RAZÓN SOCIAL ===================

def query_data_razon_social(dict_columnas: dict, termino_busqueda: str) -> str:
    """
    Devuelve una consulta SQL que filtra por RAZON_SOCIAL usando LIKE.

    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula SELECT.
    termino_busqueda : str
        Texto a buscar dentro de la columna RAZON_SOCIAL (case-insensitive).

    Retorna
    -------
    str
        Cadena con la consulta SQL final.
    """
    columnas_str = ", ".join(f'{col} AS "{alias}"' for col, alias in dict_columnas.items())
    term_escaped = termino_busqueda.replace("'", "''")  # prevenir inyección SQL

    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P AS A\n"
        f"WHERE UPPER(A.RAZON_SOCIAL) LIKE UPPER('%{term_escaped}%')"
    )
    return query


# ==================== CONSULTA POR NIT INDIVIDUAL ===================

def query_data_nit_individual(dict_columnas: dict, termino_busqueda: str) -> str:
    """
    Devuelve una consulta SQL que filtra por NIT usando LIKE.

    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula SELECT.
    termino_busqueda : str
        Texto a buscar dentro de la columna NIT (búsqueda parcial).

    Retorna
    -------
    str
        Cadena con la consulta SQL final.
    """
    columnas_str = ", ".join(f'{col} AS "{alias}"' for col, alias in dict_columnas.items())
    term_escaped = termino_busqueda.replace("'", "''")  # prevenir inyección SQL

    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P AS A\n"
        f"WHERE CAST(A.NIT AS VARCHAR) LIKE '%{term_escaped}%'"
    )
    return query