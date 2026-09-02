# Librerías
import pandas as pd
import plotly.express as px
from.utils import milify
from snowflake.snowpark.functions import count_distinct, sum as snow_sum, col

# ==================== PARÁMETROS PARA PÁGINA MUNICIPIOS ===================

from .config import (
    COLS_VARIABLES_MUNICIPIOS_EXPORTACIONES
)

# ==================== PARÁMETROS PARA MUNICIPIOS ===================

# VISTA: Exportaciones por municipio

ls_filtros_tejido_municipios = ['DEPARTAMENTO_TEJIDO',
                                'MUNICIPIO_TEJIDO',
                                'PDET',
                                'MENOR_200K_HABITANTES']

dict_filtros_tejido_municipios = {'DEPARTAMENTO_TEJIDO' : 'Departamento de la ubicación del HQ',
                                'MUNICIPIO_TEJIDO' : 'Municipio de la ubicación del HQ',
                                'PDET' : 'Ubicación del HQ en municipio PDET',
                                'MENOR_200K_HABITANTES' : 'Ubicación del HQ en municipio menor 200k habitantes'}

dict_query_tejido_municipios = {'CODIGO_DEPARTAMENTO_TEJIDO' : 'CODIGO_DEPARTAMENTO',
	'DEPARTAMENTO_TEJIDO' : 'DEPARTAMENTO',
	'CODIGO_MUNICIPIO_TEJIDO' : 'CODIGO_MUNICIPIO',
	'MUNICIPIO_TEJIDO' : 'MUNICIPIO',
	'CADENA_SEGMENTACION_TEJIDO' : 'CADENA_SEGMENTACION',
	'CADENA_PRODUCTIVA_TEJIDO' : 'CADENA_PRODUCTIVA',
	'SECTOR_TEJIDO' : 'SECTOR',
	'SUBSECTOR_TEJIDO' : 'SUBSECTOR',
	'NIT_TEJIDO' : 'NIT',
	'MENOR_200K_HABITANTES' : 'MENOR_200K_HABITANTES',
	'PDET' : 'PDET'} | COLS_VARIABLES_MUNICIPIOS_EXPORTACIONES

# VISTA: Información socioeconómica por municipio

ls_filtros_socioec_municipios = ['DEPARTAMENTO_TEJIDO',
                                'MUNICIPIO_TEJIDO',
                                'PDET',
                                'MENOR_200K_HABITANTES',
                                'ZOMAC'
                                ]

dict_filtros_socioec_municipios = {'DEPARTAMENTO_TEJIDO' : 'Departamento de la ubicación del HQ',
                                'MUNICIPIO_TEJIDO' : 'Municipio de la ubicación del HQ',
                                'PDET' : 'Ubicación del HQ en municipio PDET',
                                'MENOR_200K_HABITANTES' : 'Ubicación del HQ en municipio menor 200k habitantes', 
                                'ZOMAC' : 'Ubicación del HQ en zona más afectada por el conflicto - ZOMAC'}

dict_query_socioec_municipios = {'CODIGO_DEPARTAMENTO_TEJIDO' : 'CODIGO_DEPARTAMENTO',
	'DEPARTAMENTO_TEJIDO' : 'DEPARTAMENTO',
	'CODIGO_MUNICIPIO_TEJIDO' : 'CODIGO_MUNICIPIO',
	'MUNICIPIO_TEJIDO' : 'MUNICIPIO',
	'MENOR_200K_HABITANTES' : 'MENOR_200K_HABITANTES',
	'PDET' : 'PDET',
	'_ACT_PRIMARIAS_MUNICIPIO' : '_ACT_PRIMARIAS_MUNICIPIO',
	'_ACT_SECUNDARIAS_MUNICIPIO' : '_ACT_SECUNDARIAS_MUNICIPIO',
	'_ACT_TERCIARIAS_MUNICIPIO' : '_ACT_TERCIARIAS_MUNICIPIO',
	'_GRUPOS_ETNICOS_MUNICIPIO' : '_ACT_GRUPOS_ETNICOS_MUNICIPIO',
	'_INFORMALIDAD_MUNICIPIO' : '_INFORMALIDAD_MUNICIPIO',
	'_JOVENES_MUNICIPIO' : '_JOVENES_MUNICIPIO',
	'_MUJERES_MUNICIPIO' : '_MUJERES_MUNICIPIO',
	'_POBL_CON_DISCAPACIDAD_MUNICIPIO' : '_POBL_CON_DISCAPACIDAD_MUNICIPIO',
	'_POBL_CON_EDU_TECNICATECNOLOGIA_MUNICIPIO' : '_POBL_CON_EDU_TECNICATECNOLOGIA_MUNICIPIO',
	'_POBL_CON_EDUCACION_MEDIA_MUNICIPIO' : '_POBL_CON_EDUCACION_MEDIA_MUNICIPIO',
	'_POBL_CON_POSGRADO_MUNICIPIO' : '_POBL_CON_POSGRADO_MUNICIPIO',
	'_POBL_CON_PREGRADO_MUNICIPIO' : '_POBL_CON_PREGRADO_MUNICIPIO',
	'_POBREZA_MUNICIPIO' : '_POBREZA_MUNICIPIO',
	'POBLACION_MUNICIPIO' : 'POBLACION_MUNICIPIO',
	'ZOMAC' : 'ZOMAC'}

# ==================== FUNCIONES ===================

def query_data_tejido_municipios(
    dict_columnas: dict,
    filtros_tejido_municipios: dict,
) -> str:
    """
    Devuelve una consulta SQL dinámica para la vista **MUNICIPIOS_EXPORTACIONES** en la página de Municipios.

    El resultado:
    - Selecciona las columnas definidas en ``dict_columnas`` con alias legibles.
    - Aplica filtros sobre la tabla principal **A** mediante ``filtros_tejido_municipios``.

    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula
        ``SELECT``.
    filtros_tejido_municipios : dict
        Mapeo ``{columna_A : [valores]}`` aplicado sobre la tabla
        ``MUNICIPIOS_EXPORTACIONES`` (alias **A**).
        Cada valor asociado a una clave debe ser una secuencia de valores (por ejemplo,
        lista o tupla). Si la secuencia está vacía o el valor es falsy, el filtro para
        esa columna se omite.

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
    for col, vals in filtros_tejido_municipios.items():
        if vals:
            inner = ", ".join(f"'{v}'" for v in vals)
            condiciones_A.append(f"A.{col} IN ({inner})")
    filtros_A = " AND ".join(condiciones_A) or "1=1"

    # QUERY completa ----------------------------------------------------------
    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "MUNICIPIOS_EXPORTACIONES AS A\n"
        f"WHERE {filtros_A}\n"
    )

    return query

def resumen_exportaciones_sectores_municipios(df_snowpark, periodos_cerrados=None, periodos_corridos=None):
    """
    Procesa el DataFrame de Snowpark para generar resumen de exportaciones por sector y municipio.
    
    Parámetros
    ----------
    df_snowpark : DataFrame de Snowpark
        DataFrame con las columnas: CADENA_PRODUCTIVA, SECTOR, SUBSECTOR,
        CODIGO_DEPARTAMENTO, DEPARTAMENTO, CODIGO_MUNICIPIO, MUNICIPIO,
        VALOR_FOB_USD_2018, VALOR_FOB_USD_2019, etc.
    periodos_cerrados : list, optional
        Lista de años cerrados en formato ['USD 2022', 'USD 2023', 'USD 2024']
    periodos_corridos : list, optional
        Lista de períodos corridos en formato ['USD Ene-Abr 2024', 'USD Ene-Abr 2025']
    
    Retorna
    -------
    pd.DataFrame
        DataFrame de pandas con el resumen de valores FOB por sector, departamento y municipio
    """
    
    try:
        # Identificar columnas de valor FOB
        valor_columns = [c for c in df_snowpark.columns if 'VALOR_FOB_USD' in c]
        
        if not valor_columns:
            print("No se encontraron columnas de valor FOB")
            return pd.DataFrame()
        
        # Determinar qué columnas incluir según los parámetros
        columnas_seleccionadas = []
        
        if periodos_cerrados:
            for periodo in periodos_cerrados:
                # Extraer el año del formato 'USD 2022'
                year = periodo.split()[-1]
                col_name = f'VALOR_FOB_USD_{year}'
                if col_name in valor_columns:
                    columnas_seleccionadas.append(col_name)
        
        if periodos_corridos:
            for periodo in periodos_corridos:
                # Extraer mes-año del formato 'USD Ene-Abr 2024'
                # Dividir por espacios y tomar todo después de 'USD'
                parts = periodo.split(' ', 1)
                if len(parts) == 2:
                    periodo_texto = parts[1]  # 'Ene-Abr 2024'
                    # Buscar coincidencias flexibles en las columnas disponibles
                    for col_val in valor_columns:
                        if all(part.upper() in col_val.upper() for part in periodo_texto.split()):
                            columnas_seleccionadas.append(col_val)
                            break
        
        # Si no se especificaron períodos, usar todas las columnas
        if not columnas_seleccionadas:
            columnas_seleccionadas = valor_columns
        
        # Agregación en Snowpark - suma de valores FOB
        agg_list = [snow_sum(col(c)).alias(c) for c in columnas_seleccionadas]
        
        df_resumen_snowpark = (
            df_snowpark
            .groupBy(
                col('"SECTOR"'),
                col('"CODIGO_DEPARTAMENTO"'),
                col('"DEPARTAMENTO"'),
                col('"CODIGO_MUNICIPIO"'),
                col('"MUNICIPIO"')
            )
            .agg(*agg_list)
            .orderBy(
                col('"DEPARTAMENTO"').asc(),
                col('"MUNICIPIO"').asc()
            )
        )
        
        # Conversión a Pandas
        df_resumen = df_resumen_snowpark.to_pandas()
        
        # Renombrar columnas de agrupación
        df_resumen.rename(columns={
            'SECTOR': 'Sector',
            'CODIGO_DEPARTAMENTO': 'Código departamento',
            'DEPARTAMENTO': 'Departamento',
            'CODIGO_MUNICIPIO': 'Código municipio',
            'MUNICIPIO': 'Municipio'
        }, inplace=True)
        
        # Transformar valores USD sin decimales
        for col_name in columnas_seleccionadas:
            if col_name in df_resumen.columns:
                df_resumen[col_name] = df_resumen[col_name].astype(int)
        
        # Renombrar columnas de valor FOB al formato 'FOB USD YYYY' / 'FOB USD Enero YYYY'
        _MES = {'ENE': 'Enero', 'FEB': 'Febrero', 'MAR': 'Marzo', 'ABR': 'Abril',
                'MAY': 'Mayo', 'JUN': 'Junio', 'JUL': 'Julio', 'AGO': 'Agosto',
                'SEP': 'Septiembre', 'OCT': 'Octubre', 'NOV': 'Noviembre', 'DIC': 'Diciembre'}

        rename_dict = {}
        for col_val in df_resumen.columns:
            if 'VALOR_FOB_USD_' in col_val:
                parts = col_val.replace('VALOR_FOB_USD_', '').split('_')
                if parts[-1].isdigit():
                    año = parts[-1]
                    meses = parts[:-1]
                    if not meses:
                        rename_dict[col_val] = f'FOB USD {año}'
                    else:
                        meses_str = ' - '.join(_MES.get(m, m.capitalize()) for m in meses)
                        rename_dict[col_val] = f'FOB USD {meses_str} {año}'

        df_resumen.rename(columns=rename_dict, inplace=True)

        # Eliminar los datos de código de departamento y municipio "DESCONOCIDO"
        df_resumen = df_resumen[
            (df_resumen['Código departamento'] != 'DESCONOCIDO') &
            (df_resumen['Código municipio'] != 'DESCONOCIDO')
        ]
        
        return df_resumen
    
    except Exception as e:
        print(f"Error al procesar el resumen de exportaciones por sector y municipio: {e}")
        return pd.DataFrame()
    
def crear_mapa_municipios_sectores(
    df_resumen_sectores,
    columnas_fob: list,
    tolerance: float = None
):
    """
    Crea un mapa interactivo de municipios (puntos) mostrando sectores por municipio.

    Parámetros
    ----------
    df_resumen_sectores : pd.DataFrame
        DataFrame con columnas: 'CODIGO_MUNICIPIO', 'NOMBRE_MUNICIPIO', 'NOMBRE_DEPARTAMENTO',
        'Sector', columnas FOB, 'LATITUD', 'LONGITUD'
    columnas_fob : list
        Lista de columnas FOB a mostrar en el hover (ej: ['FOB USD 2021', 'FOB USD 2022'])
    tolerance : ignorado, mantenido por compatibilidad

    Retorna
    -------
    plotly.graph_objs._figure.Figure
        Figura de Plotly con el mapa
    """

    # Copiar el dataframe para no modificar el original
    df = df_resumen_sectores.copy()

    # Filtrar registros sin coordenadas
    df = df[df['LATITUD'].notna() & df['LONGITUD'].notna()]

    if df.empty:
        return "No se encontraron coordenadas para los filtros seleccionados."

    # Usar la última columna de la lista para determinar el top 5
    columna_ranking = columnas_fob[-1]

    # Calcular top 5 sectores por municipio según la columna de ranking
    df_top5 = (
        df.sort_values(['CODIGO_MUNICIPIO', columna_ranking], ascending=[True, False])
        .groupby('CODIGO_MUNICIPIO')
        .head(5)
    )

    # Crear texto para hover por municipio
    hover_data = {}
    for codigo_mpio in df_top5['CODIGO_MUNICIPIO'].unique():
        df_mpio = df_top5[df_top5['CODIGO_MUNICIPIO'] == codigo_mpio]

        # Construir texto formateado
        texto_hover = f"<b>Departamento:</b> {df_mpio['Departamento'].iloc[0]}<br>"
        texto_hover += f"<b>Municipio:</b> {df_mpio['Municipio'].iloc[0]}<br><br>"

        # Crear encabezado
        encabezado = "Sector".ljust(30)
        for col_fob in columnas_fob:
            nombre_corto = col_fob.replace('FOB USD ', '')
            encabezado += nombre_corto.rjust(25)
        texto_hover += f"<b>{encabezado}</b><br>"
        texto_hover += "-" * (30 + 25 * len(columnas_fob)) + "<br>"

        # Agregar filas de datos
        for _, row in df_mpio.iterrows():
            fila = row['Sector'][:28].ljust(30)
            for col_fob in columnas_fob:
                valor = "$" + milify(row[col_fob])
                fila += valor.rjust(25)
            texto_hover += fila + "<br>"

        # Agregar línea en blanco y nota al final
        texto_hover += "<br>"
        texto_hover += '<b>Nota:</b> M (millones) - USD FOB.'

        hover_data[codigo_mpio] = texto_hover

    # Obtener un punto único por municipio con lat/lon y hover text
    df_geo = df[['CODIGO_MUNICIPIO', 'NOMBRE_MUNICIPIO', 'NOMBRE_DEPARTAMENTO', 'LATITUD', 'LONGITUD']].drop_duplicates(subset='CODIGO_MUNICIPIO')
    df_geo['hover_text'] = df_geo['CODIGO_MUNICIPIO'].map(hover_data)

    if df_geo.empty:
        return "No se encontraron coordenadas para los filtros seleccionados."

    # Crear el mapa de puntos con plotly express
    fig = px.scatter_geo(
        df_geo,
        lat='LATITUD',
        lon='LONGITUD',
        hover_name='hover_text',
        hover_data={
            'LATITUD': False,
            'LONGITUD': False,
            'hover_text': False,
        },
    )

    # Configurar el diseño geográfico centrado en Colombia
    fig.update_geos(
        visible=True,
        showcountries=True,
        countrycolor='#CCCCCC',
        showcoastlines=False,
        showland=True,
        landcolor='#F5F5F5',
        bgcolor='white',
        showframe=False,
        center=dict(lat=4.5, lon=-74.0),
        projection_scale=4.5,
        projection_type='mercator',
    )

    # Layout
    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Courier New, monospace",
            align="left"
        )
    )

    # Estilo de los marcadores y tooltip
    fig.update_traces(
        marker=dict(
            color='#E67E22',
            size=8,
            line=dict(color='#2C3E50', width=1.0),
            opacity=0.9,
        ),
        hovertemplate='%{hovertext}<extra></extra>',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Courier New, monospace",
            bordercolor="#2C3E50"
        )
    )

    return fig

def resumen_empresas_tamano_municipios(df_snowpark, col_conteo=None):
    """
    Procesa el DataFrame de Snowpark para generar resumen de empresas por tamaño y municipio.

    Parámetros
    ----------
    df_snowpark : DataFrame de Snowpark
        DataFrame con las columnas: NIT, TAMANO_EMPRESA,
        CODIGO_DEPARTAMENTO, DEPARTAMENTO, CODIGO_MUNICIPIO, MUNICIPIO, VALOR_FOB_USD_*
    col_conteo : str, optional
        Alias de la columna a usar como período de filtro (ej. 'VALOR_FOB_USD_ENE_2026').
        Debe coincidir con un valor de COLS_VARIABLES_MUNICIPIOS_EXPORTACIONES en config.py.
        Si no se especifica, se usa el último año cerrado disponible.

    Retorna
    -------
    pd.DataFrame
        DataFrame de pandas con:
        - Número de empresas por tamaño y municipio
        - Distribución porcentual por tamaño dentro de cada municipio (suma 100% por municipio)
    """

    try:
        # Identificar columnas de valor FOB
        valor_columns = [c for c in df_snowpark.columns if 'VALOR_FOB_USD' in c]

        # Determinar la columna de filtro
        if col_conteo and col_conteo in valor_columns:
            columnas_seleccionadas = [col_conteo]
        else:
            # Fallback: último año cerrado (columnas cuyo sufijo es solo un número)
            closed_columns = [c for c in valor_columns if c.replace('VALOR_FOB_USD_', '').isdigit()]
            if closed_columns:
                last_closed_col = max(closed_columns, key=lambda c: int(c.replace('VALOR_FOB_USD_', '')))
                columnas_seleccionadas = [last_closed_col]
            else:
                columnas_seleccionadas = valor_columns
        
        # Filtrar empresas que exportaron en los períodos seleccionados (FOB > 0)
        if columnas_seleccionadas:
            # Crear condición: al menos una columna seleccionada debe ser > 0
            condicion = None
            for col_name in columnas_seleccionadas:
                if condicion is None:
                    condicion = col(f'"{col_name}"') > 0
                else:
                    condicion = condicion | (col(f'"{col_name}"') > 0)
            
            df_filtrado = df_snowpark.filter(condicion)
        else:
            df_filtrado = df_snowpark
        
        # Agregación en Snowpark - conteo distinto de NITs por tamaño, departamento y municipio
        df_resumen_snowpark = (
            df_filtrado
            .groupBy(
                col('"CODIGO_DEPARTAMENTO"'),
                col('"DEPARTAMENTO"'),
                col('"CODIGO_MUNICIPIO"'),
                col('"MUNICIPIO"'),
                col('"TAMANO_EMPRESA"')
            )
            .agg(count_distinct(col('"NIT"')).alias('Número de empresas'))
            .orderBy(
                col('"DEPARTAMENTO"').asc(),
                col('"MUNICIPIO"').asc(),
                col('"TAMANO_EMPRESA"').asc()
            )
        )
        
        # Conversión a Pandas
        df_resumen = df_resumen_snowpark.to_pandas()
        
        # Renombrar columnas
        df_resumen.rename(columns={
            'CODIGO_DEPARTAMENTO': 'Código departamento',
            'DEPARTAMENTO': 'Departamento',
            'CODIGO_MUNICIPIO': 'Código municipio',
            'MUNICIPIO': 'Municipio',
            'TAMANO_EMPRESA': 'Tamaño empresa'
        }, inplace=True)
        
        # Calcular distribución porcentual por municipio
        df_resumen['Distribución porcentual (%)'] = (
            df_resumen.groupby('Municipio')['Número de empresas']
            .transform(lambda x: (x / x.sum()) * 100)
        )
        
        # Redondear a 2 decimales y eliminar decimales innecesarios
        df_resumen['Distribución porcentual (%)'] = df_resumen['Distribución porcentual (%)'].round(2).astype(str).str.rstrip('0').str.rstrip('.')

        # Eliminar los datos de código de departamento y municipio "DESCONOCIDO"
        df_resumen = df_resumen[
            (df_resumen['Código departamento'] != 'DESCONOCIDO') &
            (df_resumen['Código municipio'] != 'DESCONOCIDO')
        ]
        
        return df_resumen
    
    except Exception as e:
        print(f"Error al procesar el resumen de empresas por tamaño y municipio: {e}")
        return pd.DataFrame()
    
def resumen_info_socioeconomica_municipios(df_snowpark):
    """
    Procesa el DataFrame de Snowpark para generar resumen de información socioeconómica por municipio.
    
    Parámetros
    ----------
    df_snowpark : DataFrame de Snowpark
        DataFrame con las columnas: CODIGO_DEPARTAMENTO, DEPARTAMENTO, 
        CODIGO_MUNICIPIO, MUNICIPIO, y todas las variables socioeconómicas
    
    Retorna
    -------
    pd.DataFrame
        DataFrame de pandas con información única por municipio:
        - Datos de identificación (departamento y municipio)
        - Variables socioeconómicas y demográficas
    """
    
    try:
        # Columnas de identificación
        columnas_identificacion = [
            '"CODIGO_DEPARTAMENTO"',
            '"DEPARTAMENTO"',
            '"CODIGO_MUNICIPIO"',
            '"MUNICIPIO"'
        ]
        
        # Columnas socioeconómicas
        columnas_socioeconomicas = [
            '"MENOR_200K_HABITANTES"',
            '"PDET"',
            '"_ACT_PRIMARIAS_MUNICIPIO"',
            '"_ACT_SECUNDARIAS_MUNICIPIO"',
            '"_ACT_TERCIARIAS_MUNICIPIO"',
            '"_ACT_GRUPOS_ETNICOS_MUNICIPIO"',
            '"_INFORMALIDAD_MUNICIPIO"',
            '"_JOVENES_MUNICIPIO"',
            '"_MUJERES_MUNICIPIO"',
            '"_POBL_CON_DISCAPACIDAD_MUNICIPIO"',
            '"_POBL_CON_EDU_TECNICATECNOLOGIA_MUNICIPIO"',
            '"_POBL_CON_EDUCACION_MEDIA_MUNICIPIO"',
            '"_POBL_CON_POSGRADO_MUNICIPIO"',
            '"_POBL_CON_PREGRADO_MUNICIPIO"',
            '"_POBREZA_MUNICIPIO"',
            '"POBLACION_MUNICIPIO"',
            '"ZOMAC"'
        ]
        
        # Seleccionar columnas necesarias y eliminar duplicados
        columnas_totales = columnas_identificacion + columnas_socioeconomicas
        
        df_resumen_snowpark = (
            df_snowpark
            .select(*[col(c) for c in columnas_totales])
            .distinct()
            .orderBy(
                col('"DEPARTAMENTO"').asc(),
                col('"MUNICIPIO"').asc()
            )
        )
        
        # Conversión a Pandas
        df_resumen = df_resumen_snowpark.to_pandas()
        
        # Renombrar columnas para mayor claridad
        df_resumen.rename(columns={
            'CODIGO_DEPARTAMENTO': 'Código departamento',
            'DEPARTAMENTO': 'Departamento',
            'CODIGO_MUNICIPIO': 'Código municipio',
            'MUNICIPIO': 'Municipio',
            'MENOR_200K_HABITANTES': 'Menor 200K habitantes',
            'PDET': 'PDET',
            '_ACT_PRIMARIAS_MUNICIPIO': 'Actividades primarias (%)',
            '_ACT_SECUNDARIAS_MUNICIPIO': 'Actividades secundarias (%)',
            '_ACT_TERCIARIAS_MUNICIPIO': 'Actividades terciarias (%)',
            '_ACT_GRUPOS_ETNICOS_MUNICIPIO': 'Grupos étnicos (%)',
            '_INFORMALIDAD_MUNICIPIO': 'Informalidad (%)',
            '_JOVENES_MUNICIPIO': 'Jóvenes (%)',
            '_MUJERES_MUNICIPIO': 'Mujeres (%)',
            '_POBL_CON_DISCAPACIDAD_MUNICIPIO': 'Población con discapacidad (%)',
            '_POBL_CON_EDU_TECNICATECNOLOGIA_MUNICIPIO': 'Población con educación técnica/tecnología (%)',
            '_POBL_CON_EDUCACION_MEDIA_MUNICIPIO': 'Población con educación media (%)',
            '_POBL_CON_POSGRADO_MUNICIPIO': 'Población con posgrado (%)',
            '_POBL_CON_PREGRADO_MUNICIPIO': 'Población con pregrado (%)',
            '_POBREZA_MUNICIPIO': 'Pobreza (%)',
            'POBLACION_MUNICIPIO': 'Población total',
            'ZOMAC': 'ZOMAC'
        }, inplace=True)
        
        # Redondear columnas numéricas a 2 decimales
        columnas_numericas = [
            'Actividades primarias (%)', 'Actividades secundarias (%)', 
            'Actividades terciarias (%)', 'Grupos étnicos (%)', 
            'Informalidad (%)', 'Jóvenes (%)', 'Mujeres (%)', 
            'Población con discapacidad (%)',
            'Población con educación técnica/tecnología (%)', 
            'Población con educación media (%)', 'Población con posgrado (%)',
            'Población con pregrado (%)', 'Pobreza (%)'
        ]
        
        for col_name in columnas_numericas:
            if col_name in df_resumen.columns:
                df_resumen[col_name] = df_resumen[col_name].round(2)
        
        # Convertir población total a entero
        if 'Población total' in df_resumen.columns:
            df_resumen['Población total'] = df_resumen['Población total'].fillna(0).astype(int)
        
        # Eliminar los datos de código de departamento y municipio "DESCONOCIDO"
        df_resumen = df_resumen[
            (df_resumen['Código departamento'] != 'DESCONOCIDO') &
            (df_resumen['Código municipio'] != 'DESCONOCIDO')
        ]
        
        return df_resumen
    
    except Exception as e:
        print(f"Error al procesar el resumen de información socioeconómica de municipios: {e}")
        return pd.DataFrame()
    
def crear_mapa_municipios_socioeconomico(df_municipios_sociec, tolerance=None):
    """
    Crea un mapa interactivo de municipios (puntos) con información socioeconómica.

    Parámetros
    ----------
    df_municipios_sociec : pd.DataFrame
        DataFrame con columnas de identificación de municipio, variables socioeconómicas,
        'LATITUD' y 'LONGITUD'
    tolerance : ignorado, mantenido por compatibilidad

    Retorna
    -------
    plotly.graph_objects.Figure o str
        Figura de Plotly si tiene éxito, mensaje de error si falla
    """

    try:
        df = df_municipios_sociec.copy()

        # Filtrar registros sin coordenadas
        df = df[df['LATITUD'].notna() & df['LONGITUD'].notna()]

        if df.empty:
            return "No se encontraron coordenadas para los filtros seleccionados."

        # Construir hover text por fila (un punto por municipio)
        hover_texts = []
        for _, row in df.iterrows():
            hover_lines = [
                f"<b>Departamento:</b> {row['Departamento']}",
                f"<b>Municipio:</b> {row['Municipio']}",
                ""
            ]

            poblacion = f"{int(row['Población total']):,}".replace(',', '.')
            hover_lines.append(f"<b>Población total:</b> {poblacion} habitantes")
            hover_lines.append("")

            hover_lines.append("<b>Características:</b>")
            if pd.notna(row['Menor 200K habitantes']) and row['Menor 200K habitantes'] == 'SI':
                hover_lines.append("• Municipio menor a 200K habitantes")
            if pd.notna(row['PDET']) and row['PDET'] == 'SI':
                hover_lines.append("• PDET (Programa de Desarrollo con Enfoque Territorial)")
            if pd.notna(row['ZOMAC']) and row['ZOMAC'] == 'SI':
                hover_lines.append("• ZOMAC (Zona Más Afectada por el Conflicto)")
            hover_lines.append("")

            hover_lines.append("<b>Estructura económica:</b>")
            if pd.notna(row['Actividades primarias (%)']):
                hover_lines.append(f"• Actividades primarias: {row['Actividades primarias (%)']:.1f}%")
            if pd.notna(row['Actividades secundarias (%)']):
                hover_lines.append(f"• Actividades secundarias: {row['Actividades secundarias (%)']:.1f}%")
            if pd.notna(row['Actividades terciarias (%)']):
                hover_lines.append(f"• Actividades terciarias: {row['Actividades terciarias (%)']:.1f}%")
            hover_lines.append("")

            hover_lines.append("<b>Indicadores sociales:</b>")
            if pd.notna(row['Pobreza (%)']):
                hover_lines.append(f"• Pobreza: {row['Pobreza (%)']:.1f}%")
            if pd.notna(row['Informalidad (%)']):
                hover_lines.append(f"• Informalidad: {row['Informalidad (%)']:.1f}%")
            hover_lines.append("")

            hover_lines.append("<b>Composición poblacional:</b>")
            if pd.notna(row['Mujeres (%)']):
                hover_lines.append(f"• Mujeres: {row['Mujeres (%)']:.1f}%")
            if pd.notna(row['Jóvenes (%)']):
                hover_lines.append(f"• Jóvenes: {row['Jóvenes (%)']:.1f}%")
            if pd.notna(row['Grupos étnicos (%)']):
                hover_lines.append(f"• Grupos étnicos: {row['Grupos étnicos (%)']:.1f}%")
            if pd.notna(row['Población con discapacidad (%)']):
                hover_lines.append(f"• Población con discapacidad: {row['Población con discapacidad (%)']:.1f}%")
            hover_lines.append("")

            hover_lines.append("<b>Nivel educativo:</b>")
            if pd.notna(row['Población con educación media (%)']):
                hover_lines.append(f"• Educación media: {row['Población con educación media (%)']:.1f}%")
            if pd.notna(row['Población con educación técnica/tecnología (%)']):
                hover_lines.append(f"• Técnica/Tecnología: {row['Población con educación técnica/tecnología (%)']:.1f}%")
            if pd.notna(row['Población con pregrado (%)']):
                hover_lines.append(f"• Pregrado: {row['Población con pregrado (%)']:.1f}%")
            if pd.notna(row['Población con posgrado (%)']):
                hover_lines.append(f"• Posgrado: {row['Población con posgrado (%)']:.1f}%")

            hover_texts.append({
                'CODIGO_MUNICIPIO': row['CODIGO_MUNICIPIO'],
                'hover_text': '<br>'.join(hover_lines)
            })

        df_hover = pd.DataFrame(hover_texts)

        # Un punto único por municipio con lat/lon
        df_geo = df[['CODIGO_MUNICIPIO', 'NOMBRE_MUNICIPIO', 'NOMBRE_DEPARTAMENTO', 'LATITUD', 'LONGITUD']].drop_duplicates(subset='CODIGO_MUNICIPIO')
        df_geo = df_geo.merge(df_hover, on='CODIGO_MUNICIPIO', how='left')

        if df_geo.empty:
            return "No se encontraron coordenadas para los filtros seleccionados."

        # Crear el mapa de puntos con plotly express
        fig = px.scatter_geo(
            df_geo,
            lat='LATITUD',
            lon='LONGITUD',
            hover_name='hover_text',
            hover_data={
                'LATITUD': False,
                'LONGITUD': False,
                'hover_text': False,
            },
        )

        # Configurar el diseño geográfico centrado en Colombia
        fig.update_geos(
            visible=True,
            showcountries=True,
            countrycolor='#CCCCCC',
            showcoastlines=False,
            showland=True,
            landcolor='#F5F5F5',
            bgcolor='white',
            showframe=False,
            center=dict(lat=4.5, lon=-74.0),
            projection_scale=4.5,
            projection_type='mercator',
        )

        fig.update_layout(
            height=700,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial",
                align="left"
            )
        )

        # Estilo de los marcadores y tooltip
        fig.update_traces(
            marker=dict(
                color='#3498DB',
                size=8,
                line=dict(color='#2C3E50', width=1.0),
                opacity=0.9,
            ),
            hovertemplate='%{hovertext}<extra></extra>',
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial",
                bordercolor="#2C3E50"
            )
        )

        return fig

    except Exception as e:
        return f"Error generando el gráfico: {e}"
