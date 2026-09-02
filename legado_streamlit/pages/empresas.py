#============= Bibliotecas =============#
# Bibliotecas Externas
import streamlit as st
from streamlit import session_state
import json
from datetime import timedelta

# Módulos Propios
from src.streamlit_analitica import navbar, footer
# Funciones de la página de empresas 
from src.pages_utils.empresas_utils import ls_filtros_generales_empresas, dict_filtros_generales_empresas, dict_query_empresas, query_data_empresas, calcular_metricas_resumen, crear_resumen_por_tamano, crear_top_exportadoras, crear_empresas_por_tamano
# Parámetros
from src.pages_utils.config import servicios_anios_disponibles, negocios_anios_disponibles, exportaciones_anios_disponibles
# Funciones de ayuda
from src.pages_utils.utils import load_filtros_generales, format_espanol, descarga_tabla
# Consulta segura Snowflake
from src.snowflake_analitica import registrar_evento, flujo_snowflake, update_last_activity
# Filtros dinámicos
from src.filtros_dinamicos_analitica import DynamicFilters

# ================== Configuración inicial ====================
# Configuración básica de la página en Streamlit.
st.set_page_config(
    page_title="Empresas",
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
    st.query_params.page = '3'  # Página predeterminada si no hay parámetro 'page' en la URL.

# ================== navbar =========================
# Llamada al componente de navegación personalizada (barra de navegación).
navbar()

# Redirección condicional según el valor del parámetro 'page' en la URL.
if st.query_params.page == '1':
    st.switch_page("app.py")  # Redirige a la página de inicio.
if st.query_params.page == '2':
    st.switch_page("pages/segmentacion.py") # Redirige a la página de segmentación. 
if st.query_params.page == '4':
    st.switch_page("pages/destinos.py") # Redirige a la página de destinos
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
df_filtros_generales_empresas = load_filtros_generales(_session=st.session_state.session)

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
        if (k.startswith('generales'))
        and k != '_filters_resetting'
    ]
    for k in keys_to_delete:
        del st.session_state[k]

    # 2. Reinicializar los diccionarios de filtros con listas vacías
    st.session_state['generales'] = {k: [] for k in ls_filtros_generales_empresas}

    # 2.5. Limpiar explícitamente las keys de los widgets multiselect
    for filter_name in ls_filtros_generales_empresas:
        widget_key = 'generales' + filter_name
        st.session_state.pop(widget_key, None)    

    # 3. Limpiar DataFrames de resultados y estado de descarga
    for k in (
        # Resultados de consulta principal
        'df_empresas',
        
        # DataFrames de resumen
        'df_resumen_empresas',
        
        # Diccionarios de empresas por tamaño
        'dfs_empresas_por_tamano',
        'dfs_empresas_por_tamano_formateado',
        
        # Top exportadoras
        'df_empresas_top_exportadoras',
        'df_empresas_top_exportadoras_resumen',
        
        # Métricas de resumen
        'num_empresas',
        'num_empresas_potencial',
        'num_empresas_exportadoras',
        'valor_exportado',
        
        # Flags de descarga
        'tabla_tejido_resumen',
        'tabla_tejido_grandes',
        'tabla_tejido_medianas',
        'tabla_tejido_pequeñas',
        'tabla_tejido_micro',
        'tabla_tejido_no_determinado',
        'tabla_tejido_top_exportadoras',
    ):
        st.session_state.pop(k, None)

# =========== BODY ===========
with body:

    # Título y fuentes 
    st.markdown("## **Tejido empresarial**")
    st.caption(":blue[Fuente: RUES, SUPERSOCIEDADES, DANE-DIAN, CRM PROCOLOMBIA.]")
    st.caption(":blue[Nota: Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.]")
    
    # Mensaje informativo
    st.info(
        "💡 **¿Qué puedes encontrar en esta página?**\n"
        "* **Visión general:** Obtén métricas clave sobre el total de empresas identificadas, su relación con ProColombia y su potencial de atención.\n"
        "* **Análisis por tamaño:** Explora cómo se distribuyen las empresas y el valor de sus exportaciones (Grandes, Medianas, Pequeñas y Micro).\n"
        "* **Top Exportadoras:** Identifica rápidamente las principales empresas exportadoras a nivel general y desglosadas por tamaño de empresa.", 
        icon="🏢"
    )

    # Marcador para volver al inicio
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)
       
    # ============= Filtros Generales ============
    st.markdown("#### **Filtros por tipo de empresa**")

    # Crear la clase de filtros dinámicos
    dynamic_filters_filtros_generales = DynamicFilters(df=df_filtros_generales_empresas, filters_name="generales", filters=ls_filtros_generales_empresas, display_names=dict_filtros_generales_empresas)

    # Mostrar los filtros dinámicos 
    dynamic_filters_filtros_generales.display_filters(location="columns", num_columns=4)

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

    # =========== Filtro General ============ #
    dict_filtros_generales_empresas_usuario = {'MENOR_200K_HABITANTES' : session_state['generales']['MENOR_200K_HABITANTES'],
                                'PDET' : session_state['generales']['PDET'],
                                'DEPARTAMENTO_EMP' : session_state['generales']['DEPARTAMENTO'],
                                'MUNICIPIO_EMP' : session_state['generales']['MUNICIPIO'],
                                'TAMANO' : session_state['generales']['TAMANO'],
                                'CADENA_SEGMENTACION' : session_state['generales']['CADENA_SEGMENTACION'],
                                'TRAYECTORIA_EXPORTADORA' : session_state['generales']['TRAYECTORIA_EXPORTADORA'],
                                'COD_CIIU_1' : session_state['generales']['COD_CIIU_1'],
                                'DESCRIPCION_CIIU_1' : session_state['generales']['DESCRIPCION_CIIU_1'],
                                'POTENCIAL_ATENCION' : session_state['generales']['POTENCIAL_ATENCION'],
                                'VALOR_AGREGADO_CIIU_1' : session_state['generales']['VALOR_AGREGADO_CIIU_1'],
                                'ATENDIDA_PC' : session_state['generales']['ATENDIDA_PC'],
                                'SERVICIOS' : session_state['generales']['SERVICIOS'],
                                'NEGOCIOS' : session_state['generales']['NEGOCIOS'],
                                'RANGO_ANTIGUEDAD' : session_state['generales']['RANGO_ANTIGUEDAD'],
                                'RANGO_INGRESOS' : session_state['generales']['RANGO_INGRESOS'],
                                'HA_EXPORTADO' : session_state['generales']['HA_EXPORTADO']}
        
    # =========== Búsqueda del usuario ============ #

    if buscar:

        with st.spinner("Ejecutando consulta... :surfing_woman:"):

            # Barra de progreso y realiza la lógica pesada
            progress_bar = st.progress(0)

            # Crear payload para la llave "generales"
            payload = {
                "generales": dict_filtros_generales_empresas_usuario,
            }

            # Convertir a cadena JSON
            payload_json = json.dumps(payload, ensure_ascii=False)
            
            # Guardar payload en Session State para futuras referencias
            session_state['payload_tejido'] = payload_json

            # Registrar el evento de busqueda
            registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Empresas', detalle_evento='Búsqueda de empresas', filtros=st.session_state['payload_tejido'])
            progress_bar.progress(20)

            # Crear query
            sql_query = query_data_empresas(dict_columnas = dict_query_empresas, 
                                                filtros_generales=dict_filtros_generales_empresas_usuario)
            progress_bar.progress(40)
            
            # Ejecutar consulta y guardar resultado en Session State
            session_state['df_empresas'] = st.session_state.session.sql(sql_query)
            progress_bar.progress(45)

            # Contar registros
            session_state['total_registros'] = session_state['df_empresas'].count()

            # Procesar df si hay datos
            if session_state['total_registros'] > 0:

                # Métricas de resumen 
                (st.session_state['num_empresas'],
                 st.session_state['num_empresas_servicios'],
                 st.session_state['num_empresas_negocios'],
                 st.session_state['num_empresas_potencial']) = calcular_metricas_resumen(_df_snowpark=session_state['df_empresas'], servicios_anios_disponibles=servicios_anios_disponibles, negocios_anios_disponibles=negocios_anios_disponibles)
                
                # Resumen por tamaño
                (st.session_state['df_resumen_empresas'],
                 st.session_state['df_resumen_empresas_formateado']) = crear_resumen_por_tamano(_df_snowpark=session_state['df_empresas'])
                
                # Crear top exportadoras
                (st.session_state['df_empresas_top_exportadoras_resumen'],
                 st.session_state['df_empresas_top_exportadoras_resumen_formateado']) = crear_top_exportadoras(_df_snowpark=session_state['df_empresas'], top_n=20)
                
                # Crear empresas por tamaño
                (st.session_state['dfs_empresas_por_tamano'],
                 st.session_state['dfs_empresas_por_tamano_formateado']) = crear_empresas_por_tamano(_df_snowpark=session_state['df_empresas'], top_n=10)

                # ==================== Seccion 1 ========================= #

                # Estructura 
                sec_1_row1_col1, sec_1_row1_col2 = st.columns(2, vertical_alignment='center', border=True)
                sec_1_row2_col1, sec_1_row2_col2 = st.columns(2, vertical_alignment='center', border=True)
                sec_1_row3_col1 = st.columns(1, vertical_alignment='center', border=True)[0]

                # Agregar datos de resumen

                # Número de empresas
                sec_1_row1_col1.metric("**Número total de empresas identificadas**", format_espanol(st.session_state['num_empresas'], decimales=0), border = True)
                
                # Servicios en el último año
                sec_1_row1_col2.metric(f'**Empresas con servicios de ProColombia en {servicios_anios_disponibles[0]} - {servicios_anios_disponibles[1]}**', format_espanol(st.session_state['num_empresas_servicios'], decimales=0), border = True)

                # Negocios en el último año
                sec_1_row2_col1.metric(f'**Empresas con negocios facilitados por ProColombia en {negocios_anios_disponibles[0]} - {negocios_anios_disponibles[1]}**',format_espanol(st.session_state['num_empresas_negocios'], decimales=0), border = True)

                # Empresas con potencial de atención
                sec_1_row2_col2.metric("**Empresas con potencial de atención (Muy Alto y Alto)**", format_espanol(st.session_state['num_empresas_potencial'], decimales=0), border = True)
                progress_bar.progress(60)

                # División
                st.divider()
                
                with sec_1_row3_col1:

                    # Título
                    st.markdown(f'<h4 class="custom-header" style="text-align: center;">Número de empresas y sus exportaciones por tamaño <br>(Millones USD FOB)</h4>', unsafe_allow_html=True)

                    # Mostrar los resultados si hay datos disponible
                    if not st.session_state['df_resumen_empresas_formateado'].empty:

                        # Mostrar al usuario
                        st.dataframe(st.session_state['df_resumen_empresas_formateado'], use_container_width=True, hide_index=True)

                        # Nota
                        st.caption('**Nota:** M (millones).')

                        # Habilitar el botón de descarga
                        descarga_tabla(
                            df=st.session_state['df_resumen_empresas'],
                            row_threshhold=100000,
                            label_descarga="Descargar resultados",
                            file_name='Resultados de Tejido Empresarial por Tamaño',
                            key_descarga='tabla_tejido_resumen',
                            sesion_activa=st.session_state.session,
                            tipo_evento="Descarga Resumen",
                            pagina="Empresas",
                            filtros=payload_json,
                            nota = "Los valores están en dólares FOB",
                            agregar_nota = True
                        )

                    else:
                        st.error("No se encontró información que cumpla con los filtros seleccionados.")

                # ==================== Seccion 2 ========================= #

                # Título
                st.markdown(f'<h3 class="custom-header">Top Empresas Exportadoras (Millones USD FOB)</h3>', unsafe_allow_html=True)

                # Estructura
                sec_3_row1_col1 = st.columns(1, vertical_alignment='center', border=True)[0]

                with sec_3_row1_col1:

                    # Título
                    st.markdown(f'<h3 class="custom-header">Top 20 Empresas Exportadoras (Millones USD FOB)</h3>', unsafe_allow_html=True)

                    # Datos

                    # Mostrar los resultados si hay datos disponible
                    if not st.session_state['df_empresas_top_exportadoras_resumen'].empty:
                        
                        # Mostrar el resultado
                        st.dataframe(st.session_state['df_empresas_top_exportadoras_resumen_formateado'], use_container_width=True, hide_index=True)

                        # Nota
                        st.caption('**Nota:** M (millones).')
                        progress_bar.progress(75)

                        # Habilitar descarga
                        descarga_tabla(
                        df=session_state['df_empresas_top_exportadoras_resumen'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Resultados de Tejido Empresarial - Top Empresas Exportadoras',
                        key_descarga='tabla_tejido_top_exportadoras',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga Top Empresas Exportadora",
                        pagina="Empresas",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )

                    else:
                        st.error("No se encontró información que cumpla con los filtros seleccionados.")

                # ==================== Seccion 3 ========================= #

                # Título
                st.markdown(f'<h3 class="custom-header">Empresas Exportadoras por Tamaño (Millones USD FOB)</h3>', unsafe_allow_html=True)

                # Estructura
                sec_2_row1_col1 = st.columns(1, vertical_alignment='center', border=True)[0]
                sec_2_row2_col1 = st.columns(1, vertical_alignment='center', border=True)[0]
                sec_2_row3_col1 = st.columns(1, vertical_alignment='center', border=True)[0]
                sec_2_row4_col1 = st.columns(1, vertical_alignment='center', border=True)[0]
                # TODO SE DECIDE NO MOSTRAR LAS EMPRESAS NO CLASIFICADAS POR TAMAÑO EN ESTA VERSIÓN INICIAL, YA QUE NO HAY INFORMACIÓN
                # sec_2_row5_col1 = st.columns(1, vertical_alignment='center', border=True)[0]

                with sec_2_row1_col1:

                    # Grandes
                    st.markdown(f'<h4 class="custom-header">Top 10 - Empresas Exportadoras Grandes (Millones USD FOB)</h4>', unsafe_allow_html=True)
                    st.caption(f'Solo se incluyen empresas cuyas con exportaciones mayores a 0 en {exportaciones_anios_disponibles[1]}')

                    # Datos

                    # Mostrar los resultados si hay datos disponible
                    if not st.session_state['dfs_empresas_por_tamano']['df_empresas_grandes_resumen'].empty:
                        
                        # Mostrar el resultado
                        st.dataframe(st.session_state['dfs_empresas_por_tamano_formateado']['df_empresas_grandes_resumen'], use_container_width=True, hide_index=True)

                        # Nota
                        st.caption('**Nota:** M (millones).')

                        # Habilitar descarga
                        descarga_tabla(
                        df=st.session_state['dfs_empresas_por_tamano']['df_empresas_grandes_resumen'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Resultados de Tejido Empresarial - Empresas Grandes',
                        key_descarga='tabla_tejido_grandes',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga Empresas Grandes",
                        pagina="Empresas",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                        
                    else:
                        st.error("No se encontró información de empresas grandes que cumplan con los filtros seleccionados.")

                with sec_2_row2_col1:

                    # Medianas
                    st.markdown(f'<h4 class="custom-header">Top 10 - Empresas Exportadoras Medianas (Millones USD FOB)</h4>', unsafe_allow_html=True)
                    st.caption(f'Solo se incluyen empresas cuyas con exportaciones mayores a 0 en {exportaciones_anios_disponibles[1]}')

                    # Datos

                    # Mostrar los resultados si hay datos disponible
                    if not st.session_state['dfs_empresas_por_tamano']['df_empresas_medianas_resumen'].empty:
                        
                        # Mostrar el resultado
                        st.dataframe(st.session_state['dfs_empresas_por_tamano_formateado']['df_empresas_medianas_resumen'], use_container_width=True, hide_index=True)

                        # Nota
                        st.caption('**Nota:** M (millones).')

                        # Habilitar descarga
                        descarga_tabla(
                        df=st.session_state['dfs_empresas_por_tamano']['df_empresas_medianas_resumen'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Resultados de Tejido Empresarial - Empresas Medianas',
                        key_descarga='tabla_tejido_medianas',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga Empresas Medianas",
                        pagina="Empresas",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                        
                    else:
                        st.error("No se encontró información de empresas medianas que cumplan con los filtros seleccionados.")

                with sec_2_row3_col1:
                
                    # Pequeñas 
                    st.markdown(f'<h4 class="custom-header">Top 10 - Empresas Exportadoras Pequeñas (Millones USD FOB)</h4>', unsafe_allow_html=True)
                    st.caption(f'Solo se incluyen empresas cuyas con exportaciones mayores a 0 en {exportaciones_anios_disponibles[1]}')

                    # Datos

                    # Mostrar los resultados si hay datos disponible
                    if not st.session_state['dfs_empresas_por_tamano']['df_empresas_pequeñas_resumen'].empty:
                        
                        # Mostrar el resultado
                        st.dataframe(st.session_state['dfs_empresas_por_tamano_formateado']['df_empresas_pequeñas_resumen'], use_container_width=True, hide_index=True)

                        # Nota
                        st.caption('**Nota:** M (millones).')
                        progress_bar.progress(90)

                        # Habilitar descarga
                        descarga_tabla(
                        df=st.session_state['dfs_empresas_por_tamano']['df_empresas_pequeñas_resumen'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Resultados de Tejido Empresarial - Empresas Pequeñas',
                        key_descarga='tabla_tejido_pequeñas',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga Empresas Pequeñas",
                        pagina="Empresas",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                        
                    else:
                        st.error("No se encontró información de empresas pequeñas que cumplan con los filtros seleccionados.")

                with sec_2_row4_col1:

                    # Micro
                    st.markdown(f'<h4 class="custom-header">Top 10 - Empresas Exportadoras Micro (Millones USD FOB)</h4>', unsafe_allow_html=True)
                    st.caption(f'Solo se incluyen empresas cuyas con exportaciones mayores a 0 en {exportaciones_anios_disponibles[1]}')

                    # Datos

                    # Mostrar los resultados si hay datos disponible
                    if not st.session_state['dfs_empresas_por_tamano']['df_empresas_micro_resumen'].empty:
                        
                        # Mostrar el resultado
                        st.dataframe(st.session_state['dfs_empresas_por_tamano_formateado']['df_empresas_micro_resumen'], use_container_width=True, hide_index=True)

                        # Nota
                        st.caption('**Nota:** M (millones).')

                        # Habilitar descarga
                        descarga_tabla(
                        df=st.session_state['dfs_empresas_por_tamano']['df_empresas_micro_resumen'],
                        row_threshhold=100000,
                        label_descarga="Descargar resultados",
                        file_name='Resultados de Tejido Empresarial - Empresas Micro',
                        key_descarga='tabla_tejido_micro',
                        sesion_activa=st.session_state.session,
                        tipo_evento="Descarga Empresas Micro",
                        pagina="Empresas",
                        filtros=payload_json,
                        nota = "Los valores están en dólares FOB",
                        agregar_nota = True
                        )
                        
                    else:
                        st.error("No se encontró información de empresas micro que cumplan con los filtros seleccionados.")
                    progress_bar.progress(100)
        # TODO SE DECIDE NO MOSTRAR LAS EMPRESAS NO CLASIFICADAS POR TAMAÑO EN ESTA VERSIÓN INICIAL, YA QUE NO HAY INFORMACIÓN
        #         with sec_2_row5_col1:

        #             # No clasificadas
        #             st.markdown(f'<h4 class="custom-header">Top 10 - Empresas Exportadoras por No Determinado (Millones USD FOB)</h4>', unsafe_allow_html=True)
        #             st.caption(f'Solo se incluyen empresas cuyas con exportaciones mayores a 0 en {exportaciones_anios_disponibles[1]}')

        #             # Datos

        #             # Mostrar los resultados si hay datos disponible
        #             if not st.session_state['dfs_empresas_por_tamano']['df_empresas_no_clasificadas_resumen'].empty:
                        
        #                 # Mostrar el resultado
        #                 st.dataframe(st.session_state['dfs_empresas_por_tamano_formateado']['df_empresas_no_clasificadas_resumen'], use_container_width=True, hide_index=True)

        #                 # Nota
        #                 st.caption('**Nota:** M (millones).')
        #                 progress_bar.progress(100)

        #                 # Habilitar descarga
        #                 descarga_tabla(
        #                 df=st.session_state['dfs_empresas_por_tamano']['df_empresas_no_clasificadas_resumen'],
        #                 row_threshhold=100000,
        #                 label_descarga="Descargar resultados",
        #                 file_name='Resultados de Tejido Empresarial - Empresas No Determinado',
        #                 key_descarga='tabla_tejido_no_determinado',
        #                 sesion_activa=st.session_state.session,
        #                 tipo_evento="Descarga Empresas No Determinado",
        #                 pagina="Empresas",
        #                 filtros=payload_json,
        #                 nota = "Los valores están en dólares FOB",
        #                 agregar_nota = True
        #                 )
                        
        #             else:
        #                 st.error("No se encontró información de empresas no clasificadas que cumpla con los filtros seleccionados.")
        #                 progress_bar.progress(100)

        # # En caso de que no hayan resultados para la consulta específica
        #     else:
        #         st.error("No se encontró información que cumpla con los filtros seleccionados.")

# ========== Footer ==========#
footer()  
