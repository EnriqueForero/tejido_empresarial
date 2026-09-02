#============= Bibliotecas =============#
# Bibliotecas Externas
import streamlit as st
from streamlit import session_state
import json
from datetime import timedelta
import pandas as pd

# Módulos Propios
from src.streamlit_analitica import navbar, footer
# Funciones de la página de valor agregado
from src.pages_utils.valor_agregado_utils import ls_filtros_bienes, dict_filtros_bienes, dict_query_bienes, query_data_bienes, resumen_valor_agregado, grafico_barras_periodos_seleccionados, top_partidas_por_categoria, top_partidas_por_departamento, valor_exportado_departamento_long, valor_exportado_departamento_periodo, renderizar_seccion_valor_agregado
# Parámetros
from src.pages_utils.config import periodos_cerrados, periodos_corridos, periodos_cerrados_conteo, periodos_corridos_conteo, disponibilidad_periodos_corridos_usd, disponibilidad_periodos_corridos_conteo
# Funciones de ayuda
from src.pages_utils.utils import load_filtros_bienes, descarga_tabla, mostrar_resultado_en_streamlit
# Consulta segura Snowflake
from src.snowflake_analitica import registrar_evento, flujo_snowflake, update_last_activity
# Filtros dinámicos
from src.filtros_dinamicos_analitica import DynamicFilters

# ================== Configuración inicial ====================
# Configuración básica de la página en Streamlit.
st.set_page_config(
    page_title="Valor Agregado",
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
    st.query_params.page = '5'  # Página predeterminada si no hay parámetro 'page' en la URL.

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
if st.query_params.page == '6':
    st.switch_page("pages/territorios.py") # Redirige a la página de territorios

# ================== Conexión a Snowflake =========================

# Definir tiempo de espera de sesión (15 minutos)
SESSION_TIMEOUT = timedelta(minutes=15)

# Actualizar flujo de Snowflake
flujo_snowflake()
    
# Actualizar tiempo de última actividad
update_last_activity()

# =========== Obtener insumos para los filtros del aplicativo ==============

# Filtros generales para empresas
df_filtros_bienes = load_filtros_bienes(_session=st.session_state.session)

# ============== ESTRUCTURA =============
lmargin, body, rmargin = st.columns([0.01, 0.98, 0.01], gap='small',vertical_alignment='top')

def reset_all_filters():
    """Restablece todos los filtros y limpia los resultados."""

    # 0. CRÍTICO: Marcar proceso de reset
    #    Esto previene que los widgets sobrescriban durante este ciclo
    st.session_state['_filters_resetting'] = True

    # 1. Eliminar TODAS las keys relacionadas con los filtros
    keys_to_delete = [
        k for k in list(st.session_state.keys())
        if (k.startswith('bienes'))
        and k != '_filters_resetting'
    ]
    for k in keys_to_delete:
        del st.session_state[k]

    # 2. Reinicializar los diccionarios de filtros con listas vacías
    st.session_state['bienes'] = {k: [] for k in ls_filtros_bienes}

    # 2.5. Limpiar explícitamente las keys de los widgets multiselect
    for filter_name in ls_filtros_bienes:
        widget_key = 'bienes' + filter_name
        st.session_state.pop(widget_key, None)    

    # 3. Limpiar DataFrames de resultados y estado de descarga y gráficos
    for k in (
        # Resultados de consulta principal
        'df_valor_agregado',
        'total_registros',
        'payload_bienes',
        
        # DataFrames de Cadenas
        'df_cadenas_cerrado',
        'df_cadenas_cerrado_formato',
        'df_cadenas_corrido',
        'df_cadenas_corrido_formato',
        'df_total_cadenas',
        'df_total_cadenas_formato',
        'fig_cadenas_cerrado',
        'fig_cadenas_corrido',
        
        # DataFrames por categoría de valor agregado - Productos
        'df_va_cerrado_manufactura_alta_tecnologia',
        'df_va_cerrado_manufactura_alta_tecnologia_formato',
        'df_va_corrido_manufactura_alta_tecnologia',
        'df_va_corrido_manufactura_alta_tecnologia_formato',
        'df_va_total_manufactura_alta_tecnologia',
        'df_va_total_manufactura_alta_tecnologia_formato',
        'fig_df_va_cerrado_manufactura_alta_tecnologia',
        'fig_df_va_corrido_manufactura_alta_tecnologia',
        
        'df_va_cerrado_servicios_alta_tecnologia',
        'df_va_cerrado_servicios_alta_tecnologia_formato',
        'df_va_corrido_servicios_alta_tecnologia',
        'df_va_corrido_servicios_alta_tecnologia_formato',
        'df_va_total_servicios_alta_tecnologia',
        'df_va_total_servicios_alta_tecnologia_formato',
        'fig_df_va_cerrado_servicios_alta_tecnologia',
        'fig_df_va_corrido_servicios_alta_tecnologia',
        
        'df_va_cerrado_manufacturas_baja_tecnologia',
        'df_va_cerrado_manufacturas_baja_tecnologia_formato',
        'df_va_corrido_manufacturas_baja_tecnologia',
        'df_va_corrido_manufacturas_baja_tecnologia_formato',
        'df_va_total_manufacturas_baja_tecnologia',
        'df_va_total_manufacturas_baja_tecnologia_formato',
        'fig_df_va_cerrado_manufacturas_baja_tecnologia',
        'fig_df_va_corrido_manufacturas_baja_tecnologia',
        
        'df_va_cerrado_manufacturas_recursos_naturales',
        'df_va_cerrado_manufacturas_recursos_naturales_formato',
        'df_va_corrido_manufacturas_recursos_naturales',
        'df_va_corrido_manufacturas_recursos_naturales_formato',
        'df_va_total_manufacturas_recursos_naturales',
        'df_va_total_manufacturas_recursos_naturales_formato',
        'fig_df_va_cerrado_manufacturas_recursos_naturales',
        'fig_df_va_corrido_manufacturas_recursos_naturales',
        
        'df_va_cerrado_otras_transacciones',
        'df_va_cerrado_otras_transacciones_formato',
        'df_va_corrido_otras_transacciones',
        'df_va_corrido_otras_transacciones_formato',
        'df_va_total_otras_transacciones',
        'df_va_total_otras_transacciones_formato',
        'fig_df_va_cerrado_otras_transacciones',
        'fig_df_va_corrido_otras_transacciones',
        
        'df_va_cerrado_manufacturas_tecnologia_media',
        'df_va_cerrado_manufacturas_tecnologia_media_formato',
        'df_va_corrido_manufacturas_tecnologia_media',
        'df_va_corrido_manufacturas_tecnologia_media_formato',
        'df_va_total_manufacturas_tecnologia_media',
        'df_va_total_manufacturas_tecnologia_media_formato',
        'fig_df_va_cerrado_manufacturas_tecnologia_media',
        'fig_df_va_corrido_manufacturas_tecnologia_media',
        
        'df_va_cerrado_otros_servicios_conocimiento',
        'df_va_cerrado_otros_servicios_conocimiento_formato',
        'df_va_corrido_otros_servicios_conocimiento',
        'df_va_corrido_otros_servicios_conocimiento_formato',
        'df_va_total_otros_servicios_conocimiento',
        'df_va_total_otros_servicios_conocimiento_formato',
        'fig_df_va_cerrado_otros_servicios_conocimiento',
        'fig_df_va_corrido_otros_servicios_conocimiento',
        
        'df_va_cerrado_servicios_mercado_conocimiento',
        'df_va_cerrado_servicios_mercado_conocimiento_formato',
        'df_va_corrido_servicios_mercado_conocimiento',
        'df_va_corrido_servicios_mercado_conocimiento_formato',
        'df_va_total_servicios_mercado_conocimiento',
        'df_va_total_servicios_mercado_conocimiento_formato',
        'fig_df_va_cerrado_servicios_mercado_conocimiento',
        'fig_df_va_corrido_servicios_mercado_conocimiento',
        
        'df_va_cerrado_primarios',
        'df_va_cerrado_primarios_formato',
        'df_va_corrido_primarios',
        'df_va_corrido_primarios_formato',
        'df_va_total_primarios',
        'df_va_total_primarios_formato',
        'fig_df_va_cerrado_primarios',
        'fig_df_va_corrido_primarios',
        
        # DataFrames por categoría de valor agregado - Departamentos
        'df_dep_cerrado_manufactura_alta_tecnologia',
        'df_dep_cerrado_manufactura_alta_tecnologia_formato',
        'df_dep_corrido_manufactura_alta_tecnologia',
        'df_dep_corrido_manufactura_alta_tecnologia_formato',
        'df_dep_total_manufactura_alta_tecnologia',
        'df_dep_total_manufactura_alta_tecnologia_formato',
        'fig_df_dep_cerrado_manufactura_alta_tecnologia',
        'fig_df_dep_corrido_manufactura_alta_tecnologia',
        
        'df_dep_cerrado_servicios_alta_tecnologia',
        'df_dep_cerrado_servicios_alta_tecnologia_formato',
        'df_dep_corrido_servicios_alta_tecnologia',
        'df_dep_corrido_servicios_alta_tecnologia_formato',
        'df_dep_total_servicios_alta_tecnologia',
        'df_dep_total_servicios_alta_tecnologia_formato',
        'fig_df_dep_cerrado_servicios_alta_tecnologia',
        'fig_df_dep_corrido_servicios_alta_tecnologia',
        
        'df_dep_cerrado_manufacturas_baja_tecnologia',
        'df_dep_cerrado_manufacturas_baja_tecnologia_formato',
        'df_dep_corrido_manufacturas_baja_tecnologia',
        'df_dep_corrido_manufacturas_baja_tecnologia_formato',
        'df_dep_total_manufacturas_baja_tecnologia',
        'df_dep_total_manufacturas_baja_tecnologia_formato',
        'fig_df_dep_cerrado_manufacturas_baja_tecnologia',
        'fig_df_dep_corrido_manufacturas_baja_tecnologia',
        
        'df_dep_cerrado_manufacturas_recursos_naturales',
        'df_dep_cerrado_manufacturas_recursos_naturales_formato',
        'df_dep_corrido_manufacturas_recursos_naturales',
        'df_dep_corrido_manufacturas_recursos_naturales_formato',
        'df_dep_total_manufacturas_recursos_naturales',
        'df_dep_total_manufacturas_recursos_naturales_formato',
        'fig_df_dep_cerrado_manufacturas_recursos_naturales',
        'fig_df_dep_corrido_manufacturas_recursos_naturales',
        
        'df_dep_cerrado_otras_transacciones',
        'df_dep_cerrado_otras_transacciones_formato',
        'df_dep_corrido_otras_transacciones',
        'df_dep_corrido_otras_transacciones_formato',
        'df_dep_total_otras_transacciones',
        'df_dep_total_otras_transacciones_formato',
        'fig_df_dep_cerrado_otras_transacciones',
        'fig_df_dep_corrido_otras_transacciones',
        
        'df_dep_cerrado_manufacturas_tecnologia_media',
        'df_dep_cerrado_manufacturas_tecnologia_media_formato',
        'df_dep_corrido_manufacturas_tecnologia_media',
        'df_dep_corrido_manufacturas_tecnologia_media_formato',
        'df_dep_total_manufacturas_tecnologia_media',
        'df_dep_total_manufacturas_tecnologia_media_formato',
        'fig_df_dep_cerrado_manufacturas_tecnologia_media',
        'fig_df_dep_corrido_manufacturas_tecnologia_media',
        
        'df_dep_cerrado_otros_servicios_conocimiento',
        'df_dep_cerrado_otros_servicios_conocimiento_formato',
        'df_dep_corrido_otros_servicios_conocimiento',
        'df_dep_corrido_otros_servicios_conocimiento_formato',
        'df_dep_total_otros_servicios_conocimiento',
        'df_dep_total_otros_servicios_conocimiento_formato',
        'fig_df_dep_cerrado_otros_servicios_conocimiento',
        'fig_df_dep_corrido_otros_servicios_conocimiento',
        
        'df_dep_cerrado_servicios_mercado_conocimiento',
        'df_dep_cerrado_servicios_mercado_conocimiento_formato',
        'df_dep_corrido_servicios_mercado_conocimiento',
        'df_dep_corrido_servicios_mercado_conocimiento_formato',
        'df_dep_total_servicios_mercado_conocimiento',
        'df_dep_total_servicios_mercado_conocimiento_formato',
        'fig_df_dep_cerrado_servicios_mercado_conocimiento',
        'fig_df_dep_corrido_servicios_mercado_conocimiento',
        
        'df_dep_cerrado_primarios',
        'df_dep_cerrado_primarios_formato',
        'df_dep_corrido_primarios',
        'df_dep_corrido_primarios_formato',
        'df_dep_total_primarios',
        'df_dep_total_primarios_formato',
        'fig_df_dep_cerrado_primarios',
        'fig_df_dep_corrido_primarios',
        
        # DataFrames de Conteo de Productos
        'df_valor_dep_cerrado',
        'df_valor_dep_cerrado_fmt',
        'df_valor_dep_corrido',
        'df_valor_dep_corrido_fmt',
        'df_valor_dep_long'
    ):
        st.session_state.pop(k, None)

# =========== BODY ===========
with body:

    # Título y fuentes 
    st.markdown("## **Valor agregado**")
    st.caption(":blue[Fuente: RUES, SUPERSOCIEDADES, DANE-DIAN, CRM PROCOLOMBIA.]")
    st.caption(":blue[Nota: Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.]")
    
    # Mensaje informativo
    st.info(
        "💡 **¿Qué puedes explorar en esta página?**\n"
        "* **Clasificación de valor agregado:** Analiza las exportaciones colombianas según su nivel tecnológico y de conocimiento, desglosado por **cadena productiva**.\n"
        "* **Dinámica de productos:** Consulta el volumen de partidas arancelarias exportadas y descubre los **productos** líderes dentro de cada categoría.\n"
        "* **Origen regional:** Identifica qué **departamentos** de Colombia están impulsando las exportaciones en las distintas clasificaciones de valor agregado.", 
        icon="💎"
    )

    # Marcador para volver al inicio
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)
    
    # ============= Filtros Bienes ============
    st.markdown("#### **Filtros por tipo de exportación**")

    # Crear la clase de filtros dinámicos
    dynamic_filters_filtros_bienes = DynamicFilters(df=df_filtros_bienes, filters_name="bienes", filters=ls_filtros_bienes, display_names=dict_filtros_bienes)

    # Mostrar los filtros dinámicos 
    dynamic_filters_filtros_bienes.display_filters(location="columns", num_columns=4)

    # Limpiar el flag de reset si existe
    if st.session_state.get('_filters_resetting', False):
        st.session_state['_filters_resetting'] = False
        st.rerun()  # Solo un rerun DESPUÉS de que todo se limpió

    # Estructura de botones
    col1, col2, _ = st.columns(3, vertical_alignment='bottom')

    # Botones de búsqueda
    buscar = col1.button('Buscar', type='primary', use_container_width=True, key='buscar')

    # Botón de reinicio de filtros
    reinicio = col2.button("Reiniciar filtros", type='primary', use_container_width=True, key='reiniciar', on_click=reset_all_filters)

    # =========== Filtro Bienes ============ #
    dict_filtros_bienes_usuario = {'CADENA_BIENES' : session_state['bienes']['CADENA_BIENES'],
                                    'SECTOR_BIENES' : session_state['bienes']['SECTOR_BIENES'],
                                    'SUBSECTOR_BIENES' : session_state['bienes']['SUBSECTOR_BIENES'],
                                    'COD_POSICION_ARANCELARIA_BIENES' : session_state['bienes']['COD_POSICION_ARANCELARIA_BIENES'],
                                    'DESC_POSICION_ARANCELARIA_BIENES' : session_state['bienes']['DESC_POSICION_ARANCELARIA_BIENES'],
                                    'HUB_BIENES' : session_state['bienes']['HUB_BIENES'],
                                    'PAIS_DESTINO_BIENES' : session_state['bienes']['PAIS_DESTINO_BIENES'],
                                    'VALOR_AGREGADO_EXPO_BIENES' : session_state['bienes']['VALOR_AGREGADO_EXPO_BIENES'],
                                    'TAMANO_TEJIDO' : session_state['bienes']['TAMANO_TEJIDO']
                                    }  
        
    # =========== Búsqueda del usuario ============ #

    if buscar:

        with st.spinner("Ejecutando consulta... :surfing_woman:"):

            # Barra de progreso y realiza la lógica pesada
            progress_bar = st.progress(0)

            # Crear payload con los filtros seleccionados por el usuario
            payload = {
                "bienes": dict_filtros_bienes_usuario,
            }

            # Convertir a cadena JSON
            payload_json = json.dumps(payload, ensure_ascii=False)

            # Guardar payload en Session State para futuras referencias
            session_state['payload_bienes'] = payload_json
            
            # Registrar el evento de busqueda
            registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Valor agregado', detalle_evento='Búsqueda de empresas exportadoras', filtros=payload_json)
            progress_bar.progress(5)

            # Crear query
            sql_query = query_data_bienes(dict_columnas = dict_query_bienes, 
                                                filtros_generales=dict_filtros_bienes_usuario)
            progress_bar.progress(10)

            # Ejecutar consulta y guardar resultado en Session State
            session_state['df_valor_agregado'] = st.session_state.session.sql(sql_query)
            progress_bar.progress(15)

            # Contar registros
            session_state['total_registros'] = session_state['df_valor_agregado'].count()

            # Procesar df si hay datos
            if session_state['total_registros'] > 0:

                # Parámetros de colores
                list_color = ["#343363", "#1a3a79", "#2f55c8", "#4a79f3", "#829df5"]

                # Nombres para las pestañas

                # Año cerrado (primero y último de la lista)
                tab1_title = f"Año Cerrado: ({periodos_cerrados[0]} - {periodos_cerrados[-1]}) :chart_with_upwards_trend:"
                # Año corrido
                tab2_title = f"Año Corrido: ({periodos_corridos[0]} - {periodos_corridos[1]}) :bar_chart:"

                # Tabla de datos
                tab3_title = "Tablas de Datos :books:"
                progress_bar.progress(20)

                #########
                # Cadenas
                #########

                try:
                    (st.session_state['df_cadenas_cerrado'], 
                    st.session_state['df_cadenas_cerrado_formato'],
                    st.session_state['df_cadenas_corrido'], 
                    st.session_state['df_cadenas_corrido_formato'],
                    st.session_state['df_total_cadenas'],
                    st.session_state['df_total_cadenas_formato']) = resumen_valor_agregado(df_snowpark=session_state['df_valor_agregado'], 
                                                                                            periodos_cerrados=periodos_cerrados, 
                                                                                            periodos_corridos=periodos_corridos)
                except Exception as e:
                    st.session_state['df_cadenas_cerrado'] = pd.DataFrame()
                    st.session_state['df_cadenas_cerrado_formato'] = pd.DataFrame()
                    st.session_state['df_cadenas_corrido'] = pd.DataFrame()
                    st.session_state['df_cadenas_corrido_formato'] = pd.DataFrame()
                    st.session_state['df_total_cadenas'] = pd.DataFrame()
                    st.session_state['df_total_cadenas_formato'] = pd.DataFrame()

                # Gráfico cerrado
                st.session_state['fig_cadenas_cerrado'] = grafico_barras_periodos_seleccionados(df=st.session_state['df_cadenas_cerrado'],
                    df_formateado=st.session_state['df_cadenas_cerrado_formato'],
                    columna_agrupacion='Valor agregado',
                    periodos_a_mostrar=periodos_cerrados,
                    orientacion='horizontal',
                    list_color=list_color
                )

                # Gráfico corrido
                if disponibilidad_periodos_corridos_usd == 'Si':
                    st.session_state['fig_cadenas_corrido'] = grafico_barras_periodos_seleccionados(df=st.session_state['df_cadenas_corrido'],
                        df_formateado=st.session_state['df_cadenas_corrido_formato'],
                        columna_agrupacion='Valor agregado',
                        periodos_a_mostrar=periodos_corridos,
                        orientacion='horizontal',
                        list_color=list_color
                    )
                progress_bar.progress(30)

                #########################################################
                # Gráficos por valor agregado por producto y departamento
                #########################################################

                # Diccionario con nombres simplificados para las categorías de valor agregado
                cat_va = {
                    'manufactura_alta_tecnologia': 'Manufactura de alta tecnología',
                    'servicios_alta_tecnologia': 'Servicios de alta tecnología intensivos en conocimiento',
                    'manufacturas_baja_tecnologia': 'Manufacturas de baja tecnologia',
                    'manufacturas_recursos_naturales': 'Manufacturas basadas en recursos naturales',
                    'otras_transacciones': 'Otras transacciones',
                    'manufacturas_tecnologia_media': 'Manufacturas de tecnología media',
                    'otros_servicios_conocimiento': 'Otros servicios intensivos en conocimiento',
                    'servicios_mercado_conocimiento': 'Servicios de mercado intensivos en conocimiento',
                    'primarios': 'Primarios'
                }

                # Loop por categoria
                for key, categoria in cat_va.items():

                    # Crear nombres para guardar los dfs usando las llaves del diccionario

                    ###########
                    # Productos
                    ###########

                    # Base 
                    str_va_cerrado = 'df_va_cerrado_' + key
                    str_va_corrido = 'df_va_corrido_' + key
                    str_va_total = 'df_va_total_' + key

                    try:
                        (st.session_state[str_va_cerrado], 
                        st.session_state[str_va_cerrado + '_formato'],
                        st.session_state[str_va_corrido], 
                        st.session_state[str_va_corrido + '_formato'],
                        st.session_state[str_va_total],
                        st.session_state[str_va_total + '_formato']) = top_partidas_por_categoria(df_snowpark=session_state['df_valor_agregado'],
                                                                                                    periodos_cerrados=periodos_cerrados,
                                                                                                    periodos_corridos=periodos_corridos,
                                                                                                    categoria_valor=categoria)
                    except Exception as e:
                            st.session_state[str_va_cerrado] = pd.DataFrame()
                            st.session_state[str_va_cerrado + '_formato'] = pd.DataFrame()
                            st.session_state[str_va_corrido] = pd.DataFrame()
                            st.session_state[str_va_corrido + '_formato'] = pd.DataFrame()
                            st.session_state[str_va_total] = pd.DataFrame()
                            st.session_state[str_va_total + '_formato'] = pd.DataFrame()

                    # Gráficos cerrado
                    st.session_state['fig_' + str_va_cerrado] = grafico_barras_periodos_seleccionados(
                        df=st.session_state[str_va_cerrado],
                        df_formateado=st.session_state[str_va_cerrado + '_formato'],
                        columna_agrupacion='Posición Arancelaria',
                        periodos_a_mostrar=periodos_cerrados,
                        orientacion='horizontal',
                        list_color=list_color
                    )

                    # Gráficos corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        st.session_state['fig_' + str_va_corrido] = grafico_barras_periodos_seleccionados(
                            df=st.session_state[str_va_corrido],
                            df_formateado=st.session_state[str_va_corrido + '_formato'],
                            columna_agrupacion='Posición Arancelaria',
                            periodos_a_mostrar=periodos_corridos,
                            orientacion='horizontal',
                            list_color=list_color
                        )

                    ##############
                    # Departamento
                    ##############

                    str_dep_cerrado = 'df_dep_cerrado_' + key
                    str_dep_corrido = 'df_dep_corrido_' + key
                    str_dep_total = 'df_dep_total_' + key

                    try:
                        (st.session_state[str_dep_cerrado], 
                        st.session_state[str_dep_cerrado + '_formato'],
                        st.session_state[str_dep_corrido], 
                        st.session_state[str_dep_corrido + '_formato'],
                        st.session_state[str_dep_total],
                        st.session_state[str_dep_total + '_formato']) = top_partidas_por_departamento(df_snowpark=session_state['df_valor_agregado'],
                                                                                                        periodos_cerrados=periodos_cerrados,
                                                                                                        periodos_corridos=periodos_corridos,
                                                                                                        categoria_valor=categoria)
                    except Exception as e:
                            st.session_state[str_dep_cerrado] = pd.DataFrame()
                            st.session_state[str_dep_cerrado + '_formato'] = pd.DataFrame()
                            st.session_state[str_dep_corrido] = pd.DataFrame()
                            st.session_state[str_dep_corrido + '_formato'] = pd.DataFrame()
                            st.session_state[str_dep_total] = pd.DataFrame()
                            st.session_state[str_dep_total + '_formato'] = pd.DataFrame()
                    
                    # Gráficos cerrado
                    st.session_state['fig_' + str_dep_cerrado] = grafico_barras_periodos_seleccionados(df=st.session_state[str_dep_cerrado],
                        df_formateado=st.session_state[str_dep_cerrado + '_formato'],
                        columna_agrupacion='Departamento',
                        periodos_a_mostrar=periodos_cerrados,
                        orientacion='horizontal',
                        list_color=list_color
                    )

                    # Gráficos corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        st.session_state['fig_' + str_dep_corrido] = grafico_barras_periodos_seleccionados(df=st.session_state[str_dep_corrido],
                            df_formateado=st.session_state[str_dep_corrido + '_formato'],
                            columna_agrupacion='Departamento',
                            periodos_a_mostrar=periodos_corridos,
                            orientacion='horizontal',
                            list_color=list_color
                        )
                    progress_bar.progress(60)

                ######################################################
                # Valor exportado por departamento y valor agregado 
                ######################################################

                try:
                    # Datos para la UI (Año único crudo y formateado)
                    (st.session_state['df_valor_dep_cerrado'], 
                     st.session_state['df_valor_dep_cerrado_fmt']) = valor_exportado_departamento_periodo(df_snowpark = session_state['df_valor_agregado'], 
                                                                                    periodo=periodos_cerrados_conteo)
                                                                                    
                    (st.session_state['df_valor_dep_corrido'], 
                     st.session_state['df_valor_dep_corrido_fmt']) = valor_exportado_departamento_periodo(df_snowpark = session_state['df_valor_agregado'], 
                                                                                    periodo=periodos_corridos_conteo)
                    
                    # Datos para la Descarga (Todos los años en formato long)
                    st.session_state['df_valor_dep_long'] = valor_exportado_departamento_long(df_snowpark = session_state['df_valor_agregado'])
                    
                except Exception as e:
                    st.session_state['df_valor_dep_cerrado'] = pd.DataFrame()
                    st.session_state['df_valor_dep_cerrado_fmt'] = pd.DataFrame()
                    st.session_state['df_valor_dep_corrido'] = pd.DataFrame()
                    st.session_state['df_valor_dep_corrido_fmt'] = pd.DataFrame()
                    st.session_state['df_valor_dep_long'] = pd.DataFrame()
                progress_bar.progress(80)

            ####################
            # Mostrar resultados
            ####################

            fuente_datos = 'RUES, SUPERSOCIEDADES, DANE-DIAN, CRM - Cálculos ProColombia'

            #########
            # Cadenas
            #########

            with st.container(height = 850, border=True):

                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Valor exportado por clasificación de valor agregado</h4>', unsafe_allow_html=True)

                    # Crear pestañas para gráficos y tablas
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        tab1, tab2, tab3 = st.tabs([tab1_title, tab2_title, tab3_title])
                    else:
                        tab1, tab3 = st.tabs([tab1_title, tab3_title])
                    # Pestaña 1: Año cerrado
                    with tab1:
                        # Gráfico
                        mostrar_resultado_en_streamlit(resultado=st.session_state['fig_cadenas_cerrado'], fuente=fuente_datos, llave='graph_1')
                        # Nota
                        st.caption('**Nota:** M (millones).')
                    # Pestaña 2: Año corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        with tab2:
                            # Gráfico
                            mostrar_resultado_en_streamlit(resultado=st.session_state['fig_cadenas_corrido'], fuente=fuente_datos, llave='graph_2')
                            # Nota
                            st.caption('**Nota:** M (millones).')
                    # Pestaña 3: Tablas de datos
                    with tab3:
                        # Mostrar los resultados si hay datos disponible
                        if not st.session_state['df_total_cadenas_formato'].empty:
                            # Tabla
                            st.dataframe(st.session_state['df_total_cadenas_formato'], use_container_width=True, hide_index=True)
                            # Nota
                            st.caption('**Nota:** M (millones).')
                        else:
                            st.error("No se encontro información que cumpla con los filtros seleccionados.")

            with st.container(height = 75, border=True):                        
                # Botón de descarga fuera del contenedor del gráfico
                if not st.session_state['df_total_cadenas'].empty:
                    descarga_tabla(
                    df=st.session_state['df_total_cadenas'],
                    row_threshhold=100000,
                    label_descarga="Descargar resultados",
                    file_name='Valor exportado por cadena y clasificación de valor agregado',
                    key_descarga='tabla_1',
                    sesion_activa=st.session_state.session,
                    tipo_evento="Descarga gráfico - Valor exportado por cadena y clasificación de valor agregado",
                    pagina="Valor agregado",
                    filtros=payload_json,
                    nota = "Los valores están en dólares FOB",
                    agregar_nota = True
                    )
                else:
                    st.markdown("No hay datos disponibles para descargar.")

            ###########################################################        
            # Valor exportado por departamento y valor agregado
            ###########################################################

            progress_bar.progress(90)
            st.divider()
            with st.container(height = 700, border=True):

                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Valor exportado por departamento de origen y clasificación de valor agregado</h4>', unsafe_allow_html=True)

                    # Nota
                    st.markdown(f'<h6 class="custom-header" style="text-align:center;">(En dólares FOB)</h6>', unsafe_allow_html=True)

                    # Año cerrado (primero y último de la lista)
                    tab1_title_conteo = f"Año Cerrado: ({periodos_cerrados_conteo[0]}) :chart_with_upwards_trend:"
                    # Año corrido
                    tab2_title_conteo = f"Año Corrido: ({periodos_corridos_conteo[0]}) :bar_chart:"

                    # Crear pestañas para gráficos y tablas
                    if disponibilidad_periodos_corridos_conteo == 'Si':
                        tab1, tab2 = st.tabs([tab1_title_conteo, tab2_title_conteo])
                    else:
                        tab1, = st.tabs([tab1_title_conteo])

                    # Pestaña 1: Año cerrado
                    with tab1:
                        if not st.session_state['df_valor_dep_cerrado_fmt'].empty:
                            # Tabla (Muestra el año único FORMATEADO)
                            st.dataframe(st.session_state['df_valor_dep_cerrado_fmt'], use_container_width=True, hide_index=True)
                            # Nota
                            st.caption('**Nota:** M (millones).')
                            # Botón de descarga (Exporta el histórico completo en formato long)
                            descarga_tabla(
                            df=st.session_state['df_valor_dep_long'], 
                            row_threshhold=100000,
                            label_descarga="Descargar resultados",
                            file_name='Valor exportado por departamento y clasificacion de valor agregado',
                            key_descarga='tabla_2',
                            sesion_activa=st.session_state.session,
                            tipo_evento="Descarga tabla - Valor exportado por departamento y clasificacion de valor agregado",
                            pagina="Valor agregado",
                            filtros=payload_json
                            )
                        else:
                            st.markdown("No hay datos disponibles para descargar.")
                    
                    # Pestaña 2: Año corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        with tab2:
                            if not st.session_state['df_valor_dep_corrido_fmt'].empty:
                                # Tabla (Muestra el año único FORMATEADO)
                                st.dataframe(st.session_state['df_valor_dep_corrido_fmt'], use_container_width=True, hide_index=True)
                                # Nota
                                st.caption('**Nota:** M (millones).')
                                # Botón de descarga (Exporta el histórico completo en formato long)
                                descarga_tabla(
                                df=st.session_state['df_valor_dep_long'], 
                                row_threshhold=100000,
                                label_descarga="Descargar resultados",
                                file_name='Valor exportado por departamento y clasificacion de valor agregado',
                                key_descarga='tabla_3',
                                sesion_activa=st.session_state.session,
                                tipo_evento="Descarga tabla - Valor exportado por departamento y clasificacion de valor agregado",
                                pagina="Valor agregado",
                                filtros=payload_json
                                )
                            else:
                                st.markdown("No hay datos disponibles para descargar.")
        
            ##################################
            # Valor agregado por clasificación
            ##################################

            st.divider()

            # Diccionarios con nombres simplicados para las categorías de valor agregado
            # Manufacturas
            cat_va_manufacturas = {
                'manufactura_alta_tecnologia': 'Manufactura de alta tecnología',
                'manufacturas_tecnologia_media': 'Manufacturas de tecnología media',
                'manufacturas_baja_tecnologia': 'Manufacturas de baja tecnologia',
                'manufacturas_recursos_naturales': 'Manufacturas basadas en recursos naturales',
                'primarios': 'Primarios'
            }
            # Servicios
            cat_va_servicios = {
                'servicios_alta_tecnologia': 'Servicios de alta tecnología intensivos en conocimiento',
                'servicios_mercado_conocimiento': 'Servicios de mercado intensivos en conocimiento',
                'otros_servicios_conocimiento': 'Otros servicios intensivos en conocimiento'
            }
            # Otras transacciones
            cat_va_otras_transacciones = {
                'otras_transacciones': 'Otras transacciones'
            }

            # Nombres de tabs
            tabs_titles = [tab1_title, tab2_title, tab3_title]
            
            # Título principal
            with st.container(height=75, border=True):
                st.markdown(f'<h4 class="custom-header" style="text-align:center;">Top 10 productos exportados por clasificación de valor agregado</h4>', unsafe_allow_html=True)

            # ID
            counter = 111

            # Agrupar los diccionarios para iterar sobre ellos ordenadamente
            grupos_categorias = [
                ("Manufacturas", cat_va_manufacturas),
                ("Servicios", cat_va_servicios),
                ("Otras transacciones", cat_va_otras_transacciones)
            ]

            # Loop por cada macro-categoría (Manufacturas, Servicios, etc.)
            for nombre_grupo, diccionario_grupo in grupos_categorias:
                
                # Subtítulo para separar visualmente en la interfaz
                st.markdown(f"### **{nombre_grupo}**")

                # Expander
                with st.expander("Expande para más detalles sobre esta categoría", expanded=False):
                
                    # Loop por categoría individual dentro del grupo
                    for key, categoria in diccionario_grupo.items():

                        # Base 
                        str_va_cerrado = 'df_va_cerrado_' + key
                        str_va_corrido = 'df_va_corrido_' + key
                        str_va_total = 'df_va_total_' + key

                        # Mostrar resultado
                        renderizar_seccion_valor_agregado(
                                                        # 1. Contenido Visual
                                                        titulo_seccion = f'{categoria}',
                                                        titulos_tabs = tabs_titles,
                                                        fuente_datos = fuente_datos,
                                                        
                                                        # 2. Llaves de Session State de obejtos
                                                        key_fig_cerrado = 'fig_' + str_va_cerrado,
                                                        key_fig_corrido = 'fig_' + str_va_corrido,
                                                        key_df_formato = str_va_total + '_formato',
                                                        key_df_download = str_va_total,
                                                        
                                                        # 3. Llaves para Widgets (Streamlit Keys únicas)
                                                        widget_key_graph_cerrado = f'graph_cerrado_{counter}',
                                                        widget_key_graph_corrido = f'graph_corrido_{counter}',
                                                        widget_key_boton_descarga = f'tabla_cerrado_{counter}',
                                                        
                                                        # 4. Parámetros de Descarga y Analítica
                                                        nombre_archivo_descarga = f'Top 10 productos exportados por clasificación de valor agregado: {categoria}',
                                                        evento_analitica = f'Top 10 productos exportados por clasificación de valor agregado: {categoria}',
                                                        filtros_json = payload_json,

                                                        # 5. Parámetro de disponibilidad de datos de año corrido
                                                        disponibilidad_periodos_corridos_usd = disponibilidad_periodos_corridos_usd
                                                                        )

                        # Incrementar contador para keys únicas
                        counter = counter + 1

            ##################################
            # Valor agregado por departamento
            ##################################

            st.divider()

            # Nombres de tabs
            tabs_titles = [tab1_title, tab2_title, tab3_title]
            
            # Título
            progress_bar.progress(100)
            with st.container(height = 75, border=True):
                st.markdown(f'<h4 class="custom-header" style="text-align:center;">Exportaciones por departamento y clasificación de valor agregado</h4>', unsafe_allow_html=True)

            # ID
            counter = 222

            # Loop por cada macro-categoría usando la lista 'grupos_categorias' previamente definida
            for nombre_grupo, diccionario_grupo in grupos_categorias:
                
                # Subtítulo para separar visualmente en la interfaz
                st.markdown(f"### **{nombre_grupo}**")

                # Expander
                with st.expander("Expande para más detalles sobre esta categoría", expanded=False):

                    # Loop por categoria individual dentro del grupo
                    for key, categoria in diccionario_grupo.items():

                        # Base 
                        str_dep_cerrado = 'df_dep_cerrado_' + key
                        str_dep_corrido = 'df_dep_corrido_' + key
                        str_dep_total = 'df_dep_total_' + key

                        # Mostrar resultado
                        renderizar_seccion_valor_agregado(
                                                        # 1. Contenido Visual
                                                        titulo_seccion = f'{categoria}',
                                                        titulos_tabs = tabs_titles,
                                                        fuente_datos = fuente_datos,
                                                        
                                                        # 2. Llaves de Session State de obejtos
                                                        key_fig_cerrado = 'fig_' + str_dep_cerrado,
                                                        key_fig_corrido = 'fig_' + str_dep_corrido,
                                                        key_df_formato = str_dep_total + '_formato',
                                                        key_df_download = str_dep_total,
                                                        
                                                        # 3. Llaves para Widgets (Streamlit Keys únicas)
                                                        widget_key_graph_cerrado = f'graph_cerrado_{counter}',
                                                        widget_key_graph_corrido = f'graph_corrido_{counter}',
                                                        widget_key_boton_descarga = f'tabla_cerrado_{counter}',
                                                        
                                                        # 4. Parámetros de Descarga y Analítica
                                                        nombre_archivo_descarga = f'Exportaciones por departamento y clasificación de valor agregado: {categoria}',
                                                        evento_analitica = f'Exportaciones por departamento y clasificación de valor agregado: {categoria}',
                                                        filtros_json = payload_json,

                                                        # 5. Parámetro de disponibilidad de datos de año corrido
                                                        disponibilidad_periodos_corridos_usd = disponibilidad_periodos_corridos_usd
                        )

                        # Incrementar contador para keys únicas
                        counter = counter + 1

# ========== Footer ==========#
footer()   


