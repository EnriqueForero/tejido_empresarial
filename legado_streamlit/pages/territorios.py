#============= Bibliotecas =============#
# Bibliotecas Externas
import streamlit as st
from streamlit import session_state
import json
from datetime import timedelta
import pandas as pd

# Módulos Propios
from src.streamlit_analitica import navbar, footer
# Funciones de la página de departamentos
from src.pages_utils.mapas_departamentos_utils import ls_filtros_tejido_servicios_departamentos, dict_filtros_tejido_servicios_departamentos, dict_query_tejido_servicios_departamentos, ls_filtros_exportaciones_departamentos, dict_filtros_exportaciones_departamentos, dict_query_exportaciones_departamentos, query_data_tejido_servicios_departamentos, resumen_tejido_servicios_departamentos, crear_mapa_departamentos_servicios, query_data_exportaciones_departamentos, resumen_exportaciones_sectores_departamentos, resumen_empresas_tamano_departamentos, crear_mapa_departamentos_sectores, crear_mapa_departamentos_tamanos
# Funciones de la página de municipios
from src.pages_utils.mapas_municipios_utils import ls_filtros_tejido_municipios, dict_filtros_tejido_municipios, dict_query_tejido_municipios, ls_filtros_socioec_municipios, dict_filtros_socioec_municipios, dict_query_socioec_municipios, query_data_tejido_municipios, resumen_exportaciones_sectores_municipios, crear_mapa_municipios_sectores, resumen_empresas_tamano_municipios, resumen_info_socioeconomica_municipios, crear_mapa_municipios_socioeconomico
# Parámetros
from src.pages_utils.config import periodos_mapa_sector_departamentos, ls_columnas_fob_sectores, servicios_anios_disponibles, col_conteo_tamanos_departamentos

# Funciones de ayuda
from src.pages_utils.utils import load_filtros_departamentos_servicios, load_filtros_departamentos_exportaciones, load_filtros_municipios_exportaciones, load_filtros_municipios_socioec, descarga_tabla, mostrar_resultado_en_streamlit
# Consulta segura Snowflake
from src.snowflake_analitica import registrar_evento, flujo_snowflake, update_last_activity
# Filtros dinámicos
from src.filtros_dinamicos_analitica import DynamicFilters

# ================== Configuración inicial ====================
# Configuración básica de la página en Streamlit.
st.set_page_config(
    page_title="Territorios",
    page_icon="assets/images/cubo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================== Estilos ======================
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
""", unsafe_allow_html=True)

# Configuración de producción
st.markdown("""
    <style>
    /* Ocultar el header, la decoración y la toolbar */
    header[data-testid="stHeader"],
    [data-testid="stDecoration"],
    [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Opcional: Asegurarnos de que el header no deje altura en blanco */
    header[data-testid="stHeader"] {
        height: 0px !important;
        max-height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =================== Navegación =====================
# Comprobación y configuración inicial de los parámetros de consulta en la URL.
if "page" not in st.query_params:
    st.query_params.page = '6'  # Página predeterminada si no hay parámetro 'page' en la URL.

# ================== navbar =========================
# Llamada al componente de navegación personalizada (barra de navegación).
navbar()

# Redirección condicional según el valor del parámetro 'page' en la URL.
if st.query_params.page == '1':
    st.switch_page("app.py")  # Redirige a la página de inicio.
if st.query_params.page == '2':
    st.switch_page("pages/segmentacion.py") # Redirige a la página de segmentación. 
if st.query_params.page == '3':
    st.switch_page("pages/empresas.py") # Redirige a la página de empresas
if st.query_params.page == '4':
    st.switch_page("pages/destinos.py") # Redirige a la página de destinos
if st.query_params.page == '5':
    st.switch_page("pages/valor_agregado.py") # Redirige a la página de valor agregado

# ================== Conexión a Snowflake =========================

# Definir tiempo de espera de sesión (15 minutos)
SESSION_TIMEOUT = timedelta(minutes=15)

# Actualizar flujo de Snowflake
flujo_snowflake()
    
# Actualizar tiempo de última actividad
update_last_activity()

# ============== ESTRUCTURA =============
lmargin, body, rmargin = st.columns([0.01, 0.98, 0.01], gap='small',vertical_alignment='top')

# ============== FUNCIÓN PARA REINICIAR FILTROS =============

def reset_all_filters():
    """Restablece todos los filtros y limpia los resultados."""
    
    # 0. CRÍTICO: Marcar proceso de reset
    #    Esto previene que los widgets sobrescriban durante este ciclo
    st.session_state['_filters_resetting'] = True
    
    # 1. Eliminar TODAS las keys relacionadas con los filtros
    keys_to_delete = [
        k for k in list(st.session_state.keys())
        if (k.startswith('servicios_departamentos') or k.startswith('exportaciones_departamentos')
            or k.startswith('expo_municipios') or k.startswith('socioec_municipios'))
        and k != '_filters_resetting'
    ]
    for k in keys_to_delete:
        del st.session_state[k]

    # 2. Reinicializar los diccionarios de filtros con listas vacías
    st.session_state['servicios_departamentos'] = {k: [] for k in ls_filtros_tejido_servicios_departamentos}
    st.session_state['exportaciones_departamentos'] = {k: [] for k in ls_filtros_exportaciones_departamentos}
    st.session_state['expo_municipios'] = {k: [] for k in ls_filtros_tejido_municipios}
    st.session_state['socioec_municipios'] = {k: [] for k in ls_filtros_socioec_municipios}

    # 2.5. Limpiar explícitamente las keys de los widgets multiselect
    for filter_name in ls_filtros_tejido_servicios_departamentos:
        widget_key = 'servicios_departamentos' + filter_name
        st.session_state.pop(widget_key, None)

    for filter_name in ls_filtros_exportaciones_departamentos:
        widget_key = 'exportaciones_departamentos' + filter_name
        st.session_state.pop(widget_key, None)

    for filter_name in ls_filtros_tejido_municipios:
        widget_key = 'expo_municipios' + filter_name
        st.session_state.pop(widget_key, None)

    for filter_name in ls_filtros_socioec_municipios:
        widget_key = 'socioec_municipios' + filter_name
        st.session_state.pop(widget_key, None)

    # 3. Limpiar DataFrames de resultados y estado de descarga y gráficos
    for k in (
        # Sección 1: Servicios por Departamento
        'df_geografia_departamentos',
        'df_departamentos_servicios',
        'total_registros_df_departamentos_servicios',
        'df_resumen_departamentos_servicios',
        'fig_departamentos_servicios',
        'payload_departamentos_servicios',
        
        # Sección 2: Exportaciones por Departamento
        'df_departamentos_exportaciones',
        'total_registros_df_departamentos_exportaciones',
        'df_resumen_departamentos_exportaciones',
        'fig_departamentos_exportaciones',
        'df_resumen_tamanos_departamentos',
        'fig_departamentos_tamanos',
        'payload_departamentos_exportaciones',
        
        # Sección 3: Exportaciones por Municipio
        'df_geografia_municipios',
        'df_municipios_exportaciones',
        'total_registros_df_municipios_exportaciones',
        'df_resumen_municipios_sectores',
        'fig_mapa_municipios_sectores',
        'payload_municipios_exportaciones',
        
        # Sección 4: Información Socioeconómica por Municipio
        'df_municipios_socioec',
        'total_registros_df_municipios_socioec',
        'df_resumen_municipios_socioec',
        'fig_mapa_municipios_socioec',
        'payload_municipios_socioec'
    ):
        st.session_state.pop(k, None)

# Fuente para gráficos.
fuente_datos = 'RUES, SUPERSOCIEDADES, DANE-DIAN, CRM - Cálculos ProColombia'    
        
# =========== BODY ===========
with body:
    
    # Título y fuentes 
    st.markdown("## **Territorios**")
    st.caption(":blue[Fuente: RUES, SUPERSOCIEDADES, DIRECTORIO EMPRESARIAL DEL DANE, DANE-DIAN, CRM PROCOLOMBIA.]")
    st.caption(":blue[Nota: Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.]")

    # Mensaje informativo
    st.info(
        "💡 **¿Qué puedes explorar en esta página?**\n"
        "* **Vistas dinámicas:** Utiliza el selector inferior para alternar entre mapas interactivos a nivel **departamental** y **municipal**.\n"
        "* **Tejido y exportaciones:** Visualiza geográficamente la huella de servicios de ProColombia y el origen de las exportaciones (por sectores y tamaño de empresa).\n"
        "* **Contexto socioeconómico:** Conoce los municipios de Colombia a través de sus indicadores demográficos, de educación, mercado laboral y clasificaciones especiales (como PDET o ZOMAC).", 
        icon="🗺️"
    )

    # Marcador para volver al inicio
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)

    # Selector de vista
    vista = st.radio(
    "**Seleccione la consulta que desea realizar:**",
    ["Servicios por departamento ofrecido por ProColombia", "Exportaciones por departamento de origen", "Exportaciones por municipio", "Información socioeconómica por municipio"],
    horizontal=True)
    
    # Opción 1: Servicios por Departamento
    if vista == "Servicios por departamento ofrecido por ProColombia":

        # =========== SECCIÓN 1 ===========

        # Filtros para servicios por departamentos
        df_filtros_departamentos_servicios = load_filtros_departamentos_servicios(_session=st.session_state.session)

        # Crear la clase de filtros dinámicos: Servicios por Departamentos
        dynamic_filters_filtros_departamentos_servicios = DynamicFilters(df=df_filtros_departamentos_servicios, filters_name="servicios_departamentos", filters=ls_filtros_tejido_servicios_departamentos, display_names=dict_filtros_tejido_servicios_departamentos)

        # Limpiar el flag de reset si existe
        if st.session_state.get('_filters_resetting', False):
            st.session_state['_filters_resetting'] = False
            st.rerun()  # Solo un rerun DESPUÉS de que todo se limpió

        # Marcador para volver al inicio
        st.markdown("<a id='top'></a>", unsafe_allow_html=True)

        # Título
        st.markdown(f'<h4 class="custom-header" style="text-align: center;">Distribución del tejido empresarial y los servicios facilitados por ProColombia por Departamento HQ</h4>', unsafe_allow_html=True)

        # Mostrar los filtros dinámicos: Servicios por Departamentos
        dynamic_filters_filtros_departamentos_servicios.display_filters(location="columns", num_columns=2)

        # Filtros sección de Servicios por Departamentos
        dict_filtros_generales_departamentos_servicios_usuario = {'DEPARTAMENTO_TEJIDO' : session_state['servicios_departamentos']['DEPARTAMENTO_TEJIDO'],
                                                'CADENA_SEGMENTACION_TEJIDO' : session_state['servicios_departamentos']['CADENA_SEGMENTACION_TEJIDO']}
        
        # Estructura de botones
        col1, col2, _ = st.columns(3, vertical_alignment='bottom')

        # Botones de búsqueda
        buscar = col1.button('Buscar', type='primary', use_container_width=True, key='buscar_servicios')

        # Botón de reinicio de filtros y resultados
        reinicio_vista1 = col2.button("Reiniciar filtros y resultados", type='primary', use_container_width=True, key='reiniciar1', on_click=reset_all_filters)

        if buscar:

            with st.spinner("Ejecutando consulta... :surfing_woman:"):

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Crear payload con los filtros seleccionados por el usuario
                payload_departamentos_servicios = {
                    "departamentos_servicios": dict_filtros_generales_departamentos_servicios_usuario,
                }
                progress_bar.progress(5)

                # Convertir a cadena JSON
                payload_json_departamentos_servicios = json.dumps(payload_departamentos_servicios, ensure_ascii=False)

                # Guardar payload en Session State para futuras referencias
                session_state['payload_departamentos_servicios'] = payload_json_departamentos_servicios
                progress_bar.progress(10)

                # Registrar el evento de busqueda
                registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Departamentos', detalle_evento='Búsqueda de servicios por departamento', filtros=payload_json_departamentos_servicios)
                progress_bar.progress(20)

                # Crear query
                query_tejido_servicios_departamentos = query_data_tejido_servicios_departamentos(
                    dict_columnas = dict_query_tejido_servicios_departamentos,
                    filtros_tejido_servicios_departamentos = dict_filtros_generales_departamentos_servicios_usuario
                )
                progress_bar.progress(25)

                # Obtener datos geográficos
                session_state['df_geografia_departamentos'] = st.session_state.session.sql("SELECT B.CODIGO_DEPARTAMENTO, B.NOMBRE_DEPARTAMENTO AS NOMBRE_DEPARTAMENTO_LIMPIO, B.LATITUD, B.LONGITUD FROM APP_SEGMENTACION_EXPORTACIONES.PUBLIC.GEOGRAFIA_DEPARTAMENTOS_GEO_DIVIPOLA AS B;").to_pandas()
                progress_bar.progress(30)

                # Ejecutar consulta y guardar resultado en Session State
                session_state['df_departamentos_servicios'] = st.session_state.session.sql(query_tejido_servicios_departamentos)
                progress_bar.progress(50)

                # Contar registros
                session_state['total_registros_df_departamentos_servicios'] = session_state['df_departamentos_servicios'].count()
                progress_bar.progress(55)

                # Procesar df si hay datos
                if session_state['total_registros_df_departamentos_servicios'] > 0:

                    # Crear resumen de datos
                    session_state['df_resumen_departamentos_servicios'] = resumen_tejido_servicios_departamentos(session_state['df_departamentos_servicios'])
                    progress_bar.progress(70)

                    # Unir resumen con geometría
                    session_state['df_resumen_departamentos_servicios'] = pd.merge(
                        session_state['df_resumen_departamentos_servicios'],
                        session_state['df_geografia_departamentos'],
                        left_on='Código departamento',
                        right_on='CODIGO_DEPARTAMENTO',
                        how='left'
                    )
                    progress_bar.progress(80)

                    # Elegir columnas de interés
                    session_state['df_resumen_departamentos_servicios'] = session_state['df_resumen_departamentos_servicios'][['Código departamento', 'NOMBRE_DEPARTAMENTO_LIMPIO', 'Número de empresas identificadas', 'Total de servicios ofrecidos', 'Empresas con servicios ofrecidos', 'LATITUD', 'LONGITUD']]
                    # Cambiar nombre de la columna de nombre de departamento
                    session_state['df_resumen_departamentos_servicios'] = session_state['df_resumen_departamentos_servicios'].rename(columns={'NOMBRE_DEPARTAMENTO_LIMPIO': 'Departamento'})

                    # Crear mapa
                    session_state['fig_departamentos_servicios'] = crear_mapa_departamentos_servicios(df_resumen=session_state['df_resumen_departamentos_servicios'])
                    progress_bar.progress(90)

                    # SubTítulo
                    st.markdown(f'<h5 class=custom-header" style="text-align:center;">Empresas identificadas y con servicios {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}</h5>', unsafe_allow_html=True)

                    # Mostrar el resultado
                    mostrar_resultado_en_streamlit(resultado=session_state['fig_departamentos_servicios'], fuente=fuente_datos, llave="mapa_departamentos_servicios")

                    # Habilitar descarga de datos
                    if not session_state['df_resumen_departamentos_servicios'].empty:
                        descarga_tabla(
                        df=session_state['df_resumen_departamentos_servicios'][['Código departamento', 'Departamento', 'Número de empresas identificadas', 'Total de servicios ofrecidos', 'Empresas con servicios ofrecidos']],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Distribución del tejido empresarial y los servicios facilitados por ProColombia por Departamento HQ',
                        key_descarga='tabla_1',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Distribución del tejido empresarial y los servicios facilitados por ProColombia por Departamento HQ",
                        pagina="Departamentos",
                        filtros=payload_json_departamentos_servicios
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")
                    progress_bar.progress(100)
                
                # En caso de que no hayan resultados para la consulta específica
                else:
                    st.error("No se encontro información que cumpla con los filtros seleccionados.")

    # Opción 2: Exportaciones por Departamento
    elif vista == "Exportaciones por departamento de origen":

        # =========== SECCIÓN 2 ===========

        # Filtros para exportaciones por departamentos
        df_filtros_departamentos_exportaciones = load_filtros_departamentos_exportaciones(_session=st.session_state.session)

        # Crear la clase de filtros dinámicos: Exportaciones por Departamentos
        dynamic_filters_filtros_departamentos_exportaciones = DynamicFilters(df=df_filtros_departamentos_exportaciones, filters_name="exportaciones_departamentos", filters=ls_filtros_exportaciones_departamentos, display_names=dict_filtros_exportaciones_departamentos)

        # Limpiar el flag de reset si existe
        if st.session_state.get('_filters_resetting', False):
            st.session_state['_filters_resetting'] = False
            st.rerun()  # Solo un rerun DESPUÉS de que todo se limpió
        
        # Marcador para volver al inicio
        st.markdown("<a id='top'></a>", unsafe_allow_html=True)

        # Título
        st.markdown(f'<h4 class="custom-header" style="text-align: center;">Información del tejido empresarial exportador por departamento de origen</h4>', unsafe_allow_html=True)

        # Mostrar los filtros dinámicos: Exportaciones por Departamentos
        dynamic_filters_filtros_departamentos_exportaciones.display_filters(location="columns", num_columns=3)

        # Filtros sección de Exportaciones por Departamentos
        dict_filtros_generales_departamentos_exportaciones_usuario = {'CADENA_PRODUCTIVA_BIENES_SERVICIOS' : session_state['exportaciones_departamentos']['CADENA_PRODUCTIVA_BIENES_SERVICIOS'],
                                                'SECTOR_BIENES_SERVICIOS' : session_state['exportaciones_departamentos']['SECTOR_BIENES_SERVICIOS'],
                                                'SUBSECTOR_BIENES_SERVICIOS' : session_state['exportaciones_departamentos']['SUBSECTOR_BIENES_SERVICIOS'],
                                                'COD_POSICION_ARANCELARIA_BIENES_SERVICIOS' : session_state['exportaciones_departamentos']['COD_POSICION_ARANCELARIA_BIENES_SERVICIOS'],
                                                'DESC_POSICION_ARANCELARIA_BIENES_SERVICIOS' : session_state['exportaciones_departamentos']['DESC_POSICION_ARANCELARIA_BIENES_SERVICIOS']}

        
        # Estructura de botones
        col1, col2, _ = st.columns(3, vertical_alignment='bottom')

        # Botones de búsqueda
        buscar = col1.button('Buscar', type='primary', use_container_width=True, key='buscar_exportaciones')

        # Botón de reinicio de filtros y resultados
        reinicio_vista2 = col2.button("Reiniciar filtros y resultados", type='primary', use_container_width=True, key='reiniciar2', on_click=reset_all_filters)
        
        if buscar:
            
            with st.spinner("Ejecutando consulta... :surfing_woman:"):
                    
                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Crear payload con los filtros seleccionados por el usuario
                payload_departamentos_exportaciones = {
                    "departamentos_exportaciones": dict_filtros_generales_departamentos_exportaciones_usuario,
                }
                progress_bar.progress(5)

                # Convertir a cadena JSON
                payload_json_departamentos_exportaciones = json.dumps(payload_departamentos_exportaciones, ensure_ascii=False)

                # Guardar payload en Session State para futuras referencias
                session_state['payload_departamentos_exportaciones'] = payload_json_departamentos_exportaciones
                progress_bar.progress(10)

                # Registrar el evento de busqueda
                registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Departamentos', detalle_evento='Búsqueda de exportaciones por departamento', filtros=payload_json_departamentos_exportaciones)
                progress_bar.progress(20)

                # Crear query
                query_exportaciones_departamentos = query_data_exportaciones_departamentos(
                    dict_columnas = dict_query_exportaciones_departamentos,
                    filtros_exportaciones_departamentos = dict_filtros_generales_departamentos_exportaciones_usuario
                )
                progress_bar.progress(25)

                # Obtener datos geográficos
                session_state['df_geografia_departamentos'] = st.session_state.session.sql("SELECT B.CODIGO_DEPARTAMENTO, B.NOMBRE_DEPARTAMENTO AS NOMBRE_DEPARTAMENTO_LIMPIO, B.LATITUD, B.LONGITUD FROM APP_SEGMENTACION_EXPORTACIONES.PUBLIC.GEOGRAFIA_DEPARTAMENTOS_GEO_DIVIPOLA AS B;").to_pandas()
                progress_bar.progress(30)

                # Ejecutar consulta y guardar resultado en Session State
                session_state['df_departamentos_exportaciones'] = st.session_state.session.sql(query_exportaciones_departamentos)
                progress_bar.progress(50)

                # Contar registros
                session_state['total_registros_df_departamentos_exportaciones'] = session_state['df_departamentos_exportaciones'].count()
                progress_bar.progress(55)

                # Procesar df si hay datos
                if session_state['total_registros_df_departamentos_exportaciones'] > 0:

                    ########
                    # MAPA 1
                    ########

                    # Crear resumen de datos - Sectores
                    session_state['df_resumen_departamentos_exportaciones'] = resumen_exportaciones_sectores_departamentos(session_state['df_departamentos_exportaciones'])
                    progress_bar.progress(60)

                    # Unir resumen Sectores con geometría
                    session_state['df_resumen_departamentos_exportaciones'] = pd.merge(
                        session_state['df_resumen_departamentos_exportaciones'],
                        session_state['df_geografia_departamentos'],
                        left_on='Código departamento',
                        right_on='CODIGO_DEPARTAMENTO',
                        how='left'
                    )

                    # Crear mapa
                    session_state['fig_departamentos_exportaciones'] = crear_mapa_departamentos_sectores(
                        df_resumen_sectores=session_state['df_resumen_departamentos_exportaciones'],
                        columnas_fob=periodos_mapa_sector_departamentos,
                    )

                    # SubTítulo
                    st.markdown(f'<h5 class=custom-header" style="text-align:center;">Top 5 sectores de exportación por departamento de origen</h5>', unsafe_allow_html=True)

                    # Mostrar el resultado
                    mostrar_resultado_en_streamlit(resultado=session_state['fig_departamentos_exportaciones'], fuente=fuente_datos, llave="mapa_departamentos_exportaciones_sectores")

                    # Elegir columnas de interés
                    session_state['df_resumen_departamentos_exportaciones'] = session_state['df_resumen_departamentos_exportaciones'][['Código departamento', 'NOMBRE_DEPARTAMENTO_LIMPIO', 'Sector'] + periodos_mapa_sector_departamentos]

                    # Cambiar nombre de la columna de nombre de departamento
                    session_state['df_resumen_departamentos_exportaciones'] = session_state['df_resumen_departamentos_exportaciones'].rename(columns={'NOMBRE_DEPARTAMENTO_LIMPIO': 'Departamento'})

                    # Habilitar descarga de datos - Sectores
                    if not session_state['df_resumen_departamentos_exportaciones'].empty:
                        descarga_tabla(
                        df=session_state['df_resumen_departamentos_exportaciones'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Información del tejido empresarial exportador por departamento de origen - Sectores',
                        key_descarga='tabla_2',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Información del tejido empresarial exportador por departamento de origen - Sectores",
                        pagina="Departamentos",
                        filtros=payload_json_departamentos_exportaciones
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                    ########
                    # MAPA 2
                    ########

                    # Crear resumen de datos - Tamaños y empresas
                    session_state['df_resumen_tamanos_departamentos'] = resumen_empresas_tamano_departamentos(session_state['df_departamentos_exportaciones'], col_conteo=col_conteo_tamanos_departamentos)
                    progress_bar.progress(80)

                    # Rellenar vacios de Tamaño empresa por Desconocido (SOLO POR DEBUGG)
                    session_state['df_resumen_tamanos_departamentos']['Tamaño empresa'] = session_state['df_resumen_tamanos_departamentos']['Tamaño empresa'].fillna('Desconocido')

                    # Unir resumen con geometría
                    session_state['df_resumen_tamanos_departamentos'] = pd.merge(
                        session_state['df_resumen_tamanos_departamentos'],
                        session_state['df_geografia_departamentos'],
                        left_on='Código departamento',
                        right_on='CODIGO_DEPARTAMENTO',
                        how='left'
                    )

                    # Elegir columnas de interés
                    session_state['df_resumen_tamanos_departamentos'] = session_state['df_resumen_tamanos_departamentos'][['Código departamento', 'NOMBRE_DEPARTAMENTO_LIMPIO', 'Tamaño empresa', 'Número de empresas', 'Distribución porcentual (%)', 'LATITUD', 'LONGITUD']]
                    # Cambiar nombre de la columna de nombre de departamento
                    session_state['df_resumen_tamanos_departamentos'] = session_state['df_resumen_tamanos_departamentos'].rename(columns={'NOMBRE_DEPARTAMENTO_LIMPIO': 'Departamento'})

                    # SubTítulo — el período se deriva del último corrido en ls_columnas_fob_sectores
                    periodo_tamanos = ls_columnas_fob_sectores[-1].replace('FOB USD ', '')
                    st.divider()
                    st.markdown(f'<h5 class=custom-header" style="text-align:center;">Tamaño de empresas exportadoras por departamento de origen ({periodo_tamanos})</h5>', unsafe_allow_html=True)

                    # Crear mapa
                    session_state['fig_departamentos_tamanos'] = crear_mapa_departamentos_tamanos(df_resumen_tamanos=session_state['df_resumen_tamanos_departamentos'])
                    progress_bar.progress(90)

                    # Mostrar el resultado
                    mostrar_resultado_en_streamlit(resultado=session_state['fig_departamentos_tamanos'], fuente=fuente_datos, llave="mapa_departamentos_tamanos")

                    # Habilitar descarga de datos - Tamaños y empresas
                    if not session_state['df_resumen_tamanos_departamentos'].empty:
                        descarga_tabla(
                        df=session_state['df_resumen_tamanos_departamentos'][['Código departamento', 'Departamento', 'Tamaño empresa', 'Número de empresas', 'Distribución porcentual (%)']],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Información del tejido empresarial exportador por departamento de origen - Tamaños y empresas',
                        key_descarga='tabla_3',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Información del tejido empresarial exportador por departamento de origen - Tamaños y empresas",
                        pagina="Departamentos",
                        filtros=payload_json_departamentos_exportaciones
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                    progress_bar.progress(100)
                else:
                    st.error("No se encontro información que cumpla con los filtros seleccionados.")
                    progress_bar.progress(100)

    # Opción 3: Exportaciones por Municipio
    if vista == "Exportaciones por municipio":

        # =========== SECCIÓN 3 ===========

        # Filtros para exportaciones por municipio
        df_filtros_municipios_exportaciones = load_filtros_municipios_exportaciones(_session=st.session_state.session)

        # Llenar vacios en los filtros de municipios con 'Desconocido' en todas las columnas
        for col in df_filtros_municipios_exportaciones.columns:
            df_filtros_municipios_exportaciones[col] = df_filtros_municipios_exportaciones[col].fillna('Desconocido')

        # Crear la clase de filtros dinámicos: Exportaciones por Municipios
        dynamic_filters_filtros_municipios_expo = DynamicFilters(df=df_filtros_municipios_exportaciones, filters_name="expo_municipios", filters=ls_filtros_tejido_municipios, display_names=dict_filtros_tejido_municipios)

        # Limpiar el flag de reset si existe
        if st.session_state.get('_filters_resetting', False):
            st.session_state['_filters_resetting'] = False
            st.rerun()  # Solo un rerun DESPUÉS de que todo se limpió

        # Marcador para volver al inicio
        st.markdown("<a id='top'></a>", unsafe_allow_html=True)

        # Título
        st.markdown(f'<h4 class="custom-header" style="text-align: center;">Distribución de exportaciones por Municipio HQ</h4>', unsafe_allow_html=True)

        # Mostrar los filtros dinámicos: Exportaciones por Municipios
        dynamic_filters_filtros_municipios_expo.display_filters(location="columns", num_columns=4)

        # Filtros sección de Exportaciones por Municipios
        dict_filtros_generales_municipios_exportaciones_usuario = {'DEPARTAMENTO_TEJIDO' : session_state['expo_municipios']['DEPARTAMENTO_TEJIDO'],
                                                'MUNICIPIO_TEJIDO' : session_state['expo_municipios']['MUNICIPIO_TEJIDO'],
                                                'PDET' : session_state['expo_municipios']['PDET'],
                                                'MENOR_200K_HABITANTES' : session_state['expo_municipios']['MENOR_200K_HABITANTES']}
        # Estructura de botones
        col1, col2, _ = st.columns(3, vertical_alignment='bottom')

        # Botones de búsqueda
        buscar = col1.button('Buscar', type='primary', use_container_width=True, key='buscar_municipios_expo')

        # Botón de reinicio de filtros y resultados
        reinicio_vista3 = col2.button("Reiniciar filtros y resultados", type='primary', use_container_width=True, key='reiniciar3', on_click=reset_all_filters)

        if buscar:
            
            with st.spinner("Ejecutando consulta... :surfing_woman:"):
                    
                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Crear payload con los filtros seleccionados por el usuario
                payload_municipios_exportaciones = {
                    "municipios_exportaciones": dict_filtros_generales_municipios_exportaciones_usuario,
                }
                progress_bar.progress(5)

                # Convertir a cadena JSON
                payload_json_municipios_exportaciones = json.dumps(payload_municipios_exportaciones, ensure_ascii=False)

                # Guardar payload en Session State para futuras referencias
                session_state['payload_municipios_exportaciones'] = payload_json_municipios_exportaciones
                progress_bar.progress(10)

                # Registrar el evento de busqueda
                registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Departamentos', detalle_evento='Búsqueda de exportaciones por municipio', filtros=payload_json_municipios_exportaciones)
                progress_bar.progress(20)

                # Crear query
                query_tejido_tejido_municipios = query_data_tejido_municipios(
                    dict_columnas = dict_query_tejido_municipios,
                    filtros_tejido_municipios = dict_filtros_generales_municipios_exportaciones_usuario
                )
                progress_bar.progress(25)

                # Obtener datos geográficos
                session_state['df_geografia_municipios'] = st.session_state.session.sql("SELECT B.CODIGO_DEPARTAMENTO, B.NOMBRE_DEPARTAMENTO, B.CODIGO_MUNICIPIO, B.NOMBRE_MUNICIPIO, B.LONGITUD, B.LATITUD FROM APP_SEGMENTACION_EXPORTACIONES.PUBLIC.GEOGRAFIA_MUNICIPIOS_GEO_DIVIPOLA AS B;").to_pandas()
                progress_bar.progress(30)

                # Ejecutar consulta y guardar resultado en Session State
                session_state['df_municipios_exportaciones'] = st.session_state.session.sql(query_tejido_tejido_municipios)
                progress_bar.progress(50)

                # Contar registros
                session_state['total_registros_df_municipios_exportaciones'] = session_state['df_municipios_exportaciones'].count()
                progress_bar.progress(55)

                # Procesar df si hay datos
                if session_state['total_registros_df_municipios_exportaciones'] > 0:

                    ########
                    # MAPA 1
                    ########

                    # Crear resumen de datos - Sectores
                    session_state['df_resumen_municipios_sectores'] = resumen_exportaciones_sectores_municipios(session_state['df_municipios_exportaciones'])
                    progress_bar.progress(60)

                    # Unir resumen Sectores con geometría
                    session_state['df_resumen_municipios_sectores'] = pd.merge(
                        session_state['df_resumen_municipios_sectores'],
                        session_state['df_geografia_municipios'],
                        left_on=['Código departamento', 'Código municipio'],
                        right_on=['CODIGO_DEPARTAMENTO', 'CODIGO_MUNICIPIO'],
                        how='left'
                    )

                    # Crear mapa
                    session_state['fig_mapa_municipios_sectores'] = crear_mapa_municipios_sectores(
                        df_resumen_sectores=session_state['df_resumen_municipios_sectores'],
                        columnas_fob=ls_columnas_fob_sectores,
                    )
                    progress_bar.progress(90)

                    # SubTítulo
                    st.markdown(f'<h5 class=custom-header" style="text-align:center;">Sectores exportados por empresas registradas en el municipio</h5>', unsafe_allow_html=True)

                    # Mostrar el resultado
                    mostrar_resultado_en_streamlit(resultado=session_state['fig_mapa_municipios_sectores'], fuente=fuente_datos, llave="mapa_municipios_expo")

                    # Habilitar descarga de datos - Municipios sectores
                    if not session_state['df_resumen_municipios_sectores'].empty:
                        descarga_tabla(
                        df=session_state['df_resumen_municipios_sectores'][['Sector', 'Código departamento', 'Departamento', 'Código municipio', 'Municipio'] + ls_columnas_fob_sectores],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Sectores exportados por empresas registradas en el municipio',
                        key_descarga='tabla_4',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Sectores exportados por empresas registradas en el municipio",
                        pagina="Departamentos",
                        filtros=payload_json_municipios_exportaciones
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                    progress_bar.progress(100)
                else:
                    st.error("No se encontro información que cumpla con los filtros seleccionados.")
                    progress_bar.progress(100)

    # Opción 4: Información socioeconómica por Municipio
    if vista == "Información socioeconómica por municipio":

        # =========== SECCIÓN 4 ===========

        # Filtros para información socioeconómica por municipio
        df_filtros_municipios_socioec = load_filtros_municipios_socioec(_session=st.session_state.session)

        # Llenar vacios en los filtros de municipios con 'Desconocido' en todas las columnas
        for col in df_filtros_municipios_socioec.columns:
            df_filtros_municipios_socioec[col] = df_filtros_municipios_socioec[col].fillna('Desconocido')

        # Crear la clase de filtros dinámicos: Información socioeconómica por Municipios
        dynamic_filters_filtros_municipios_socioec = DynamicFilters(df=df_filtros_municipios_socioec, filters_name="socioec_municipios", filters=ls_filtros_socioec_municipios, display_names=dict_filtros_socioec_municipios)

        # Limpiar el flag de reset si existe
        if st.session_state.get('_filters_resetting', False):
            st.session_state['_filters_resetting'] = False
            st.rerun()  # Solo un rerun DESPUÉS de que todo se limpió

        # Marcador para volver al inicio
        st.markdown("<a id='top'></a>", unsafe_allow_html=True)

        # Título
        st.markdown(f'<h4 class="custom-header" style="text-align: center;">Información socioeconómica por municipio</h4>', unsafe_allow_html=True)

        # Mostrar los filtros dinámicos: Exportaciones por Municipios
        dynamic_filters_filtros_municipios_socioec.display_filters(location="columns", num_columns=4)

        # Filtros sección de Exportaciones por Municipios
        dict_filtros_generales_municipios_socioec_usuario = {'DEPARTAMENTO_TEJIDO' : session_state['socioec_municipios']['DEPARTAMENTO_TEJIDO'],
                                                'MUNICIPIO_TEJIDO' : session_state['socioec_municipios']['MUNICIPIO_TEJIDO'],
                                                'PDET' : session_state['socioec_municipios']['PDET'],
                                                'MENOR_200K_HABITANTES' : session_state['socioec_municipios']['MENOR_200K_HABITANTES'],
                                                'ZOMAC' : session_state['socioec_municipios']['ZOMAC']}
        # Estructura de botones
        col1, col2, _ = st.columns(3, vertical_alignment='bottom')

        # Botones de búsqueda
        buscar = col1.button('Buscar', type='primary', use_container_width=True, key='buscar_info_socioec')

        # Botón de reinicio de filtros y resultados
        reinicio_vista4 = col2.button("Reiniciar filtros y resultados", type='primary', use_container_width=True, key='reiniciar4', on_click=reset_all_filters)

        if buscar:
            
            with st.spinner("Ejecutando consulta... :surfing_woman:"):
                    
                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Crear payload con los filtros seleccionados por el usuario
                payload_municipios_socioec = {
                    "municipios_socioec": dict_filtros_generales_municipios_socioec_usuario,
                }
                progress_bar.progress(5)

                # Convertir a cadena JSON
                payload_json_municipios_socioec = json.dumps(payload_municipios_socioec, ensure_ascii=False)

                # Guardar payload en Session State para futuras referencias
                session_state['payload_municipios_socioec'] = payload_json_municipios_socioec
                progress_bar.progress(10)

                # Registrar el evento de busqueda
                registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Departamentos', detalle_evento='Búsqueda de información socioec por municipio', filtros=payload_json_municipios_socioec)
                progress_bar.progress(20)

                # Crear query
                query_tejido_socioec_municipios = query_data_tejido_municipios(
                    dict_columnas = dict_query_socioec_municipios,
                    filtros_tejido_municipios = dict_filtros_generales_municipios_socioec_usuario
                )
                progress_bar.progress(25)

                # Obtener datos geográficos
                session_state['df_geografia_municipios'] = st.session_state.session.sql("SELECT B.CODIGO_DEPARTAMENTO, B.NOMBRE_DEPARTAMENTO, B.CODIGO_MUNICIPIO, B.NOMBRE_MUNICIPIO, B.LONGITUD, B.LATITUD FROM APP_SEGMENTACION_EXPORTACIONES.PUBLIC.GEOGRAFIA_MUNICIPIOS_GEO_DIVIPOLA AS B;").to_pandas()
                progress_bar.progress(30)

                # Ejecutar consulta y guardar resultado en Session State
                session_state['df_municipios_socioec'] = st.session_state.session.sql(query_tejido_socioec_municipios)
                progress_bar.progress(50)

                # Contar registros
                session_state['total_registros_df_municipios_socioec'] = session_state['df_municipios_socioec'].count()
                progress_bar.progress(55)

                # Procesar df si hay datos
                if session_state['total_registros_df_municipios_socioec'] > 0:

                    # Crear resumen de datos - Indicadores socioeconómicos
                    session_state['df_resumen_municipios_socioec'] = resumen_info_socioeconomica_municipios(session_state['df_municipios_socioec'])
                    progress_bar.progress(70)
                    
                    # Unir resumen Sectores con geometría
                    session_state['df_resumen_municipios_socioec'] = pd.merge(
                        session_state['df_resumen_municipios_socioec'],
                        session_state['df_geografia_municipios'],
                        left_on=['Código departamento', 'Código municipio'],
                        right_on=['CODIGO_DEPARTAMENTO', 'CODIGO_MUNICIPIO'],
                        how='left'
                    )

                    # Crear mapa
                    session_state['fig_mapa_municipios_socioec'] = crear_mapa_municipios_socioeconomico(
                        df_municipios_sociec=session_state['df_resumen_municipios_socioec'],
                    )
                    progress_bar.progress(90)

                    # SubTítulo
                    st.markdown(f'<h5 class=custom-header" style="text-align:center;">Indicadores socioeconómicos por municipio</h5>', unsafe_allow_html=True)

                    # Mostrar el resultado
                    mostrar_resultado_en_streamlit(resultado=session_state['fig_mapa_municipios_socioec'], fuente=fuente_datos, llave="mapa_municipios_socioec")
                    progress_bar.progress(100)

                    # Habilitar descarga de datos - Municipios sectores
                    if not session_state['df_resumen_municipios_socioec'].empty:
                        descarga_tabla(
                        df=session_state['df_resumen_municipios_socioec'][['Código departamento', 'Departamento', 'Código municipio', 'Municipio', 'Menor 200K habitantes', 'PDET', 'Actividades primarias (%)', 'Actividades secundarias (%)', 'Actividades terciarias (%)', 'Grupos étnicos (%)', 'Informalidad (%)', 'Jóvenes (%)', 'Mujeres (%)', 'Población con discapacidad (%)', 'Población con educación técnica/tecnología (%)', 'Población con educación media (%)', 'Población con posgrado (%)', 'Población con pregrado (%)', 'Pobreza (%)', 'Población total', 'ZOMAC']],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Indicadores socioeconómicos por municipio',
                        key_descarga='tabla_5',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Indicadores socioeconómicos por municipio",
                        pagina="Departamentos",
                        filtros=payload_json_municipios_socioec
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

# ========== Footer ==========#
footer()   
