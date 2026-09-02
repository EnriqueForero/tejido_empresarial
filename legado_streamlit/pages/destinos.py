#============= Bibliotecas =============#
# Bibliotecas Externas
import streamlit as st
from streamlit import session_state
import json
from datetime import timedelta
import pandas as pd

# Módulos Propios
from src.streamlit_analitica import navbar, footer
# Funciones de la página de destinos
from src.pages_utils.destinos_utils import ls_filtros_bienes, dict_filtros_bienes, dict_query_bienes, query_data_bienes, resumen_por_cadena, resumen_por_tamano, resumen_por_pais, resumen_por_pais_tamano, resumen_por_razon_social, conteo_empresas_exportadoras, grafico_barras_periodos_seleccionados
# Parámetros
from src.pages_utils.config import periodos_cerrados, periodos_corridos, disponibilidad_periodos_corridos_usd
# Funciones de ayuda
from src.pages_utils.utils import load_filtros_bienes, descarga_tabla, mostrar_resultado_en_streamlit
# Consulta segura Snowflake
from src.snowflake_analitica import registrar_evento, flujo_snowflake, update_last_activity
# Filtros dinámicos
from src.filtros_dinamicos_analitica import DynamicFilters

# ================== Configuración inicial ====================
# Configuración básica de la página en Streamlit.
st.set_page_config(
    page_title="Destinos",
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
    st.query_params.page = '4'  # Página predeterminada si no hay parámetro 'page' en la URL.

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
if st.query_params.page == '5':
    st.switch_page("pages/valor_agregado.py") # Redirige a la página de valor agregado
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

    # 3. Limpiar DataFrames de resultados y estado de descarga
    for k in (
        # Resultados de consulta principal
        'df_destinos',
        'total_registros',
        'payload_bienes',
        
        # DataFrames de Cadenas
        'df_cadenas',
        'df_cadenas_formato',
        'graph_cadenas_cerrado',
        'graph_cadenas_corrido',
        
        # DataFrames de Tamaño
        'df_tamano',
        'df_tamano_formato',
        'graph_tamano_cerrado',
        'graph_tamano_corrido',
        
        # DataFrames de País
        'df_pais',
        'df_pais_formato',
        'graph_pais_cerrado',
        'graph_pais_corrido',
        
        # DataFrames de País y Tamaño
        'df_pais_tamano',
        'df_pais_tamano_formato',
        
        # DataFrames de Empresas
        'df_empresas',
        'df_empresas_formato',
        'graph_empresas_cerrado',
        'graph_empresas_corrido',
        
        # DataFrames de Conteo de Empresas
        'df_empresas_conteo',
        'df_empresas_conteo_formato',
        'df_empresas_conteo_graph',
        'df_empresas_conteo_formato_graph',
        'graph_empresas_conteo_cerrado'
    ):
        st.session_state.pop(k, None)

# =========== BODY ===========
with body:
    
    # Título y fuentes 
    st.markdown("## **Destinos**")
    st.caption(":blue[Fuente: RUES, SUPERSOCIEDADES, DANE-DIAN, CRM PROCOLOMBIA.]")
    st.caption(":blue[Nota: Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.]")
    
    # Mensaje informativo
    st.info(
        "💡 **¿Qué puedes analizar en esta página?**\n"
        "* **Mercados objetivo:** Inicia tu búsqueda utilizando los filtros principales de **HUB** y **País de destino** para enfocar tu análisis.\n"
        "* **Comportamiento exportador:** Observa cómo se distribuyen las exportaciones hacia esos destinos según la **Cadena productiva** y el **Tamaño de la empresa**.\n"
        "* **Top de exportaciones:** Descubre la composición de las exportaciones por **país**, la cantidad de empresas que llegan a ellos y las **principales empresas** colombianas en esos mercados.", 
        icon="🌎"
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
    dict_filtros_bienes_usuario = {# Filtros de países
                                   'HUB_BIENES' : session_state['bienes']['HUB_BIENES'],
                                   'PAIS_DESTINO_BIENES' : session_state['bienes']['PAIS_DESTINO_BIENES'],
                                   'CADENA_BIENES' : session_state['bienes']['CADENA_BIENES'],
                                   'SECTOR_BIENES' : session_state['bienes']['SECTOR_BIENES'],
                                   'COD_POSICION_ARANCELARIA_BIENES' : session_state['bienes']['COD_POSICION_ARANCELARIA_BIENES'],
                                   'DESC_POSICION_ARANCELARIA_BIENES' : session_state['bienes']['DESC_POSICION_ARANCELARIA_BIENES'],
                                   'SUBSECTOR_BIENES' : session_state['bienes']['SUBSECTOR_BIENES'],
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
            registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Destinos', detalle_evento='Búsqueda de empresas exportadoras', filtros=payload_json)

            # Crear query
            sql_query = query_data_bienes(dict_columnas = dict_query_bienes, 
                                                filtros_generales=dict_filtros_bienes_usuario)
            progress_bar.progress(5)

            # Ejecutar consulta y guardar resultado en Session State
            session_state['df_destinos'] = st.session_state.session.sql(sql_query)
            progress_bar.progress(15)

            # Contar registros
            session_state['total_registros'] = session_state['df_destinos'].count()

            # Procesar df si hay datos
            if session_state['total_registros'] > 0:

                # Parámetros de colores
                list_color = ["#343363", "#1a3a79", "#2f55c8", "#4a79f3", "#829df5"]

                # Nombres para las pestañas

                # Año cerrado (primero y último de la lista)
                tab1_title = f"Año Cerrado: ({periodos_cerrados[0]} - {periodos_cerrados[-1]}) :chart_with_upwards_trend:"
                # Año corrido
                if disponibilidad_periodos_corridos_usd == 'Si':
                    tab2_title = f"Año Corrido: ({periodos_corridos[0]} - {periodos_corridos[1]}) :bar_chart:"

                # Tabla de datos
                tab3_title = "Tablas de Datos :books:"
                progress_bar.progress(20)

                #########
                # Cadenas
                #########

                try:
                    (st.session_state['df_cadenas'], 
                    st.session_state['df_cadenas_formato']) = resumen_por_cadena(df_snowpark=session_state['df_destinos'])
                except Exception as e:
                    st.session_state['df_cadenas'] = pd.DataFrame()
                    st.session_state['df_cadenas_formato'] = pd.DataFrame()
                
                # Gráfico cerrado
                st.session_state['graph_cadenas_cerrado'] = grafico_barras_periodos_seleccionados(
                    df=st.session_state['df_cadenas'],
                    df_formateado=st.session_state['df_cadenas_formato'],
                    columna_agrupacion='Cadena Productiva',
                    periodos_a_mostrar=periodos_cerrados,
                    orientacion='vertical',
                    list_color=list_color
                )

                # Gráfico corrido
                if disponibilidad_periodos_corridos_usd == 'Si':
                    st.session_state['graph_cadenas_corrido'] = grafico_barras_periodos_seleccionados(
                        df=st.session_state['df_cadenas'],
                        df_formateado=st.session_state['df_cadenas_formato'],
                        columna_agrupacion='Cadena Productiva',
                        periodos_a_mostrar=periodos_corridos,
                        orientacion='vertical',
                        list_color=list_color
                    )
                progress_bar.progress(40)
                
                ########
                # Tamaño
                ########

                try:
                    (st.session_state['df_tamano'], 
                    st.session_state['df_tamano_formato']) = resumen_por_tamano(df_snowpark=session_state['df_destinos'])
                    # Llenar vaciós de la columna 'Tamaño de la Empresa' por debug mientras hay datos nuevos
                    st.session_state['df_tamano']['Tamaño de la Empresa'] = st.session_state['df_tamano']['Tamaño de la Empresa'].fillna('No Definido')
                    st.session_state['df_tamano_formato']['Tamaño de la Empresa'] = st.session_state['df_tamano_formato']   ['Tamaño de la Empresa'].fillna('No Definido')
                except Exception as e:
                    st.session_state['df_tamano'] = pd.DataFrame()
                    st.session_state['df_tamano_formato'] = pd.DataFrame()
                
                # Gráfico cerrado
                st.session_state['graph_tamano_cerrado'] = grafico_barras_periodos_seleccionados(
                    df=st.session_state['df_tamano'],
                    df_formateado=st.session_state['df_tamano_formato'],
                    columna_agrupacion='Tamaño de la Empresa',
                    periodos_a_mostrar=periodos_cerrados,
                    orientacion='vertical',
                    list_color=list_color
                )

                # Gráfico corrido
                if disponibilidad_periodos_corridos_usd == 'Si':
                    st.session_state['graph_tamano_corrido'] = grafico_barras_periodos_seleccionados(
                        df=st.session_state['df_tamano'],
                        df_formateado=st.session_state['df_tamano_formato'],
                        columna_agrupacion='Tamaño de la Empresa',
                        periodos_a_mostrar=periodos_corridos,
                        orientacion='vertical',
                        list_color=list_color
                    )
                progress_bar.progress(50)
                
                ######
                # País
                ######
                
                try:
                    (st.session_state['df_pais'], 
                    st.session_state['df_pais_formato']) = resumen_por_pais(df_snowpark=session_state['df_destinos'])
                except Exception as e:
                    st.session_state['df_pais'] = pd.DataFrame()
                    st.session_state['df_pais_formato'] = pd.DataFrame()
                
                # Gráfico cerrado
                st.session_state['graph_pais_cerrado'] = grafico_barras_periodos_seleccionados(
                    df=st.session_state['df_pais'].head(5),
                    df_formateado=st.session_state['df_pais_formato'].head(5),
                    columna_agrupacion='País',
                    periodos_a_mostrar=periodos_cerrados,
                    orientacion='vertical',
                    list_color=list_color
                )

                # Gráfico corrido
                if disponibilidad_periodos_corridos_usd == 'Si':
                    st.session_state['graph_pais_corrido'] = grafico_barras_periodos_seleccionados(
                        df=st.session_state['df_pais'].head(5),
                        df_formateado=st.session_state['df_pais_formato'].head(5),
                        columna_agrupacion='País',
                        periodos_a_mostrar=periodos_corridos,
                        orientacion='vertical',
                        list_color=list_color
                    )
                progress_bar.progress(60)
                
                ###############
                # País y Tamaño
                ###############
                
                try:
                    (st.session_state['df_pais_tamano'], 
                    st.session_state['df_pais_tamano_formato']) = resumen_por_pais_tamano(df_snowpark=session_state['df_destinos'])
                except Exception as e:
                    st.session_state['df_pais_tamano'] = pd.DataFrame()
                    st.session_state['df_pais_tamano_formato'] = pd.DataFrame()
                progress_bar.progress(70)
                
                ##############
                # Razón Social
                ##############
                
                try:
                    (st.session_state['df_empresas'], 
                    st.session_state['df_empresas_formato']) = resumen_por_razon_social(df_snowpark=session_state['df_destinos'])
                except Exception as e:
                    st.session_state['df_empresas'] = pd.DataFrame()
                    st.session_state['df_empresas_formato'] = pd.DataFrame()
                
                # Gráfico cerrado
                st.session_state['graph_empresas_cerrado'] = grafico_barras_periodos_seleccionados(
                    df=st.session_state['df_empresas'].head(5),
                    df_formateado=st.session_state['df_empresas_formato'].head(5),
                    columna_agrupacion='Razón Social',
                    periodos_a_mostrar=periodos_cerrados,
                    orientacion='horizontal',
                    list_color=list_color
                )

                # Gráfico corrido
                if disponibilidad_periodos_corridos_usd == 'Si':
                    st.session_state['graph_empresas_corrido'] = grafico_barras_periodos_seleccionados(
                        df=st.session_state['df_empresas'].head(5),
                        df_formateado=st.session_state['df_empresas_formato'].head(5),
                        columna_agrupacion='Razón Social',
                        periodos_a_mostrar=periodos_corridos,
                        orientacion='horizontal',
                        list_color=list_color
                    )
                progress_bar.progress(75)
                
                #################################
                # Conteo de empresas exportadoras
                #################################

                try:
                    (st.session_state['df_empresas_conteo'], 
                     st.session_state['df_empresas_conteo_formato']) = conteo_empresas_exportadoras(df_snowpark=session_state['df_destinos'])
                except Exception as e:
                    st.session_state['df_empresas_conteo'] = pd.DataFrame()
                    st.session_state['df_empresas_conteo_formato'] = pd.DataFrame()
                
                 # Renombrar la columna 'Empresas' para que contenga 'USD'
                st.session_state['df_empresas_conteo_graph'] = st.session_state['df_empresas_conteo'].rename(columns={'Empresas': 'USD Empresas'})
                st.session_state['df_empresas_conteo_formato_graph'] = st.session_state['df_empresas_conteo_formato'].rename(columns={'Empresas': 'USD Empresas'})

                # Gráfico cerrado
                st.session_state['graph_empresas_conteo_cerrado'] = grafico_barras_periodos_seleccionados(
                    df=st.session_state['df_empresas_conteo_graph'].head(10),
                    df_formateado=st.session_state['df_empresas_conteo_formato_graph'].head(10),
                    columna_agrupacion='País',
                    periodos_a_mostrar=['USD Empresas'],
                    orientacion='vertical',
                    list_color=list_color
                )
                
                ####################
                # Mostrar resultados
                ####################

                fuente_datos = 'RUES, SUPERSOCIEDADES, DANE-DIAN, CRM - Cálculos ProColombia'

                ######
                # País
                ######

                progress_bar.progress(85)
                with st.container(height = 850, border=True):
    
                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Top de Mercados por Valor Exportado</h4>', unsafe_allow_html=True)

                    # Crear pestañas para gráficos y tablas
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        tab1, tab2, tab3 = st.tabs([tab1_title, tab2_title, tab3_title])
                    else:
                        tab1, tab3 = st.tabs([tab1_title, tab3_title])
                    # Pestaña 1: Año cerrado
                    with tab1:
                        # Gráfico
                        mostrar_resultado_en_streamlit(resultado=st.session_state['graph_pais_cerrado'], fuente=fuente_datos, llave='graph_pais_cerrado')
                        # Nota
                        st.caption('**Nota:** M (millones).')
                    # Pestaña 2: Año corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        with tab2:
                            # Gráfico
                            mostrar_resultado_en_streamlit(resultado=st.session_state['graph_pais_corrido'], fuente=fuente_datos, llave='graph_pais_corrido')
                            # Nota
                            st.caption('**Nota:** M (millones).')
                    # Pestaña 3: Tablas de datos
                    with tab3:
                        # Mostrar los resultados si hay datos disponible
                        if not st.session_state['df_pais_formato'].empty:
                            # Tabla
                            st.dataframe(st.session_state['df_pais_formato'].head(5), use_container_width=True, hide_index=True)
                            # Nota
                            st.caption('**Nota:** M (millones).')
                        else:
                            st.error("No se encontró información que cumpla con los filtros seleccionados.")
                    # Botón de descarga fuera del contenedor del gráfico
                    if not st.session_state['df_pais'].empty:
                        descarga_tabla(
                        df=st.session_state['df_pais'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Top de Mercados por Valor Exportado',
                        key_descarga='tabla_exportaciones_pais',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Top de Mercados por Valor Exportado",
                        pagina="Destinos",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                #########
                # Cadenas
                #########

                with st.container(height = 850, border=True):
    
                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Participación de las Exportaciones Colombianas por Cadena</h4>', unsafe_allow_html=True)

                    # Crear pestañas para gráficos y tablas
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        tab1, tab2, tab3 = st.tabs([tab1_title, tab2_title, tab3_title])
                    else:
                        tab1, tab3 = st.tabs([tab1_title, tab3_title])
                    # Pestaña 1: Año cerrado
                    with tab1:
                        # Gráfico
                        mostrar_resultado_en_streamlit(resultado=st.session_state['graph_cadenas_cerrado'], fuente=fuente_datos, llave='graph_cadenas_cerrado')
                        # Nota
                        st.caption('**Nota:** M (millones).')
                    # Pestaña 2: Año corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        with tab2:
                            # Gráfico
                            mostrar_resultado_en_streamlit(resultado=st.session_state['graph_cadenas_corrido'], fuente=fuente_datos, llave='graph_cadenas_corrido')
                            # Nota
                            st.caption('**Nota:** M (millones).')
                    # Pestaña 3: Tablas de datos
                    with tab3:
                        # Mostrar los resultados si hay datos disponible
                        if not st.session_state['df_cadenas_formato'].empty:
                            # Tabla
                            st.dataframe(st.session_state['df_cadenas_formato'], use_container_width=True, hide_index=True)
                            # Nota
                            st.caption('**Nota:** M (millones).')
                        else:
                            st.error("No se encontró información que cumpla con los filtros seleccionados.")
                    # Botón de descarga fuera del contenedor del gráfico
                    if not st.session_state['df_cadenas'].empty:
                        descarga_tabla(
                        df=st.session_state['df_cadenas'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Participación de las Exportaciones Colombianas por Cadena',
                        key_descarga='tabla_exportaciones_cadena',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Participación de las Exportaciones Colombianas por Cadena",
                        pagina="Destinos",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                ########
                # Tamaño
                ########

                with st.container(height = 850, border=True):
    
                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Exportaciones por Tamaño de Empresa</h4>', unsafe_allow_html=True)

                    # Crear pestañas para gráficos y tablas
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        tab1, tab2, tab3 = st.tabs([tab1_title, tab2_title, tab3_title])
                    else:
                        tab1, tab3 = st.tabs([tab1_title, tab3_title])
                    # Pestaña 1: Año cerrado
                    with tab1:
                        # Gráfico
                        mostrar_resultado_en_streamlit(resultado=st.session_state['graph_tamano_cerrado'], fuente=fuente_datos, llave='graph_tamano_cerrado')
                        # Nota
                        st.caption('**Nota:** M (millones).')
                    # Pestaña 2: Año corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        with tab2:
                            # Gráfico
                            mostrar_resultado_en_streamlit(resultado=st.session_state['graph_tamano_corrido'], fuente=fuente_datos, llave='graph_tamano_corrido')
                            # Nota
                            st.caption('**Nota:** M (millones).')
                    # Pestaña 3: Tablas de datos
                    with tab3:
                        # Mostrar los resultados si hay datos disponible
                        if not st.session_state['df_tamano_formato'].empty:
                            # Tabla
                            st.dataframe(st.session_state['df_tamano_formato'], use_container_width=True, hide_index=True)
                            # Nota
                            st.caption('**Nota:** M (millones).')
                        else:
                            st.error("No se encontró información que cumpla con los filtros seleccionados.")
                    # Botón de descarga fuera del contenedor del gráfico
                    if not st.session_state['df_tamano'].empty:
                        descarga_tabla(
                        df=st.session_state['df_tamano'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Exportaciones por Tamaño de Empresa',
                        key_descarga='tabla_exportaciones_tamano',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Exportaciones por Tamaño de Empresa",
                        pagina="Destinos",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                #################################
                # Conteo de Empresas Exportadoras
                #################################

                progress_bar.progress(100)
                with st.container(height = 850, border=True):

                    anio_conteo = periodos_cerrados[-1].replace('USD ', '')

                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Número de Empresas Exportadoras ({anio_conteo})</h4>', unsafe_allow_html=True)

                    # Crear pestañas para gráficos y tablas
                    tab_conteo_title = f"Empresas exportadoras en {anio_conteo} :bar_chart:"
                    tab1, tab3 = st.tabs([tab_conteo_title, tab3_title])
                    # Pestaña 1: Año cerrado
                    with tab1:
                        # Gráfico
                        mostrar_resultado_en_streamlit(resultado=st.session_state['graph_empresas_conteo_cerrado'], fuente=fuente_datos, llave='graph_empresas_conteo_cerrado')
                    # Pestaña 3: Tablas de datos
                    with tab3:
                        # Mostrar los resultados si hay datos disponible
                        if not st.session_state['df_empresas_conteo_formato'].empty:
                            # Tabla
                            st.dataframe(st.session_state['df_empresas_conteo_formato'].head(10), use_container_width=True, hide_index=True)
                        else:
                            st.error("No se encontró información que cumpla con los filtros seleccionados.")
                    # Botón de descarga fuera del contenedor del gráfico
                    if not st.session_state['df_empresas_conteo'].empty:
                        descarga_tabla(
                        df=st.session_state['df_empresas_conteo'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Número de Empresas Exportadoras',
                        key_descarga='tabla_exportaciones_numero_empresas',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Número de Empresas Exportadoras",
                        pagina="Destinos",
                        filtros=payload_json
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                ##############
                # Razón Social
                ##############

                with st.container(height = 750, border=True):
    
                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align:center;">Principales Empresas Exportadoras</h4>', unsafe_allow_html=True)

                    # Crear pestañas para gráficos y tablas
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        tab1, tab2, tab3 = st.tabs([tab1_title, tab2_title, tab3_title])
                    else:
                        tab1, tab3 = st.tabs([tab1_title, tab3_title])
                    # Pestaña 1: Año cerrado
                    with tab1:
                        # Gráfico
                        mostrar_resultado_en_streamlit(resultado=st.session_state['graph_empresas_cerrado'], fuente=fuente_datos, llave='graph_empresas_cerrado')
                        # Nota
                        st.caption('**Nota:** M (millones).')
                    # Pestaña 2: Año corrido
                    if disponibilidad_periodos_corridos_usd == 'Si':
                        with tab2:
                            # Gráfico
                            mostrar_resultado_en_streamlit(resultado=st.session_state['graph_empresas_corrido'], fuente=fuente_datos, llave='graph_empresas_corrido')
                            # Nota
                            st.caption('**Nota:** M (millones).')
                    # Pestaña 3: Tablas de datos
                    with tab3:
                        # Mostrar los resultados si hay datos disponible
                        if not st.session_state['df_empresas_formato'].empty:
                            # Tabla
                            st.dataframe(st.session_state['df_empresas_formato'].head(5), use_container_width=True, hide_index=True)
                            # Nota
                            st.caption('**Nota:** M (millones).')
                        else:
                            st.error("No se encontró información que cumpla con los filtros seleccionados.")
                    # Botón de descarga fuera del contenedor del gráfico
                    if not st.session_state['df_empresas'].empty:
                        descarga_tabla(
                        df=st.session_state['df_empresas'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Principales Empresas Exportadoras',
                        key_descarga='tabla_exportaciones_razon_social',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga gráfico - Principales Empresas Exportadoras",
                        pagina="Destinos",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                    else:
                        st.markdown("No hay datos disponibles para descargar.")

                
                        

            # En caso de que no hayan resultados para la consulta específica
            else:
                st.error("No se encontró información que cumpla con los filtros seleccionados.")
# ========== Footer ==========#
footer()   


