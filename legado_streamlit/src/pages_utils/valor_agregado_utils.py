# Librerías
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import textwrap
from.utils import format_espanol, milify
from snowflake.snowpark.functions import count_distinct, sum as snow_sum, col
from src.pages_utils.utils import descarga_tabla, mostrar_resultado_en_streamlit
import re

# ==================== PARÁMETROS PARA PÁGINA VALOR AGREGADO ===================

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
                    'SUBSECTOR_BIENES',
                    'COD_POSICION_ARANCELARIA_BIENES',
                    'DESC_POSICION_ARANCELARIA_BIENES',
                    'VALOR_AGREGADO_EXPO_BIENES',
                    'TAMANO_TEJIDO'
]

dict_filtros_bienes = {'CADENA_BIENES' : f'Cadena de segmentación {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'SECTOR_BIENES' : f'Sector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'SUBSECTOR_BIENES' : f'Subsector exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'COD_POSICION_ARANCELARIA_BIENES' : f'Código de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'DESC_POSICION_ARANCELARIA_BIENES' : f'Descripción de posición arancelaria exportaciones {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'HUB_BIENES' : f'HUB de destino {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'PAIS_DESTINO_BIENES' : f'País de destino {exportaciones_bienes_servicios_anios_disponibles[0]} - {exportaciones_bienes_servicios_anios_disponibles[1]}',
                        'VALOR_AGREGADO_EXPO_BIENES' : 'Valor agregado exportaciones',
                        'TAMANO_TEJIDO' : 'Tamaño empresa'
}

# ==================== DICCIONARIO DE COLUMNAS PARA LA CONSULTA DE RESULTADOS ===================

dict_query_bienes = {'TAMANO_TEJIDO': 'Tamaño de la Empresa',
    'VALOR_AGREGADO_EXPO_BIENES': 'Valor Agregado Exportaciones', 
    'DEPARTAMENTO_BIENES': 'Departamento Origen',
    'POSICION_ARANCELARIA_COMPLETA_BIENES': 'Posición Arancelaria'} | COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA

# ==================== LISTA DE COLUMNAS PARA MOSTRAR AL USUARIO ===================

# Deben ser iguales a los elementos del AS en el diccionario anterior

ls_columnas_usuario_bienes = ['Tamaño de la Empresa',
    'Valor Agregado Exportaciones',
    'Departamento Origen',
    'Posición Arancelaria'].append(COLS_VARIABLES_USUARIOS_COLS_VARIABLES_BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P_DESTINOS_VA)

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
def aplicar_formato_columnas(df):
    """
    Función auxiliar para aplicar formato a las columnas (USD y Empresas)
    """
    df_formateado = df.copy()
    
    for col_name in df_formateado.columns:
        if "USD" in col_name:
            df_formateado[col_name] = df_formateado[col_name].apply(lambda x: milify(x))
        elif 'Empresas' in col_name:
            df_formateado[col_name] = df_formateado[col_name].apply(lambda x: format_espanol(x, decimales=0))
    
    return df_formateado

def resumen_valor_agregado(df_snowpark, periodos_cerrados, periodos_corridos):
    """
    Procesa el DataFrame de Snowpark para generar resúmenes de Valor Agregado.
    
    Retorna 6 DataFrames individuales en este orden:
    df_cerrado, df_cerrado_fmt, df_corrido, df_corrido_fmt, df_total, df_total_fmt
    """
    
    # 1. Identificar columnas de valor FOB USD
    valor_columns = [c for c in df_snowpark.columns if 'Valor FOB USD ' in c]
    
    # Manejo de caso vacío
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Valor agregado'])
        # Retornamos estructura vacía consistente (6 dataframes)
        return df_vacio, df_vacio.copy(), df_vacio, df_vacio.copy(), df_vacio, df_vacio.copy()

    # 2. Columna más reciente: año más alto; corridos (contienen 'Enero') tienen prioridad sobre año cerrado
    last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))

    # 3. Agregación en Snowpark
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]

    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"Valor Agregado Exportaciones"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )

    # 4. Conversión a Pandas y limpieza inicial
    df_total = df_resumen_snowpark.to_pandas()
    
    # Renombrar columnas (quitar 'Valor FOB ' y renombrar agrupación)
    df_total.columns = [col.replace('Valor FOB ', '') for col in df_total.columns]
    df_total = df_total.rename(columns={'Valor Agregado Exportaciones': 'Valor agregado'})

    # 5. Procesamiento Periodos Cerrados
    df_cerrado = df_total[['Valor agregado'] + periodos_cerrados].copy()
    if periodos_cerrados:
        df_cerrado = df_cerrado.sort_values(by=periodos_cerrados[-1], ascending=False)
    
    # 6. Procesamiento Periodos Corridos
    df_corrido = df_total[['Valor agregado'] + periodos_corridos].copy()
    if periodos_corridos:
        df_corrido = df_corrido.sort_values(by=periodos_corridos[-1], ascending=False)

    # 7. Aplicación de formatos (Reutilizando la función auxiliar)
    df_cerrado_fmt = aplicar_formato_columnas(df_cerrado)
    df_corrido_fmt = aplicar_formato_columnas(df_corrido)
    df_total_fmt = aplicar_formato_columnas(df_total)

    # Retornar los 6 DataFrames individuales
    return df_cerrado, df_cerrado_fmt, df_corrido, df_corrido_fmt, df_total, df_total_fmt

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

        # Obtener categorías aplicando textwrap para dividir en múltiples líneas
        # width=45 indica el máximo de caracteres por línea antes de hacer el salto (<br>)
        categorias = ['<br>'.join(textwrap.wrap(str(cat), width=45)) for cat in df[columna_agrupacion].values]
        
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

def top_partidas_por_categoria(df_snowpark, periodos_cerrados, periodos_corridos, categoria_valor):
    """
    Genera el top 10 de partidas arancelarias para una categoría específica de valor agregado.
    
    Parámetros:
    - df_snowpark: DataFrame de Snowpark
    - periodos_cerrados: Lista de columnas de años cerrados
    - periodos_corridos: Lista de columnas de periodos corridos
    - categoria_valor: String con la categoría a filtrar (ej: 'Manufactura de alta tecnología')
    
    Retorna 6 DataFrames individuales:
    df_cerrado, df_cerrado_fmt, df_corrido, df_corrido_fmt, df_total, df_total_fmt
    """
    
    # 1. Identificar columnas de valor FOB USD
    valor_columns = [c for c in df_snowpark.columns if 'Valor FOB USD ' in c]
    
    # Manejo de caso vacío
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Posición Arancelaria'])
        return df_vacio, df_vacio.copy(), df_vacio, df_vacio.copy(), df_vacio, df_vacio.copy()

    # 2. Determinar la columna del período más reciente (corrido > cerrado para el mismo año)
    last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))

    # 3. Agregación en Snowpark con filtro por categoría y límite
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]

    df_resumen_snowpark = (
        df_snowpark
        .filter(col('"Valor Agregado Exportaciones"') == categoria_valor)  # Filtro dinámico
        .groupBy(col('"Posición Arancelaria"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
        .limit(10)
    )

    # 4. Conversión a Pandas y limpieza inicial
    df_total = df_resumen_snowpark.to_pandas()
    
    # Renombrar columnas (quitar 'Valor FOB ')
    df_total.columns = [col.replace('Valor FOB ', '') for col in df_total.columns]
    
    # 5. Procesamiento Periodos Cerrados
    df_cerrado = df_total[['Posición Arancelaria'] + periodos_cerrados].copy()
    if periodos_cerrados:
        df_cerrado = df_cerrado.sort_values(by=periodos_cerrados[-1], ascending=False)
    
    # 6. Procesamiento Periodos Corridos
    df_corrido = df_total[['Posición Arancelaria'] + periodos_corridos].copy()
    if periodos_corridos:
        df_corrido = df_corrido.sort_values(by=periodos_corridos[-1], ascending=False)

    # 7. Aplicación de formatos (Reutilizando la función auxiliar)
    df_cerrado_fmt = aplicar_formato_columnas(df_cerrado)
    df_corrido_fmt = aplicar_formato_columnas(df_corrido)
    df_total_fmt = aplicar_formato_columnas(df_total)

    # Retornar los 6 DataFrames individuales
    return df_cerrado, df_cerrado_fmt, df_corrido, df_corrido_fmt, df_total, df_total_fmt

def top_partidas_por_departamento(df_snowpark, periodos_cerrados, periodos_corridos, categoria_valor):
    """
    Genera la distribución por departamento para una categoría específica de valor agregado.
    
    Parámetros:
    - df_snowpark: DataFrame de Snowpark
    - periodos_cerrados: Lista de columnas de años cerrados
    - periodos_corridos: Lista de columnas de periodos corridos
    - categoria_valor: String con la categoría a filtrar (ej: 'Manufactura de alta tecnología')
    
    Retorna 6 DataFrames individuales:
    df_cerrado, df_cerrado_fmt, df_corrido, df_corrido_fmt, df_total, df_total_fmt
    """
    
    # 1. Identificar columnas de valor FOB USD
    valor_columns = [c for c in df_snowpark.columns if 'Valor FOB USD ' in c]
    
    # Manejo de caso vacío
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Departamento Origen'])
        return df_vacio, df_vacio.copy(), df_vacio, df_vacio.copy(), df_vacio, df_vacio.copy()

    # 2. Determinar la columna del período más reciente (corrido > cerrado para el mismo año)
    last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))

    # 3. Agregación en Snowpark con filtro por categoría y límite
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]

    df_resumen_snowpark = (
        df_snowpark
        .filter(col('"Valor Agregado Exportaciones"') == categoria_valor)  # Filtro dinámico
        .groupBy(col('"Departamento Origen"'))
        .agg(*agg_list)
        .orderBy(col(last_year_col_original).desc())
    )

    # 4. Conversión a Pandas y limpieza inicial
    df_total = df_resumen_snowpark.to_pandas()

    # 5. Cambiar nombre de columna de agrupación
    df_total = df_total.rename(columns={'Departamento Origen': 'Departamento'})
    
    # 6. Renombrar columnas (quitar 'Valor FOB ')
    df_total.columns = [col.replace('Valor FOB ', '') for col in df_total.columns]
    
    # 7. Procesamiento Periodos Cerrados
    df_cerrado = df_total[['Departamento'] + periodos_cerrados].copy()
    if periodos_cerrados:
        df_cerrado = df_cerrado.sort_values(by=periodos_cerrados[-1], ascending=False)
    
    # 8. Procesamiento Periodos Corridos
    df_corrido = df_total[['Departamento'] + periodos_corridos].copy()
    if periodos_corridos:
        df_corrido = df_corrido.sort_values(by=periodos_corridos[-1], ascending=False)

    # 9. Aplicación de formatos (Reutilizando la función auxiliar)
    df_cerrado_fmt = aplicar_formato_columnas(df_cerrado)
    df_corrido_fmt = aplicar_formato_columnas(df_corrido)
    df_total_fmt = aplicar_formato_columnas(df_total)

    # Retornar los 6 DataFrames individuales
    return df_cerrado, df_cerrado_fmt, df_corrido, df_corrido_fmt, df_total, df_total_fmt

def conteo_partidas_periodo(df_snowpark, periodo):
    """
    Realiza el conteo de partidas arancelarias con movimientos (>0) 
    por Departamento y Tipo de Valor Agregado para un periodo específico.
    
    Retorna una tabla pivoteada con:
    - Fila: Departamento
    - Columnas: Categorías de Valor Agregado + Columna 'Total'
    - Ordenada de mayor a menor por 'Total'
    """
    
    # 1. Identificar la columna de valor específica basada en el periodo
    p_busqueda = periodo[0]
    valor_columns = [
        c for c in df_snowpark.columns 
        if f'Valor FOB {p_busqueda}' in c.replace('"', '') 
    ]
    
    # 2. Manejo de caso vacío
    if not valor_columns:
        return pd.DataFrame(columns=['Departamento', 'Total'])

    target_col = valor_columns[0]

    # 3. Consultar Snowpark (Agrupar y Contar)
    agg_list = [count_distinct(col('"Posición Arancelaria"')).alias('Productos')]
    
    df_resumen_snowpark = (
        df_snowpark
        .filter(col(target_col) > 0)
        .groupBy(col('"Valor Agregado Exportaciones"'), col('"Departamento Origen"'))
        .agg(*agg_list)
    )

    # 4. Convertir a Pandas
    df_temp = df_resumen_snowpark.to_pandas()

    # 5. Renombrar columnas para estandarizar
    df_temp = df_temp.rename(columns={
        'Valor Agregado Exportaciones': 'Valor agregado',
        'Departamento Origen': 'Departamento',
        'PRODUCTOS': 'Productos'
    })

    # 6. Pivotar la tabla
    df_pivot = df_temp.pivot(index='Departamento', columns='Valor agregado', values='Productos')

    # 7. Limpieza y conversión a enteros
    df_pivot = df_pivot.fillna(0).astype(int)
    
    # 8. Calcular Total y Ordenar
    # axis=1 suma los valores de todas las columnas (categorías) para cada fila (departamento)
    df_pivot['Total de productos'] = df_pivot.sum(axis=1)
    
    # Ordenar descendente por el Total
    df_pivot = df_pivot.sort_values(by='Total de productos', ascending=False)
    
    # 9. Resetear índice y limpieza final
    df_pivot.reset_index(inplace=True)
    df_pivot.columns.name = None
    
    return df_pivot

def valor_exportado_departamento_periodo(df_snowpark, periodo):
    """
    Calcula la suma del valor exportado (FOB USD) por Departamento y Tipo de Valor Agregado 
    para un periodo específico.
    Retorna el DataFrame original y una copia formateada para visualización.
    """
    
    # 1. Identificar la columna de valor específica basada en el periodo
    p_busqueda = periodo[0]
    valor_columns = [
        c for c in df_snowpark.columns 
        if f'Valor FOB {p_busqueda}' in c.replace('"', '') 
    ]
    
    # 2. Manejo de caso vacío
    if not valor_columns:
        df_vacio = pd.DataFrame(columns=['Departamento', 'Total'])
        return df_vacio, df_vacio.copy()

    target_col = valor_columns[0]

    # 3. Consultar Snowpark (Agrupar y Sumar el valor)
    agg_list = [snow_sum(col(target_col)).alias('Valor FOB')]
    
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"Valor Agregado Exportaciones"'), col('"Departamento Origen"'))
        .agg(*agg_list)
    )

    # 4. Convertir a Pandas
    df_temp = df_resumen_snowpark.to_pandas()

    # 5. Renombrar columnas para estandarizar
    df_temp = df_temp.rename(columns=lambda x: x.upper())
    df_temp = df_temp.rename(columns={
        'VALOR AGREGADO EXPORTACIONES': 'Valor agregado',
        'DEPARTAMENTO ORIGEN': 'Departamento',
        'VALOR FOB': 'Valor FOB'
    })

    # 6. Pivotar la tabla
    df_pivot = df_temp.pivot(index='Departamento', columns='Valor agregado', values='Valor FOB')

    # 7. Limpieza y manejo de nulos
    df_pivot = df_pivot.fillna(0)
    
    # 8. Calcular Total y Ordenar
    df_pivot['Total valor exportado'] = df_pivot.sum(axis=1)
    df_pivot = df_pivot.sort_values(by='Total valor exportado', ascending=False)
    
    # 9. Resetear índice
    df_pivot.reset_index(inplace=True)
    df_pivot.columns.name = None
    
    # 10. Crear la versión formateada (aplicar milify a todo menos a 'Departamento')
    df_pivot_fmt = df_pivot.copy()
    for col_name in df_pivot_fmt.columns:
        if col_name != 'Departamento':
            df_pivot_fmt[col_name] = df_pivot_fmt[col_name].apply(lambda x: milify(x))

    return df_pivot, df_pivot_fmt

def valor_exportado_departamento_long(df_snowpark):
    """
    Calcula la suma del valor exportado (FOB USD) por Departamento y Tipo de Valor Agregado 
    para todos los años disponibles, retornando el resultado en formato long (despivotado).
    """
    # 1. Identificar TODAS las columnas de valor FOB USD disponibles
    valor_columns = [c for c in df_snowpark.columns if 'Valor FOB USD ' in c.replace('"', '')]
    
    if not valor_columns:
        return pd.DataFrame(columns=['Departamento', 'Valor agregado', 'Año', 'Valor FOB USD'])

    # 2. Consultar Snowpark (Agrupar y Sumar todos los años detectados)
    agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
    
    df_resumen_snowpark = (
        df_snowpark
        .groupBy(col('"Valor Agregado Exportaciones"'), col('"Departamento Origen"'))
        .agg(*agg_list)
    )

    # 3. Convertir a Pandas
    df_temp = df_resumen_snowpark.to_pandas()

    # 4. Limpiar nombres de columnas para estandarizar
    df_temp.columns = [c.replace('"', '').strip() for c in df_temp.columns]
    df_temp = df_temp.rename(columns=lambda x: x.upper())
    
    df_temp = df_temp.rename(columns={
        'VALOR AGREGADO EXPORTACIONES': 'Valor agregado',
        'DEPARTAMENTO ORIGEN': 'Departamento'
    })

    # Identificar las columnas de valor exactas después del renombre
    val_cols_renamed = [c for c in df_temp.columns if 'VALOR FOB USD' in c]

    # 5. Transformar a formato Long usando pd.melt
    df_long = pd.melt(
        df_temp, 
        id_vars=['Departamento', 'Valor agregado'], 
        value_vars=val_cols_renamed,
        var_name='Año', 
        value_name='Valor FOB USD'
    )

    # 6. Limpiar prefijo de la columna 'Año' preservando la distinción año cerrado vs corrido
    # Ej: 'VALOR FOB USD 2025' -> '2025', 'VALOR FOB USD ENERO 2025' -> 'ENERO 2025'
    df_long['Año'] = df_long['Año'].apply(
        lambda x: x.replace('VALOR FOB USD ', '').strip() if pd.notnull(x) else x
    )

    # 7. Filtrar filas con valor 0 para no generar un archivo pesado con vacíos
    df_long = df_long[df_long['Valor FOB USD'] > 0]

    # 8. Ordenar los datos
    df_long = df_long.sort_values(by=['Departamento', 'Valor agregado', 'Año'])
    df_long.reset_index(drop=True, inplace=True)

    return df_long

# ==================== FUNCIÓN DE CONTENEDORES ===================

def renderizar_seccion_valor_agregado(
    # 1. Contenido Visual
    titulo_seccion: str,
    titulos_tabs: list,
    fuente_datos: str,
    
    # 2. Llaves de Session State de obejtos
    key_fig_cerrado: str,
    key_fig_corrido: str,
    key_df_formato: str,
    key_df_download: str,
    
    # 3. Llaves para Widgets (Streamlit Keys únicas)
    widget_key_graph_cerrado: str,
    widget_key_graph_corrido: str,
    widget_key_boton_descarga: str,
    
    # 4. Parámetros de Descarga y Analítica
    nombre_archivo_descarga: str,
    evento_analitica: str,
    filtros_json,

    # 5. Parámetro de disponibilidad de datos de año corrido
    disponibilidad_periodos_corridos_usd: str
):
    """
    Genera el contenedor estándar de gráficos y tablas para la sección de Valor Agregado.
    Recibe parámetros explícitos tipo string para las llaves de session_state.
    """
    
    with st.container(height=850, border=True):

        # Título
        st.markdown(f'<h6 class="custom-header" style="text-align:center;">{titulo_seccion}</h6>', unsafe_allow_html=True)

        # Crear pestañas
        if disponibilidad_periodos_corridos_usd == 'Si':
            tab1, tab2, tab3 = st.tabs(titulos_tabs)
        else:
            tab1, tab3 = st.tabs([titulos_tabs[0], titulos_tabs[2]])

        # --- Pestaña 1: Año cerrado ---
        with tab1:
            if key_fig_cerrado in st.session_state and not st.session_state[key_df_formato].empty:
                mostrar_resultado_en_streamlit(
                    resultado=st.session_state[key_fig_cerrado], 
                    fuente=fuente_datos, 
                    llave=widget_key_graph_cerrado
                )
                # Nota
                st.caption('**Nota:** M (millones).')
            else:
                st.error("No se encontro información que cumpla con los filtros seleccionados.")

        # --- Pestaña 2: Año corrido ---
        if disponibilidad_periodos_corridos_usd == 'Si':
            with tab2:
                if key_fig_corrido in st.session_state and not st.session_state[key_df_formato].empty:
                    mostrar_resultado_en_streamlit(
                        resultado=st.session_state[key_fig_corrido], 
                        fuente=fuente_datos, 
                        llave=widget_key_graph_corrido
                    )
                    # Nota
                    st.caption('**Nota:** M (millones).')
                else:
                    st.error("No se encontro información que cumpla con los filtros seleccionados.")

        # --- Pestaña 3: Tablas de datos ---
        with tab3:
            if key_df_formato in st.session_state and not st.session_state[key_df_formato].empty:
                st.dataframe(
                    st.session_state[key_df_formato], 
                    use_container_width=True, 
                    hide_index=True
                )
                # Nota
                st.caption('**Nota:** M (millones).')
            else:
                st.error("No se encontro información que cumpla con los filtros seleccionados.")

    # --- Botón de descarga ---
    with st.container(height = 75, border=True):                        
        # Verificación de seguridad antes de intentar renderizar el botón
        if key_df_download in st.session_state and not st.session_state[key_df_download].empty:
            descarga_tabla(
                df=st.session_state[key_df_download],
                row_threshhold=1500,
                label_descarga="Descargar resultados",
                file_name=nombre_archivo_descarga,
                key_descarga=widget_key_boton_descarga,
                sesion_activa=st.session_state.session,
                tipo_evento=f"Descarga gráfico - {evento_analitica}",
                pagina="Valor agregado",
                filtros=filtros_json,
                nota = "Los valores están en dólares FOB",
                agregar_nota = True
            )
        else:
            st.markdown("No hay datos disponibles para descargar.")