# Librerías
import pandas as pd
import plotly.express as px
from.utils import milify
from snowflake.snowpark.functions import count_distinct, sum as snow_sum, col, when

# ==================== PARÁMETROS PARA PÁGINA SEGMENTACIÓN ===================
from .config import (
    exportaciones_bienes_servicios_anios_disponibles,
    COLS_VARIABLES_DEPARTAMENTOS_EXPORTACIONES
)

# ==================== PARÁMETROS PARA DEPARTAMENTOS ===================

# VISTA: Servicios por departamento ofrecido por ProColombia

ls_filtros_tejido_servicios_departamentos = ['DEPARTAMENTO_TEJIDO',
                                             'CADENA_SEGMENTACION_TEJIDO']

dict_filtros_tejido_servicios_departamentos = {'DEPARTAMENTO_TEJIDO' : 'Departamento de la ubicación del HQ',
                                               'CADENA_SEGMENTACION_TEJIDO' : 'Cadena de segmentación'}

dict_query_tejido_servicios_departamentos = {'CODIGO_DEPARTAMENTO_TEJIDO' : 'CODIGO_DEPARTAMENTO',
                                             'DEPARTAMENTO_TEJIDO' : 'DEPARTAMENTO',
                                             'CADENA_SEGMENTACION_TEJIDO' : 'CADENA_SEGMENTACION',
                                             'NIT_TEJIDO' : 'NIT',
                                             'TOTAL_SERVICIOS_OFRECIDOS_TEJIDO' : 'TOTAL_SERVICIOS_OFRECIDOS',
                                             'EMPRESA_CON_SERVICIOS_TEJIDO' : 'EMPRESA_CON_SERVICIOS'}

# VISTA: Exportaciones por departamento de origen

ls_filtros_exportaciones_departamentos = ['CADENA_PRODUCTIVA_BIENES_SERVICIOS',
                                          'SECTOR_BIENES_SERVICIOS',
                                          'SUBSECTOR_BIENES_SERVICIOS',
                                          'COD_POSICION_ARANCELARIA_BIENES_SERVICIOS',
                                          'DESC_POSICION_ARANCELARIA_BIENES_SERVICIOS']

dict_filtros_exportaciones_departamentos = {'CADENA_PRODUCTIVA_BIENES_SERVICIOS' : f'Cadena productiva de exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                                            'SECTOR_BIENES_SERVICIOS' : f'Sector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                                            'SUBSECTOR_BIENES_SERVICIOS' : f'Subsector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                                            'COD_POSICION_ARANCELARIA_BIENES_SERVICIOS' : f'Código de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                                            'DESC_POSICION_ARANCELARIA_BIENES_SERVICIOS' : f'Descripción de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}'}

dict_query_exportaciones_departamentos = {'CADENA_PRODUCTIVA_BIENES_SERVICIOS':'CADENA_PRODUCTIVA',
                                          'SECTOR_BIENES_SERVICIOS':'SECTOR',
                                          'SUBSECTOR_BIENES_SERVICIOS': 'SUBSECTOR',
                                          'CODIGO_DEPARTAMENTO_BIENES_SERVICIOS': 'CODIGO_DEPARTAMENTO',
                                          'DEPARTAMENTO_BIENES_SERVICIOS':'DEPARTAMENTO',
                                          'NIT_BIENES_SERVICIOS':'NIT',
                                          'TAMANO_EMPRESA_TEJIDO':'TAMANO_EMPRESA'} | COLS_VARIABLES_DEPARTAMENTOS_EXPORTACIONES

# ==================== FUNCIONES ===================

def query_data_tejido_servicios_departamentos(
    dict_columnas: dict,
    filtros_tejido_servicios_departamentos: dict,
) -> str:
    """
    Devuelve una consulta SQL dinámica para la vista **DEPARTAMENTOS_SERVICIOS** en la página de Departamentos.

    El resultado:
    - Selecciona las columnas definidas en ``dict_columnas`` con alias legibles.
    - Aplica filtros sobre la tabla principal **A** mediante ``filtros_tejido_servicios_departamentos``.
    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula
        ``SELECT``.
    filtros_tejido_servicios_departamentos : dict
        Mapeo ``{columna_A : [valores]}`` aplicado sobre la tabla
        ``DEPARTAMENTOS_SERVICIOS`` (alias **A**).
        Si la lista de valores está vacía, el filtro se omite.

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
    for col, vals in filtros_tejido_servicios_departamentos.items():
        if vals:
            inner = ", ".join(f"'{v}'" for v in vals)
            condiciones_A.append(f"A.{col} IN ({inner})")
    filtros_A = " AND ".join(condiciones_A) or "1=1"

    # QUERY completa ----------------------------------------------------------
    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "DEPARTAMENTOS_SERVICIOS AS A\n"
        f"WHERE {filtros_A}\n"
    )

    return query

def resumen_tejido_servicios_departamentos(df_snowpark):
    """
    Procesa el DataFrame de Snowpark para generar resumen de tejido de servicios por departamento.
    
    Parámetros
    ----------
    df_snowpark : DataFrame de Snowpark
        DataFrame con las columnas: NIT, CODIGO_DEPARTAMENTO, DEPARTAMENTO, TOTAL_SERVICIOS_OFRECIDOS
    
    Retorna
    -------
    pd.DataFrame
        DataFrame de pandas con el resumen por departamento
    """

    try:
    
        # Agregación en Snowpark
        agg_list = [
            count_distinct(col('NIT')).alias('Número de empresas identificadas'),
            snow_sum(col('TOTAL_SERVICIOS_OFRECIDOS')).alias('Total de servicios ofrecidos'),
            count_distinct(
                when(col('TOTAL_SERVICIOS_OFRECIDOS') > 0, col('NIT'))
            ).alias('Empresas con servicios ofrecidos')
        ]
        
        df_resumen_snowpark = (
            df_snowpark
            .groupBy(col('"CODIGO_DEPARTAMENTO"'), col('"DEPARTAMENTO"'))
            .agg(*agg_list)
            .orderBy(col('"DEPARTAMENTO"').asc())
        )
        
        # Conversión a Pandas
        df_resumen = df_resumen_snowpark.to_pandas()

        # Renombras columnas
        df_resumen.rename(columns={
            'CODIGO_DEPARTAMENTO': 'Código departamento',
            'DEPARTAMENTO': 'Departamento'
        }, inplace=True)

        # Quitar decimales
        df_resumen['Número de empresas identificadas'] = df_resumen['Número de empresas identificadas'].astype(int)
        df_resumen['Total de servicios ofrecidos'] = df_resumen['Total de servicios ofrecidos'].astype(int)
        df_resumen['Empresas con servicios ofrecidos'] = df_resumen['Empresas con servicios ofrecidos'].astype(int)

        # Eliminar código de departamento "No determinado"
        df_resumen = df_resumen[df_resumen['Código departamento'] != 'No determinado']
        
        return df_resumen

    except Exception as e:
        print(f"Error al procesar el resumen: {e}")
        return pd.DataFrame()
    
def crear_mapa_departamentos_servicios(df_resumen):
    """
    Crea un mapa interactivo de departamentos con Plotly (puntos).

    Parámetros
    ----------
    df_resumen : pd.DataFrame
        DataFrame con las columnas: 'Código departamento', 'Departamento',
        'Número de empresas identificadas', 'Total de servicios ofrecidos',
        'Empresas con servicios ofrecidos', 'LATITUD', 'LONGITUD'

    Retorna
    -------
    plotly.graph_objects.Figure o str
        Figura de Plotly si tiene éxito, mensaje de error si falla
    """

    try:
        df = df_resumen.copy()

        # Eliminar filas sin coordenadas
        df = df[df['LATITUD'].notna() & df['LONGITUD'].notna()]

        # Preparar texto personalizado para hover con separador de miles usando punto
        df['hover_text'] = (
            '<b>Departamento:</b> ' + df['Departamento'] + '<br>' +
            '<br>' +
            '<b>Número de empresas identificadas:</b> ' + df['Número de empresas identificadas'].apply(lambda x: f'{int(x):,}'.replace(',', '.')) + '<br>' +
            '<b>Total de servicios ofrecidos:</b> ' + df['Total de servicios ofrecidos'].apply(lambda x: f'{int(x):,}'.replace(',', '.')) + '<br>' +
            '<b>Empresas con servicios ofrecidos:</b> ' + df['Empresas con servicios ofrecidos'].apply(lambda x: f'{int(x):,}'.replace(',', '.')) + '<br>' +
            '<br>' +
            '<i>Los indicadores se calculan según la ubicación del HQ de las empresas.</i>'
        )

        # Crear el mapa de puntos con plotly express
        fig = px.scatter_geo(
            df,
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
                font_size=13,
                font_family="Arial",
                align="left"
            )
        )

        # Estilo de los marcadores y tooltip
        fig.update_traces(
            marker=dict(
                color='#4A90E2',
                size=10,
                line=dict(color='#2C3E50', width=1.5),
                opacity=0.9,
            ),
            hovertemplate='%{hovertext}<extra></extra>',
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Arial",
                bordercolor="#2C3E50"
            )
        )

        return fig
    
    except Exception as e:
        # Manejo de excepciones y retorno de un mensaje de error
        return f"Error generando el gráfico: {e}"
    
def query_data_exportaciones_departamentos(
    dict_columnas: dict,
    filtros_exportaciones_departamentos: dict,
) -> str:
    """
    Devuelve una consulta SQL dinámica para la vista **DEPARTAMENTOS_EXPORTACIONES** en la página de Departamentos.

    El resultado:
    - Selecciona las columnas definidas en ``dict_columnas`` con alias legibles.
    - Aplica filtros sobre la tabla principal **A** mediante ``filtros_exportaciones_departamentos``.
    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula
        ``SELECT``.
    filtros_exportaciones_departamentos : dict
        Mapeo ``{columna_A : [valores]}`` aplicado sobre la tabla
        ``DEPARTAMENTOS_EXPORTACIONES`` (alias **A**).
        Si la lista de valores está vacía, el filtro se omite.

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
    for col, vals in filtros_exportaciones_departamentos.items():
        if vals:
            inner = ", ".join(f"'{v}'" for v in vals)
            condiciones_A.append(f"A.{col} IN ({inner})")
    filtros_A = " AND ".join(condiciones_A) or "1=1"

    # QUERY completa ----------------------------------------------------------
    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "DEPARTAMENTOS_EXPORTACIONES AS A\n"
        f"WHERE {filtros_A}\n"
    )

    return query

def resumen_exportaciones_sectores_departamentos(df_snowpark, periodos_cerrados=None, periodos_corridos=None):
    """
    Procesa el DataFrame de Snowpark para generar resumen de exportaciones por sector y departamento.
    
    Parámetros
    ----------
    df_snowpark : DataFrame de Snowpark
        DataFrame con las columnas: CADENA_PRODUCTIVA, SECTOR, SUBSECTOR,
        CODIGO_DEPARTAMENTO, DEPARTAMENTO, 
        VALOR_FOB_USD_2020, VALOR_FOB_USD_2021, etc.
    periodos_cerrados : list, optional
        Lista de años cerrados en formato ['USD 2022', 'USD 2023', 'USD 2024']
    periodos_corridos : list, optional
        Lista de períodos corridos en formato ['USD Ene-Abr 2024', 'USD Ene-Abr 2025']
    
    Retorna
    -------
    pd.DataFrame
        DataFrame de pandas con el resumen de valores FOB por sector y departamento
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
                col('"DEPARTAMENTO"')
            )
            .agg(*agg_list)
            .orderBy(col('"DEPARTAMENTO"').asc())
        )
        
        # Conversión a Pandas
        df_resumen = df_resumen_snowpark.to_pandas()
        
        # Renombrar columnas de agrupación
        df_resumen.rename(columns={
            'SECTOR': 'Sector',
            'CODIGO_DEPARTAMENTO': 'Código departamento',
            'DEPARTAMENTO': 'Departamento'
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

        # Eliminar los datos de código de departamento "DESCONOCIDO"
        df_resumen = df_resumen[df_resumen['Código departamento'] != 'DESCONOCIDO']
        
        return df_resumen
    
    except Exception as e:
        print(f"Error al procesar el resumen de exportaciones por sector: {e}")
        return pd.DataFrame()


def resumen_empresas_tamano_departamentos(df_snowpark, col_conteo=None):
    """
    Procesa el DataFrame de Snowpark para generar resumen de empresas por tamaño y departamento.

    Parámetros
    ----------
    df_snowpark : DataFrame de Snowpark
        DataFrame con las columnas: NIT, TAMANO_EMPRESA,
        CODIGO_DEPARTAMENTO, DEPARTAMENTO, VALOR_FOB_USD_*
    col_conteo : str, optional
        Alias de la columna a usar como período de filtro (ej. 'VALOR_FOB_USD_ENE_2026').
        Debe coincidir con un valor de COLS_VARIABLES_DEPARTAMENTOS_EXPORTACIONES en config.py.
        Si no se especifica, se usa el último año cerrado disponible.

    Retorna
    -------
    pd.DataFrame
        DataFrame de pandas con:
        - Número de empresas por tamaño y departamento
        - Distribución porcentual por tamaño dentro de cada departamento (suma 100% por departamento)
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
        
        # Agregación en Snowpark - conteo distinto de NITs por tamaño y departamento
        df_resumen_snowpark = (
            df_filtrado
            .groupBy(
                col('"CODIGO_DEPARTAMENTO"'),
                col('"DEPARTAMENTO"'),
                col('"TAMANO_EMPRESA"')
            )
            .agg(count_distinct(col('"NIT"')).alias('Número de empresas'))
            .orderBy(col('"DEPARTAMENTO"').asc(), col('"TAMANO_EMPRESA"').asc())
        )
        
        # Conversión a Pandas
        df_resumen = df_resumen_snowpark.to_pandas()
        
        # Renombrar columnas
        df_resumen.rename(columns={
            'CODIGO_DEPARTAMENTO': 'Código departamento',
            'DEPARTAMENTO': 'Departamento',
            'TAMANO_EMPRESA': 'Tamaño empresa'
        }, inplace=True)
        
        # Calcular distribución porcentual por departamento
        df_resumen['Distribución porcentual (%)'] = (
            df_resumen.groupby('Departamento')['Número de empresas']
            .transform(lambda x: (x / x.sum()) * 100)
        )
        
        # Redondear a 2 decimales y eliminar decimales innecesarios
        df_resumen['Distribución porcentual (%)'] = df_resumen['Distribución porcentual (%)'].round(2)

        # Eliminar los datos de código de departamento "DESCONOCIDO"
        df_resumen = df_resumen[df_resumen['Código departamento'] != 'DESCONOCIDO']
        
        return df_resumen
    
    except Exception as e:
        print(f"Error al procesar el resumen de empresas por tamaño: {e}")
        return pd.DataFrame()
    
def crear_mapa_departamentos_sectores(
    df_resumen_sectores,
    columnas_fob: list,
):
    """
    Crea un mapa interactivo de departamentos (puntos) mostrando sectores por departamento.

    Parámetros
    ----------
    df_resumen_sectores : pd.DataFrame
        DataFrame con columnas: 'CODIGO_DEPARTAMENTO', 'NOMBRE_DEPARTAMENTO_LIMPIO',
        'Sector', columnas FOB, 'LATITUD', 'LONGITUD'
    columnas_fob : list
        Lista de columnas FOB a mostrar en el hover (ej: ['FOB USD 2023', 'FOB USD 2024'])
    tolerance : ignorado, mantenido por compatibilidad

    Retorna
    -------
    plotly.graph_objs._figure.Figure
        Figura de Plotly con el mapa
    """

    # Copiar el dataframe para no modificar el original
    df = df_resumen_sectores.copy()

    # Usar la última columna de la lista para determinar el top 5
    columna_ranking = columnas_fob[-1]

    # Calcular top 5 sectores por departamento según la columna de ranking
    df_top5 = (
        df.sort_values(['CODIGO_DEPARTAMENTO', columna_ranking], ascending=[True, False])
        .groupby('CODIGO_DEPARTAMENTO')
        .head(5)
    )

    # Crear texto para hover por departamento
    hover_data = {}
    for codigo_depto in df_top5['CODIGO_DEPARTAMENTO'].unique():
        df_depto = df_top5[df_top5['CODIGO_DEPARTAMENTO'] == codigo_depto]

        # Construir texto formateado
        texto_hover = f"<b>Departamento:</b> {df_depto['NOMBRE_DEPARTAMENTO_LIMPIO'].iloc[0]}<br><br>"

        # Crear encabezado
        encabezado = "Sector".ljust(30)
        for col_fob in columnas_fob:
            nombre_corto = col_fob.replace('FOB USD ', '')
            encabezado += nombre_corto.rjust(25)
        texto_hover += f"<b>{encabezado}</b><br>"
        texto_hover += "-" * (30 + 25 * len(columnas_fob)) + "<br>"

        # Agregar filas de datos
        for _, row in df_depto.iterrows():
            fila = row['Sector'][:28].ljust(30)  # Truncar sector si es muy largo
            for col_fob in columnas_fob:
                valor = "$" + milify(row[col_fob])
                fila += valor.rjust(25)
            texto_hover += fila + "<br>"

        # Agregar línea en blanco y nota al final
        texto_hover += "<br>"
        texto_hover += '<b>Nota:</b> M (millones) - USD FOB.'

        hover_data[codigo_depto] = texto_hover

    # Obtener un punto único por departamento con lat/lon y hover text
    df_geo = df[['CODIGO_DEPARTAMENTO', 'NOMBRE_DEPARTAMENTO_LIMPIO', 'LATITUD', 'LONGITUD']].drop_duplicates(subset='CODIGO_DEPARTAMENTO')
    df_geo = df_geo[df_geo['LATITUD'].notna() & df_geo['LONGITUD'].notna()].copy()
    df_geo['hover_text'] = df_geo['CODIGO_DEPARTAMENTO'].map(hover_data)

    # Si quedó vacío, devolvemos un mensaje amigable
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
            size=10,
            line=dict(color='#2C3E50', width=1.5),
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

def crear_mapa_departamentos_tamanos(df_resumen_tamanos):
    """
    Crea un mapa interactivo de departamentos con distribución por tamaño de empresa.
    
    Parámetros
    ----------
    df_resumen_tamanos : pd.DataFrame
        DataFrame con las columnas: 'Código departamento', 'Departamento',
        'Tamaño empresa', 'Número de empresas', 'Distribución porcentual (%)',
        'GEOMETRIA' (en formato WKT)
    tolerance : float, optional
        Nivel de simplificación de geometrías (default: 0.05).
        Valores mayores = más simplificación = más rápido
    
    Retorna
    -------
    plotly.graph_objects.Figure o str
        Figura de Plotly si tiene éxito, mensaje de error si falla
    """
    
    try:
        df = df_resumen_tamanos.copy()

        # Eliminar filas sin coordenadas
        df = df[df['LATITUD'].notna() & df['LONGITUD'].notna()]

        # Construir hover text por departamento
        hover_texts = []
        for codigo_dpto in df['Código departamento'].unique():
            df_dpto = df[df['Código departamento'] == codigo_dpto]
            nombre_dpto = df_dpto['Departamento'].iloc[0]

            hover_lines = [f'<b>Departamento:</b> {nombre_dpto}', '']

            total_empresas = 0
            total_porcentaje = 0

            for _, row in df_dpto.iterrows():
                tamano = row['Tamaño empresa']
                num_empresas = int(row['Número de empresas'])
                porcentaje = float(row['Distribución porcentual (%)']) if isinstance(row['Distribución porcentual (%)'], (int, float)) else float(str(row['Distribución porcentual (%)']).replace(',', '.'))

                total_empresas += num_empresas
                total_porcentaje += porcentaje

                num_empresas_fmt = f'{num_empresas:,}'.replace(',', '.')
                porcentaje_fmt = f'{porcentaje:.2f}'.replace('.', ',')

                hover_lines.append(f'<b>{tamano}:</b> {num_empresas_fmt} empresas ({porcentaje_fmt}%)')

            total_empresas_fmt = f'{total_empresas:,}'.replace(',', '.')
            total_porcentaje_fmt = f'{total_porcentaje:.2f}'.replace('.', ',')

            hover_lines.append('')
            hover_lines.append(f'<b>Total:</b> {total_empresas_fmt} empresas ({total_porcentaje_fmt}%)')
            hover_lines.append('')
            hover_lines.append('<i>Los indicadores se calculan según el departamento de origen de exportación.</i>')

            hover_texts.append({
                'Código departamento': codigo_dpto,
                'hover_text': '<br>'.join(hover_lines)
            })

        df_hover = pd.DataFrame(hover_texts)

        # Un punto único por departamento con lat/lon
        df_geo = df[['Código departamento', 'Departamento', 'LATITUD', 'LONGITUD']].drop_duplicates(subset='Código departamento')
        df_geo = df_geo.merge(df_hover, on='Código departamento', how='left')

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
                font_size=13,
                font_family="Arial",
                align="left"
            )
        )

        # Estilo de los marcadores y tooltip
        fig.update_traces(
            marker=dict(
                color='#27AE60',
                size=10,
                line=dict(color='#2C3E50', width=1.5),
                opacity=0.9,
            ),
            hovertemplate='%{hovertext}<extra></extra>',
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Arial",
                bordercolor="#2C3E50"
            )
        )

        return fig

    except Exception as e:
        return f"Error generando el gráfico: {e}"