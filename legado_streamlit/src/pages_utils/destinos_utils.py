# Librerías
import pandas as pd
import plotly.graph_objects as go
from.utils import format_espanol, milify
from snowflake.snowpark.functions import count_distinct, sum as snow_sum, col
import re

# ==================== PARÁMETROS PARA PÁGINA DESTINOS ===================

from .config import (
    exportaciones_bienes_servicios_anios_disponibles,
    COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA,
    COLS_VARIABLES_USUARIOS_COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA
)

# ==================== LISTA DE COLUMNAS Y DICCIONARIO DE NOMBRES PARA FILTROS ===================

ls_filtros_bienes = ['HUB_BIENES',
                    'PAIS_DESTINO_BIENES',
                    'CADENA_BIENES',
                    'SECTOR_BIENES',
                    'COD_POSICION_ARANCELARIA_BIENES',
                    'DESC_POSICION_ARANCELARIA_BIENES',
                    'SUBSECTOR_BIENES',
                    'VALOR_AGREGADO_EXPO_BIENES',
                    'TAMANO_TEJIDO'
                    ]

dict_filtros_bienes = {'HUB_BIENES' : f'HUB de destino {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'PAIS_DESTINO_BIENES' : f'País de destino {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'CADENA_BIENES' : f'Cadena de segmentación {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'SECTOR_BIENES' : f'Sector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'SUBSECTOR_BIENES' : f'Subsector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'COD_POSICION_ARANCELARIA_BIENES' : f'Código de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'DESC_POSICION_ARANCELARIA_BIENES' : f'Descripción de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'VALOR_AGREGADO_EXPO_BIENES' : 'Valor agregado exportaciones',
                        'TAMANO_TEJIDO' : 'Tamaño empresa'
}

# ==================== DICCIONARIO DE COLUMNAS PARA LA CONSULTA DE RESULTADOS ===================

dict_query_bienes = {'NIT_BIENES': 'NIT',
    'RAZON_SOCIAL_BIENES': 'Razón Social',
    'CADENA_BIENES': 'Cadena',
    'SECTOR_BIENES': 'Sector',
    'SUBSECTOR_BIENES': 'Subsector',
    'COD_POSICION_ARANCELARIA_BIENES': 'Subpartida',
    'DESC_POSICION_ARANCELARIA_BIENES': 'Posición Arancelaria',
    'VALOR_AGREGADO_EXPO_BIENES': 'Valor Agregado Exportaciones',
    'COD_DEPARTAMENTO_BIENES': 'Código Departamento Origen',
    'DEPARTAMENTO_BIENES' : 'Departamento de Origen',
    'PAIS_DESTINO_BIENES' : 'País de Destino Final',
    'HUB_BIENES': 'HUB',
    'TAMANO_TEJIDO': 'Tamaño de la Empresa',
    'INVERSION_EXTRANJERA_TEJIDO' : 'Sucursal/Sociedad Extranjera'
    } | COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA

# ==================== LISTA DE COLUMNAS PARA MOSTRAR AL USUARIO ===================

# Deben ser iguales a los elementos del AS en el diccionario anterior

ls_columnas_usuario_bienes = ['NIT',
    'Razón Social',
    'Cadena',
    'Tamaño de la Empresa',
    'País de Destino Final'
    ].append(COLS_VARIABLES_USUARIOS_COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA)

# ==================== GENERADOR DE CONSULTA ===================

def query_data_bienes(
    dict_columnas: dict,
    filtros_generales: dict,
) -> str:
    """
    Devuelve una consulta SQL dinámica para la vista **Bienes** en la página de Destinos.

    El resultado:
    - Selecciona las columnas definidas en ``dict_columnas`` con alias legibles.
    - Aplica filtros sobre la tabla principal **A** mediante ``filtros_generales``.

    Parámetros
    ----------
    dict_columnas : dict
        Mapeo ``{columna_en_base : alias_para_usuario}`` empleado en la cláusula
        ``SELECT``.
    filtros_generales : dict
        Mapeo ``{columna_A : [valores]}`` aplicado sobre la tabla
        ``BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P`` (alias **A**).
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
    for col, vals in filtros_generales.items():
        if vals:
            inner = ", ".join(f"'{v}'" for v in vals)
            condiciones_A.append(f"A.{col} IN ({inner})")
    filtros_A = " AND ".join(condiciones_A) or "1=1"

    # QUERY completa ----------------------------------------------------------
    query = (
        f"SELECT {columnas_str}\n"
        "FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION."
        "BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P AS A\n"
        f"WHERE {filtros_A}\n"
    )

    return query

# ==================== FUNCIONES PARA AGRUPAR DATOS ===================

def obtener_columnas_valor_y_ultimo_anio(df_snowpark):
    """
    Función auxiliar para identificar columnas de valor FOB USD y el último año
    """
    valor_columns = [c for c in df_snowpark.columns if 'Valor FOB USD ' in c]
    
    if not valor_columns:
        return None, None, None
    
    # Columna más reciente: año más alto; corridos (contienen 'Enero') tienen prioridad sobre año cerrado
    last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))
    last_year = int(re.findall(r'\d{4}', last_year_col_original)[0])

    return valor_columns, last_year, last_year_col_original

def aplicar_formato_columnas(df):
    """
    Función auxiliar para aplicar formato a las columnas
    """
    df_formateado = df.copy()
    
    for col_name in df_formateado.columns:
        if "USD" in col_name:
            df_formateado[col_name] = df_formateado[col_name].apply(lambda x: milify(x))
        if 'Empresas' in col_name:
            df_formateado[col_name] = df_formateado[col_name].apply(lambda x: format_espanol(x, decimales=0))
    
    return df_formateado

def resumen_por_cadena(df_snowpark):
    """
    Retorna: (df_resumen_cadenas, df_resumen_cadenas_formateado)
    """
    # Obtener columnas de valor y último año
    valor_columns, last_year, last_year_col_original = obtener_columnas_valor_y_ultimo_anio(df_snowpark)
    
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Cadena Productiva'])
        return (df_vacio, df_vacio.copy())
    
    # Crear lista de agregaciones
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
    
    # Agrupar y agregar
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"Cadena"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )
    
    # Convertir a pandas
    df_resumen_cadenas = df_resumen_snowpark.to_pandas()
    
    # Eliminar Valor FOB de los nombres de las columnas
    df_resumen_cadenas.columns = [col.replace('Valor FOB ', '') for col in df_resumen_cadenas.columns]
    
    # Cambiar nombre de la columna de agrupación
    df_resumen_cadenas = df_resumen_cadenas.rename(columns={'Cadena': 'Cadena Productiva'})
    
    # Aplicar formato
    df_resumen_cadenas_formateado = aplicar_formato_columnas(df_resumen_cadenas)
    
    return df_resumen_cadenas, df_resumen_cadenas_formateado

def resumen_por_tamano(df_snowpark):
    """
    Retorna: (df_resumen_tamano, df_resumen_tamano_formateado)
    """
    # Obtener columnas de valor y último año
    valor_columns, last_year, last_year_col_original = obtener_columnas_valor_y_ultimo_anio(df_snowpark)
    
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Tamaño de la Empresa'])
        return (df_vacio, df_vacio.copy())
    
    # Crear lista de agregaciones
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
    
    # Agrupar y agregar
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"Tamaño de la Empresa"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )
    
    # Convertir a pandas
    df_resumen_tamano = df_resumen_snowpark.to_pandas()
    
    # Eliminar Valor FOB de los nombres de las columnas
    df_resumen_tamano.columns = [col.replace('Valor FOB ', '') for col in df_resumen_tamano.columns]
    
    # Aplicar formato
    df_resumen_tamano_formateado = aplicar_formato_columnas(df_resumen_tamano)
    
    return df_resumen_tamano, df_resumen_tamano_formateado

def resumen_por_pais(df_snowpark):
    """
    Retorna: (df_resumen_pais, df_resumen_pais_formateado)
    """
    # Obtener columnas de valor y último año
    valor_columns, last_year, last_year_col_original = obtener_columnas_valor_y_ultimo_anio(df_snowpark)
    
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['País'])
        return (df_vacio, df_vacio.copy())
    
    # Crear lista de agregaciones
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
    
    # Agrupar y agregar
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"País de Destino Final"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )
    
    # Convertir a pandas
    df_resumen_pais = df_resumen_snowpark.to_pandas()
    
    # Eliminar Valor FOB de los nombres de las columnas
    df_resumen_pais.columns = [col.replace('Valor FOB ', '') for col in df_resumen_pais.columns]
    
    # Cambiar nombre de la columna de agrupación
    df_resumen_pais = df_resumen_pais.rename(columns={'País de Destino Final': 'País'})
    
    # Aplicar formato
    df_resumen_pais_formateado = aplicar_formato_columnas(df_resumen_pais)
    
    return df_resumen_pais, df_resumen_pais_formateado

def resumen_por_pais_tamano(df_snowpark):
    """
    Retorna: (df_resumen_pais_tamano, df_resumen_pais_tamano_formateado)
    """
    # Obtener columnas de valor y último año
    valor_columns, last_year, last_year_col_original = obtener_columnas_valor_y_ultimo_anio(df_snowpark)
    
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['País', 'Tamaño de la Empresa'])
        return (df_vacio, df_vacio.copy())
    
    # Crear lista de agregaciones
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
    
    # Agrupar y agregar
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"País de Destino Final"'), col('"Tamaño de la Empresa"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )
    
    # Convertir a pandas
    df_resumen_pais_tamano = df_resumen_snowpark.to_pandas()
    
    # Eliminar Valor FOB de los nombres de las columnas
    df_resumen_pais_tamano.columns = [col.replace('Valor FOB ', '') for col in df_resumen_pais_tamano.columns]
    
    # Cambiar nombre de la columna de agrupación
    df_resumen_pais_tamano = df_resumen_pais_tamano.rename(columns={'País de Destino Final': 'País'})
    
    # Aplicar formato
    df_resumen_pais_tamano_formateado = aplicar_formato_columnas(df_resumen_pais_tamano)
    
    return df_resumen_pais_tamano, df_resumen_pais_tamano_formateado

def resumen_por_razon_social(df_snowpark):
    """
    Retorna: (df_resumen_empresas, df_resumen_empresas_formateado)
    """
    # Obtener columnas de valor y último año
    valor_columns, last_year, last_year_col_original = obtener_columnas_valor_y_ultimo_anio(df_snowpark)
    
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Razón Social'])
        return (df_vacio, df_vacio.copy())
    
    # Crear lista de agregaciones
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
    
    # Agrupar y agregar
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"Razón Social"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )
    
    # Convertir a pandas
    df_resumen_empresas = df_resumen_snowpark.to_pandas()
    
    # Eliminar Valor FOB de los nombres de las columnas
    df_resumen_empresas.columns = [col.replace('Valor FOB ', '') for col in df_resumen_empresas.columns]
    
    # Aplicar formato
    df_resumen_empresas_formateado = aplicar_formato_columnas(df_resumen_empresas)
    
    return df_resumen_empresas, df_resumen_empresas_formateado

def conteo_empresas_exportadoras(df_snowpark):
    """
    Retorna: (df_resumen_empresas_conteo, df_resumen_empresas_conteo_formateado)
    """
    valor_columns = [c for c in df_snowpark.columns if 'Valor FOB USD ' in c]

    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['País', 'Empresas'])
        return (df_vacio, df_vacio.copy())

    # Último año cerrado disponible (excluye corridos que contienen 'Enero')
    closed_columns = [c for c in valor_columns if 'Enero' not in c]
    last_closed_col = max(closed_columns, key=lambda c: int(re.findall(r'\d{4}', c)[0]))

    # Crear lista de agregaciones
    agg_list = [count_distinct('NIT').alias('Empresas')]

    # Filtrar solo empresas con exportaciones > 0 en el último año cerrado, luego agrupar
    df_resumen_snowpark = (
        df_snowpark
        .filter(col(last_closed_col) > 0)
        .groupBy(col('"País de Destino Final"'))
        .agg(*agg_list)
    )
    
    # Convertir a pandas
    df_resumen_empresas_conteo = df_resumen_snowpark.to_pandas()
    
    # Cambiar nombre de la columna de agrupación
    df_resumen_empresas_conteo = df_resumen_empresas_conteo.rename(columns={'País de Destino Final': 'País', 'EMPRESAS': 'Empresas'})
    
    # Ordenar de mayor a menor por número de empresas
    df_resumen_empresas_conteo = df_resumen_empresas_conteo.sort_values(by='Empresas', ascending=False)
    
    # Aplicar formato
    df_resumen_empresas_conteo_formateado = aplicar_formato_columnas(df_resumen_empresas_conteo)
    
    return df_resumen_empresas_conteo, df_resumen_empresas_conteo_formateado


# ==================== FUNCIONES PARA GENERAR GRÁFICOS ===================

def grafico_barras_multiples(df, df_formateado, columna_agrupacion='Cadena Productiva',
                            orientacion='horizontal', nombre_eje_categorias=None, list_color=None):
    """
    Crea un gráfico de barras agrupadas (horizontal o vertical) con valores formateados como etiquetas
    
    Parámetros:
    -----------
    df : DataFrame
        DataFrame con valores numéricos originales
    df_formateado : DataFrame
        DataFrame con valores formateados para mostrar como etiquetas
    columna_agrupacion : str
        Nombre de la columna de agrupación (default: 'Cadena Productiva')
    orientacion : str
        'horizontal' o 'vertical' (default: 'horizontal')
    nombre_eje_categorias : str
        Etiqueta para el eje de categorías (si es None, usa el nombre de columna_agrupacion)
    list_color : list
        Lista de colores para las barras
    """

    try:
    
        # Colores por defecto si no se proporcionan
        if list_color is None:
            list_color = ["#343363", "#1a3a79", "#2f55c8", "#4a79f3", "#829df5"]
        
        # Usar nombre de columna de agrupación si no se especifica nombre_eje_categorias
        if nombre_eje_categorias is None:
            nombre_eje_categorias = columna_agrupacion
        
        # Identificar columnas de valor (todas las que tienen 'USD')
        valor_columns = [c for c in df.columns if c != columna_agrupacion and 'USD' in c]
        
        if not valor_columns:
            print("No se encontraron columnas de valor")
            return None
        
        # Obtener categorías
        categorias = df[columna_agrupacion].values
        
        # Crear el gráfico
        fig = go.Figure()
        
        # Determinar si es horizontal o vertical
        es_horizontal = orientacion.lower() == 'horizontal'
        
        # Agregar una traza por cada período
        for i, col in enumerate(valor_columns):
            valores = df[col].values
            valores_formateados = df_formateado[col].values
            
            # Limpiar el nombre de la serie (quitar 'USD ')
            nombre_serie = col.replace('USD ', '')
            
            if es_horizontal:
                fig.add_trace(go.Bar(
                    name=nombre_serie,
                    y=categorias,
                    x=valores,
                    orientation='h',
                    text=valores_formateados,
                    textposition='outside',
                    textfont=dict(size=20), # CAMBIO: Tamaño valores etiquetas a 20
                    textangle=0,  # Siempre horizontal
                    marker_color=list_color[i % len(list_color)],
                    hovertemplate='<b>%{y}</b><br>' +
                                f'{nombre_serie}: %{{text}}<br>' +
                                '<extra></extra>'
                ))
            else:
                fig.add_trace(go.Bar(
                    name=nombre_serie,
                    x=categorias,
                    y=valores,
                    text=valores_formateados,
                    textposition='outside',
                    textfont=dict(size=20), # CAMBIO: Tamaño valores etiquetas a 20
                    textangle=0,  # Siempre horizontal
                    marker_color=list_color[i % len(list_color)],
                    hovertemplate='<b>%{x}</b><br>' +
                                f'{nombre_serie}: %{{text}}<br>' +
                                '<extra></extra>'
                ))
        
        # Configurar el layout según la orientación
        if es_horizontal:
            fig.update_layout(
                xaxis_title=None,  # Eliminar título del eje X (valores)
                yaxis_title=nombre_eje_categorias,
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center", # CAMBIO: Centrar la leyenda
                    x=0.5,            # CAMBIO: Posición X en el centro
                    font=dict(size=15) # CAMBIO: Tamaño de fuente leyenda a 15
                ),
                margin=dict(l=20, r=150, t=60, b=40),
                height=max(500, len(categorias) * 100),  # Altura dinámica para horizontal
                plot_bgcolor='white',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=0.5,
                    zeroline=True,
                    zerolinecolor='gray',
                    zerolinewidth=1,
                    showticklabels=False,  # Ocultar etiquetas del eje X
                    showline=False,  # Ocultar línea del eje X
                ),
                yaxis=dict(
                    showgrid=False,
                    autorange='reversed', # Primera categoría arriba
                    tickfont=dict(size=15),   # CAMBIO: Tamaño texto categorías a 20
                    title_font=dict(size=12)  # CAMBIO: Tamaño nombre del eje a 15
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=20,
                    font_family="Arial"
                )
            )
        else:
            fig.update_layout(
                xaxis_title=nombre_eje_categorias,
                yaxis_title=None,  # Eliminar título del eje Y (valores)
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center", # CAMBIO: Centrar la leyenda
                    x=0.5,            # CAMBIO: Posición X en el centro
                    font=dict(size=15) # CAMBIO: Tamaño de fuente leyenda a 15
                ),
                margin=dict(l=40, r=40, t=60, b=100),
                height=600,
                plot_bgcolor='white',
                yaxis=dict(
                    showgrid=True,
                    gridcolor='lightgray',
                    gridwidth=0.5,
                    zeroline=True,
                    zerolinecolor='gray',
                    zerolinewidth=1,
                    showticklabels=False,  # Ocultar etiquetas del eje Y
                    showline=False,  # Ocultar línea del eje Y
                ),
                xaxis=dict(
                    showgrid=False,
                    tickangle=-45 if len(categorias[0]) > 15 else 0,
                    tickfont=dict(size=15),   # CAMBIO: Tamaño texto categorías a 20
                    title_font=dict(size=12)  # CAMBIO: Tamaño nombre del eje a 15
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=20,
                    font_family="Arial"
                )
            )
        
        # Ajustar el espaciado entre grupos de barras
        fig.update_layout(
            bargap=0.15,      # Espacio entre grupos
            bargroupgap=0.1   # Espacio entre barras del mismo grupo
        )
        
        return fig
    
    except Exception as e:
        # Manejo de excepciones y retorno de un mensaje de error
        return f"Error generando el gráfico: {e}"

# Función simplificada para mostrar solo años específicos
def grafico_barras_periodos_seleccionados(df, df_formateado, columna_agrupacion='Cadena Productiva',
                                         periodos_a_mostrar=None, orientacion='horizontal',
                                         nombre_eje_categorias=None, list_color=None):
    """
    Versión que permite seleccionar qué períodos mostrar
    
    Parámetros:
    -----------
    df : DataFrame
        DataFrame con valores numéricos originales
    df_formateado : DataFrame
        DataFrame con valores formateados para mostrar como etiquetas
    columna_agrupacion : str
        Nombre de la columna de agrupación (default: 'Cadena Productiva')
    periodos_a_mostrar : list
        Lista de columnas de períodos a mostrar (ej: ['USD 2023', 'USD 2024'])
    orientacion : str
        'horizontal' o 'vertical' (default: 'horizontal')
    nombre_eje_categorias : str
        Etiqueta para el eje de categorías (si es None, usa el nombre de columna_agrupacion)
    list_color : list
        Lista de colores para las barras
    """
    
    # Si se especifican períodos, filtrar el DataFrame
    if periodos_a_mostrar:
        columnas_seleccionadas = [columna_agrupacion] + periodos_a_mostrar
        df_filtrado = df[columnas_seleccionadas]
        df_formateado_filtrado = df_formateado[columnas_seleccionadas]
    else:
        df_filtrado = df
        df_formateado_filtrado = df_formateado
    
    return grafico_barras_multiples(
        df=df_filtrado,
        df_formateado=df_formateado_filtrado,
        columna_agrupacion=columna_agrupacion,
        orientacion=orientacion,
        nombre_eje_categorias=nombre_eje_categorias,
        list_color=list_color
    )