# Librerías
from snowflake.snowpark.functions import count_distinct, sum as snow_sum, col
import re
import pandas as pd
from src.pages_utils.utils import milify, format_espanol

# ==================== PARÁMETROS PARA PÁGINA EMPRESAS ===================

from .config import (
    exportaciones_anios_disponibles,
    servicios_anios_disponibles,
    negocios_anios_disponibles,
    COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS,
    COLS_VARIABLES_USUARIO_COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS
)

# ==================== LISTA DE COLUMNAS Y DICCIONARIO DE NOMBRES PARA FILTROS ===================

ls_filtros_generales_empresas = [
                                 'MENOR_200K_HABITANTES',
                                 'PDET',
                                 'DEPARTAMENTO',
                                 'MUNICIPIO',
                                 'TAMANO',
                                 'CADENA_SEGMENTACION',
                                 'TRAYECTORIA_EXPORTADORA',
                                 'COD_CIIU_1',
                                 'DESCRIPCION_CIIU_1',
                                 'POTENCIAL_ATENCION',
                                 'VALOR_AGREGADO_CIIU_1',
                                 'ATENDIDA_PC',
                                 'SERVICIOS',
                                 'NEGOCIOS',
                                 'RANGO_ANTIGUEDAD',
                                 'RANGO_INGRESOS',
                                 'HA_EXPORTADO']

dict_filtros_generales_empresas = {'MENOR_200K_HABITANTES' : 'Ubicación del HQ en municipio menor 200k habitantes',
                                 'PDET' : 'Ubicación del HQ en municipio PDET',
                                 'DEPARTAMENTO' : 'Departamento de la ubicación del HQ',
                                 'MUNICIPIO' : 'Municipio de la ubicación del HQ',
                                 'TAMANO' : 'Tamaño empresa',
                                 'CADENA_SEGMENTACION' : 'Cadena de segmentación',
                                 'TRAYECTORIA_EXPORTADORA' : 'Trayectoria exportadora',
                                 'COD_CIIU_1' : 'Código CIIU Rev 4 - Actividad principal',
                                 'DESCRIPCION_CIIU_1' : 'Descripción CIIU Rev 4 - Actividad principal',
                                 'VALOR_AGREGADO_CIIU_1' : 'Valor Agregado - Actividad principal',
                                 'POTENCIAL_ATENCION' : 'Potencial de atención',
                                 'ATENDIDA_PC' : f'Empresa atendida por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}',
                                 'SERVICIOS' : f'Servicios prestados por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}',
                                 'NEGOCIOS' : f'Negocios facilitados por ProColombia {negocios_anios_disponibles[0]} - {negocios_anios_disponibles[1]}',
                                 'RANGO_ANTIGUEDAD' : 'Antiguedad de la empresa (años)', 
                                 'RANGO_INGRESOS' : 'Ingreso operacional (COP)',
                                 'HA_EXPORTADO' : f'¿La empresa ha exportado {exportaciones_anios_disponibles[0]} - {exportaciones_anios_disponibles[1]}?'}

# ==================== DICCIONARIO DE COLUMNAS PARA LA CONSULTA DE RESULTADOS ===================

dict_query_empresas = {
    # Datos básicos
    'NIT': 'NIT',
    'RAZON_SOCIAL': 'Razón Social',
    'INVERSION_EXTRANJERA': 'Sucursal/Sociedad Extranjera',
    'TAMANO': 'Tamaño de la Empresa',
    # Exportaciones
    'CADENA': 'Cadena',
    'SECTOR': 'Sector',
    'SUBSECTOR': 'Subsector',
    # ProColombia
    'TRAYECTORIA_EXPORTADORA': 'Trayectoria Exportadora',
    'ATENDIDA_PC': 'Empresa atendida por ProColombia',
    # Segmentación
    'CADENA_SEGMENTACION': 'Cadena de Segmentación',
    'POTENCIAL_ATENCION': 'Potencial de Atención'} | COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS

# ==================== LISTA DE COLUMNAS PARA MOSTRAR AL USUARIO ===================

# Deben ser iguales a los elementos del AS en el diccionario anterior

ls_columnas_usuario_empresas = ['NIT',
    'Razón Social',
    'Sucursal/Sociedad Extranjera',
    'Cadena',
    'Sector',
    'Subsector',
    'Tamaño de la Empresa',
    'Trayectoria Exportadora',
    'Empresa atendida por ProColombia',
    'Cadena de Segmentación',
    'Potencial de Atención'].append(COLS_VARIABLES_USUARIO_COLS_VARIABLES_TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P_EMPRESAS)

# ==================== GENERADOR DE CONSULTA ===================

def query_data_empresas(
    dict_columnas: dict,
    filtros_generales: dict,
) -> str:
    """
    Devuelve una consulta SQL dinámica para la vista **Segmentación** en la página de Empresas.

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
        ``TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P`` (alias **A**).
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
        "TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P AS A\n"
        f"WHERE {filtros_A}\n"
    )

    return query

# ==================== GENERADORES DE DFs DE RESUMEN ===================

def calcular_metricas_resumen(_df_snowpark, servicios_anios_disponibles, negocios_anios_disponibles):
    """
    Calcula las métricas principales del tejido empresarial.
    
    Parámetros:
    -----------
    _df_snowpark : Snowpark DataFrame
        DataFrame de Snowpark con los datos de empresas
    servicios_anios_disponibles : list
        Lista de años disponibles para servicios
    negocios_anios_disponibles : list
        Lista de años disponibles para negocios
    
    Retorna:
    --------
    dict
        Tupla con las métricas: num_empresas, 
        num_empresas_servicios, num_empresas_negocios, num_empresas_potencial
    """

    try:
        # Verificar si hay datos
        if _df_snowpark.count() == 0:
            return (0, 0, 0, 0)
        
        # Número de empresas
        num_empresas = _df_snowpark.select(count_distinct('NIT', 'Razón Social')).to_pandas().iloc[0, 0]
        
        # Servicios
        num_empresas_servicios = _df_snowpark.filter(
            _df_snowpark[f'Servicios prestados por ProColombia {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}'] == 'Sí'
        ).select(count_distinct('NIT', 'Razón Social')).to_pandas().iloc[0, 0]
        
        # Negocios
        num_empresas_negocios = _df_snowpark.filter(
            _df_snowpark[f'Negocios facilitados por ProColombia {negocios_anios_disponibles[0]} - {negocios_anios_disponibles[1]}'] == 'Sí'
        ).select(count_distinct('NIT', 'Razón Social')).to_pandas().iloc[0, 0]
        
        # Empresas con potencial de atención Muy Alto y Alto
        num_empresas_potencial = _df_snowpark.filter(
            (_df_snowpark['Potencial de Atención'] == 'Muy alto') | 
            (_df_snowpark['Potencial de Atención'] == 'Alto')
        ).select(count_distinct('NIT', 'Razón Social')).to_pandas().iloc[0, 0]
        
        return (
            num_empresas,
            num_empresas_servicios,
            num_empresas_negocios,
            num_empresas_potencial
        )
    except Exception:
        return (0, 0, 0, 0)

def crear_resumen_por_tamano(_df_snowpark):
    """
    Crea tablas de resumen agrupadas por tamaño de empresa.
    
    Parámetros:
    -----------
    _df_snowpark : Snowpark DataFrame
        DataFrame de Snowpark con los datos de empresas

    Retorna:
    --------
    tuple
        (df_resumen_empresas, df_resumen_empresas_formateado)
    """
    try:
        # Identificar columnas de valor FOB USD
        valor_columns = [c for c in _df_snowpark.columns if 'Valor FOB USD ' in c]
        
        # Verificar que existan columnas de valor
        if not valor_columns:
            df_vacio = pd.DataFrame(columns=['Tamaño', 'Empresas'])
            return (df_vacio, df_vacio.copy())
        
        # Determinar la columna más reciente (año más alto; corridos tienen prioridad sobre año cerrado)
        last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))

        # Crear lista de agregaciones
        agg_list = [count_distinct('NIT', 'Razón Social').alias('Empresas')] + [snow_sum(col(c)).alias(c) for c in valor_columns]
        
        # Agrupar y agregar
        df_resumen_snowpark = (
            _df_snowpark
            .groupBy(col('Tamaño de la Empresa').alias('Tamaño'))
            .agg(*agg_list)
            .orderBy(col(last_year_col_original).desc())
        )
        
        # Convertir a pandas
        df_resumen_empresas = df_resumen_snowpark.to_pandas()
        
        # Verificar si está vacío
        if df_resumen_empresas.empty:
            df_vacio = pd.DataFrame(columns=['Tamaño', 'Empresas'] + [c.replace('Valor FOB ', '') for c in valor_columns])
            return (df_vacio, df_vacio.copy())
        
        # Renombrar columnas
        df_resumen_empresas = df_resumen_empresas.rename(columns={"EMPRESAS": 'Empresas'})
        
        # Eliminar Valor FOB de los nombres de las columnas
        df_resumen_empresas.columns = [col_name.replace('Valor FOB ', '') for col_name in df_resumen_empresas.columns]
        
        # Crear copia para aplicar formato
        df_resumen_empresas_formateado = df_resumen_empresas.copy()
        
        # Aplicar formato
        for col_name in df_resumen_empresas_formateado.columns:
            if "USD" in col_name:
                df_resumen_empresas_formateado[col_name] = df_resumen_empresas_formateado[col_name].apply(lambda x: milify(x))
            if 'Empresas' in col_name:
                df_resumen_empresas_formateado[col_name] = df_resumen_empresas_formateado[col_name].apply(lambda x: format_espanol(x, decimales=0))
        
        return (df_resumen_empresas, df_resumen_empresas_formateado)
    
    except Exception:
        df_vacio = pd.DataFrame(columns=['Tamaño', 'Empresas'])
        return (df_vacio, df_vacio.copy())

def crear_top_exportadoras(_df_snowpark, top_n=20):
    """    
    Crea tabla con las top N empresas exportadoras.
    
    Parámetros:
    -----------
    _df_snowpark : Snowpark DataFrame
        DataFrame de Snowpark con los datos de empresas
    top_n : int
        Número de empresas top a retornar (default: 20)
    
    Retorna:
    --------
    tuple
        (df_empresas_top_exportadoras_resumen, df_empresas_top_exportadoras_resumen_formateado)
    """
    try:
        # Identificar columnas de valor FOB USD
        valor_columns = [c for c in _df_snowpark.columns if 'Valor FOB USD ' in c]
        
        # Verificar que existan columnas de valor
        if not valor_columns:
            df_vacio = pd.DataFrame(columns=['NIT', 'Razón Social'])
            return (df_vacio, df_vacio.copy())
        
        # Determinar la columna más reciente (año más alto; corridos tienen prioridad sobre año cerrado)
        last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))

        # Crear lista de agregaciones
        agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]

        # Agrupar, agregar, filtrar y ordenar en Snowpark
        df_top_snowpark = (
            _df_snowpark
            .groupBy('NIT', 'Razón Social')
            .agg(*agg_list)
            .filter(col(last_year_col_original) > 0)
            .orderBy(col(last_year_col_original).desc())
            .limit(top_n)
        )

        # Convertir a pandas
        df_empresas_top_exportadoras_resumen = df_top_snowpark.to_pandas()

        # Verificar si está vacío
        if df_empresas_top_exportadoras_resumen.empty:
            df_vacio = pd.DataFrame(columns=['NIT', 'Razón Social'] + [c.replace('Valor FOB ', '') for c in valor_columns])
            return (df_vacio, df_vacio.copy())

        # Simplificar nombres de columnas (Valor FOB USD 2025 → USD 2025, Valor FOB USD Enero 2026 → USD Enero 2026)
        df_empresas_top_exportadoras_resumen.columns = [col_name.replace('Valor FOB ', '') for col_name in df_empresas_top_exportadoras_resumen.columns]
        
        # Crear copia para aplicar formato
        df_empresas_top_exportadoras_resumen_formateado = df_empresas_top_exportadoras_resumen.copy()
        
        # Aplicar formato milify
        for col_name in df_empresas_top_exportadoras_resumen_formateado.columns:
            if "USD" in col_name:
                df_empresas_top_exportadoras_resumen_formateado[col_name] = df_empresas_top_exportadoras_resumen_formateado[col_name].apply(lambda x: milify(x))
        
        return (df_empresas_top_exportadoras_resumen, df_empresas_top_exportadoras_resumen_formateado)
    
    except Exception:
        df_vacio = pd.DataFrame(columns=['NIT', 'Razón Social'])
        return (df_vacio, df_vacio.copy())

def crear_empresas_por_tamano(_df_snowpark, top_n=10):
    """    
    Crea tablas con las top N empresas por cada tamaño.
    
    Parámetros:
    -----------
    _df_snowpark : Snowpark DataFrame
        DataFrame de Snowpark con los datos de empresas
    top_n : int
        Número de empresas top a retornar por tamaño (default: 10)
    
    Retorna:
    --------
    tuple
        (dfs_empresas, dfs_empresas_formato) - dos diccionarios con dataframes sin formato y con formato
    """
    try:
        # Identificar columnas de valor FOB USD
        valor_columns = [c for c in _df_snowpark.columns if 'Valor FOB USD ' in c]
        
        # Verificar que existan columnas de valor
        if not valor_columns:
            return ({}, {})
        
        # Determinar la columna más reciente (año más alto; corridos tienen prioridad sobre año cerrado)
        last_year_col_original = max(valor_columns, key=lambda c: (int(re.findall(r'\d{4}', c)[0]), 'Enero' in c))

        # Crear lista de agregaciones
        agg_list = [snow_sum(col(c)).alias(c) for c in valor_columns]
        
        # Agrupar una sola vez en Snowpark (incluye Tamaño de la Empresa)
        df_all_snowpark = (
            _df_snowpark
            .groupBy('NIT', 'Razón Social', 'Tamaño de la Empresa')
            .agg(*agg_list)
            .filter(col(last_year_col_original) > 0)
            .orderBy(col(last_year_col_original).desc())
        )
        
        # Definir tamaños
        tamanos_dict = {
            'df_empresas_grandes_resumen': 'Grande',
            'df_empresas_medianas_resumen': 'Mediana',
            'df_empresas_pequeñas_resumen': 'Pequeña',
            'df_empresas_micro_resumen': 'Micro',
            'df_empresas_no_clasificadas_resumen': 'No determinado'
        }
        
        # Filtrar, convertir y aplicar transformaciones
        dfs_empresas = {}
        dfs_empresas_formato = {}
        
        for df_name, tamano in tamanos_dict.items():
            # Filtrar en Snowpark y convertir a pandas
            df_temp = (
                df_all_snowpark
                .filter(col('Tamaño de la Empresa') == tamano)
                .limit(top_n)
                .drop('Tamaño de la Empresa')
                .to_pandas()
            )
            
            # Si está vacío, crear DataFrame vacío con columnas esperadas
            if df_temp.empty:
                columnas = ['NIT', 'Razón Social'] + [c.replace('Valor FOB ', '') for c in valor_columns]
                df_temp = pd.DataFrame(columns=columnas)
                dfs_empresas[df_name] = df_temp
                dfs_empresas_formato[df_name] = df_temp.copy()
                continue

            # Simplificar nombres de columnas (Valor FOB USD 2025 → USD 2025, Valor FOB USD Enero 2026 → USD Enero 2026)
            df_temp.columns = [c.replace('Valor FOB ', '') for c in df_temp.columns]
            
            # Crear copia para aplicar formato
            df_temp_formato = df_temp.copy()
            
            # Aplicar formato milify
            for col_name in df_temp_formato.columns:
                if "USD" in col_name:
                    df_temp_formato[col_name] = df_temp_formato[col_name].apply(lambda x: milify(x))
            
            # Guardar en diccionarios
            dfs_empresas[df_name] = df_temp
            dfs_empresas_formato[df_name] = df_temp_formato
        
        return (dfs_empresas, dfs_empresas_formato)
    
    except Exception:
        return ({}, {})
