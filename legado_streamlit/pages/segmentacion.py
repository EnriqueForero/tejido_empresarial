#============= Bibliotecas =============#
# Bibliotecas Externas
import streamlit as st
from streamlit import session_state
import json
from datetime import timedelta

# Módulos Propios
from src.streamlit_analitica import navbar, footer
# Funciones de la página de segmentación 
from src.pages_utils.segmentacion_utils import ls_filtros_generales_empresas, dict_filtros_generales_empresas, ls_filtros_exportadoras, dict_filtros_exportadoras, dict_query_segmentacion, ls_columnas_usuario_segmentacion, query_data_segmentacion, buscar_nits, query_data_razon_social, query_data_nit_individual
# Funciones de ayuda
from src.pages_utils.utils import load_filtros_generales, load_filtros_exportadoras, transformar_numericas, descarga_tabla
# Consulta segura Snowflake
from src.snowflake_analitica import registrar_evento, flujo_snowflake, update_last_activity
# Snowpark
from snowflake.snowpark.functions import col
# Filtros dinámicos
from src.filtros_dinamicos_analitica import DynamicFilters

# ================== Configuración inicial ====================
# Configuración básica de la página en Streamlit.
st.set_page_config(
    page_title="Tejido Empresarial",
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

# =================== Constantes =====================
# Enlace público (OneDrive) al Excel con el glosario de todas las variables del aplicativo
GLOSARIO_URL = "https://proexportcol-my.sharepoint.com/:x:/g/personal/nforero_procolombia_co/IQAWIkimBGxcQ4UzASM2f5SKAetTiRp0dVik0ERI8_CAtSI?e=cVf1jN"

# =================== Navegación =====================
# Comprobación y configuración inicial de los parámetros de consulta en la URL.
if "page" not in st.query_params:
    st.query_params.page = '2'  # Página predeterminada si no hay parámetro 'page' en la URL.

# =================== Estado inicial de búsqueda de NITs ===================
for k, v in {'NITS': set(), 'BUSCAR_NITS': False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =================== Estado inicial de búsqueda por Razón Social ===================
for k, v in {'RAZON_SOCIAL_BUSQUEDA': '', 'BUSCAR_RAZON_SOCIAL': False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =================== Estado inicial de búsqueda por NIT Individual ===================
for k, v in {'NIT_INDIVIDUAL_BUSQUEDA': '', 'BUSCAR_NIT_INDIVIDUAL': False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================== navbar =========================
# Llamada al componente de navegación personalizada (barra de navegación).
navbar()

# Redirección condicional según el valor del parámetro 'page' en la URL.
# if st.query_params.page == '1':
#     st.switch_page("app.py")  # Redirige a la página de inicio.
# if st.query_params.page == '3':
#     st.switch_page("pages/empresas.py") # Redirige a la página de empresas
# if st.query_params.page == '4':
#     st.switch_page("pages/destinos.py") # Redirige a la página de destinos
# if st.query_params.page == '5':
#     st.switch_page("pages/valor_agregado.py") # Redirige a la página de valor agregado
# if st.query_params.page == '6':
#     st.switch_page("pages/territorios.py") # Redirige a la página de territorios

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

# Filtros para empresas exportadoras
df_filtros_empresas_exportadoras = load_filtros_exportadoras(_session=st.session_state.session)

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
        if (k.startswith('generales') or k.startswith('exportadoras'))
        and k != '_filters_resetting'
    ]
    for k in keys_to_delete:
        del st.session_state[k]
    
    # 2. Reinicializar los diccionarios de filtros con listas vacías
    st.session_state['generales'] = {k: [] for k in ls_filtros_generales_empresas}
    # st.session_state['exportadoras'] = {k: [] for k in ls_filtros_exportadoras}

    # 2.5. Limpiar explícitamente las keys de los widgets multiselect
    for filter_name in ls_filtros_generales_empresas:
        widget_key = 'generales' + filter_name
        st.session_state.pop(widget_key, None)
        
    for filter_name in ls_filtros_exportadoras:
        widget_key = 'exportadoras' + filter_name
        st.session_state.pop(widget_key, None)
    
    # 3. Búsqueda por NITs
    st.session_state['BUSCAR_NITS'] = False
    st.session_state['NITS'] = set()
    
    # 4. Limpiar DataFrames de resultados, conteos y payloads
    
    # Resultados de segmentación general
    st.session_state.pop('df_segmentacion', None)
    st.session_state.pop('df_segmentacion_impresion', None)
    st.session_state.pop('df_segmentacion_impresion_snowpark', None)
    st.session_state.pop('total_registros', None)
    st.session_state.pop('payload_segmentacion', None)
    st.session_state.pop('df_descarga', None)
    
    # Resultados de búsqueda por NITs
    st.session_state.pop('df_segmentacion_nits', None)
    st.session_state.pop('df_segmentacion_nits_impresion', None)
    st.session_state.pop('df_segmentacion_nits_impresion_snowpark', None)
    st.session_state.pop('total_registros_nits', None)
    st.session_state.pop('payload_segmentacion_nits', None)
    st.session_state.pop('df_descarga_nits', None)

    # Resultados de búsqueda por Razón Social
    st.session_state['BUSCAR_RAZON_SOCIAL'] = False
    st.session_state['RAZON_SOCIAL_BUSQUEDA'] = ''
    st.session_state.pop('df_segmentacion_rs', None)
    st.session_state.pop('df_segmentacion_rs_impresion', None)
    st.session_state.pop('df_segmentacion_rs_impresion_snowpark', None)
    st.session_state.pop('total_registros_rs', None)
    st.session_state.pop('payload_segmentacion_rs', None)
    st.session_state.pop('df_descarga_rs', None)

    # Resultados de búsqueda por NIT Individual
    st.session_state['BUSCAR_NIT_INDIVIDUAL'] = False
    st.session_state['NIT_INDIVIDUAL_BUSQUEDA'] = ''
    st.session_state.pop('df_segmentacion_nit_ind', None)
    st.session_state.pop('df_segmentacion_nit_ind_impresion', None)
    st.session_state.pop('df_segmentacion_nit_ind_impresion_snowpark', None)
    st.session_state.pop('total_registros_nit_ind', None)
    st.session_state.pop('payload_segmentacion_nit_ind', None)
    st.session_state.pop('df_descarga_nit_ind', None)

# =========== BODY ===========
with body:
    
    # Título y fuentes 
    st.markdown("## **Tejido Empresarial de Colombia**")
    st.caption(":blue[Fuente: RUES, SUPERSOCIEDADES, DANE-DIAN EXPORTACIONES, CRM PROCOLOMBIA]")
    st.caption(":blue[Nota: Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.]")

    # Mensaje informativo
    st.info(
        "💡 **¿Qué puedes hacer en esta página?**\n"
        "* **Búsqueda por filtros:** Utiliza el panel de filtros para segmentar empresas según sus características generales.\n"
        "* **Búsqueda individual:** Encuentra una empresa específica digitando su **Razón social** o **NIT** en las barras de búsqueda inferiores.\n"
        "* **Búsqueda masiva:** Sube un archivo de texto (.txt) y consulta múltiples empresas a la vez.\n"
        f"* **Glosario de variables:** Consulta la definición de todas las variables del aplicativo en el siguiente [archivo]({GLOSARIO_URL}).",
        icon="🏢"
    )

    # Selector de vista
    vista = st.radio(
    "**Seleccione la consulta que desea realizar:**",
    ["Búsqueda por filtros", 
     "Búsqueda de una empresa por razón social", 
     "Búsqueda de una empresa por NIT",
     "Búsqueda masiva por NITs"],
    horizontal=True)

    # Marcador para volver al inicio
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)

    # Opción 1: Búsqueda por filtros
    if vista == "Búsqueda por filtros":
    
        # Búsqueda por filtros
        st.markdown("##### **Búsqueda por filtros**")

        # ============= Filtros por tipo de empresa ============
        st.markdown("#### **Filtros por tipo de empresa**")

        # Crear la clase de filtros dinámicos
        dynamic_filters_filtros_generales = DynamicFilters(df=df_filtros_generales_empresas, filters_name="generales", filters=ls_filtros_generales_empresas, display_names=dict_filtros_generales_empresas)

        # Mostrar los filtros dinámicos
        dynamic_filters_filtros_generales.display_filters(location="columns", num_columns=4)

        # ============= Nota aclaratoria sobre los filtros ============
        # Se usa HTML para lograr un texto compacto y con color de texto normal
        # (st.caption lo renderiza atenuado y con más interlineado).
        st.markdown("""
            <div style="font-size:0.75rem; line-height:1.3; margin:0.25rem 0 0.75rem 0;">
                <strong>Nota sobre la definición de algunos filtros:</strong>
                <ul style="margin:0.1rem 0 0 1rem; padding:0;">
                    <li><strong>Cadena de segmentación:</strong> Para las empresas exportadoras, corresponde a la cadena productiva que más ha exportado la empresa en los últimos 5 años, según clasificación ProColombia. Para las empresas no exportadoras, corresponde a la cadena productiva asociada al CIIU principal de la empresa, según clasificación ProColombia.</li>
                    <li><strong>Inversión extranjera:</strong> Indica "Sí" cuando la empresa está identificada como sucursal de sociedad extranjera o cuando reporta un porcentaje de capital social extranjero.</li>
                    <li><strong>Cadena CIIU Rev 4 - Actividad principal:</strong> Cadena ProColombia correspondiente al CIIU principal de la empresa. La correlativa entre estas dos variables fue construida en conjunto por la Gerencia de Inteligencia Comercial y la Vicepresidencia de Exportaciones.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # # ============= Filtros por tipo de exportación ============
        # st.markdown("#### **Filtros por tipo de exportación**")

        # # Crear la clase de filtros dinámicos
        dynamic_filters_filtros_exportadoras = DynamicFilters(df=df_filtros_empresas_exportadoras, filters_name="exportadoras", filters=ls_filtros_exportadoras, display_names=dict_filtros_exportadoras)

        # # Mostrar los filtros dinámicos 
        # dynamic_filters_filtros_exportadoras.display_filters(location="columns", num_columns=4)

        # Limpiar el flag de reset si existe
        if st.session_state.get('_filters_resetting', False):
            st.session_state['_filters_resetting'] = False
            st.rerun()  # Solo un rerun DESPUÉS de que todo se limpió

        # Estructura de botones
        st.markdown("#### **Botones para búsqueda y descarga**")
        col0, col1, col2, _ = st.columns(4, vertical_alignment='bottom')

        # Botones de búsqueda
        buscar = col0.button('Buscar', type='primary', use_container_width=True, key='buscar')

        # Botón de preparación de descarga
        preparar_descarga_boton = col1.button('Preparar descarga', type='primary', use_container_width=True, key='preparar_descarga')

        # Botón de reinicio de filtros
        reinicio = col2.button("Reiniciar filtros y resultados", type='primary', use_container_width=True, key='reiniciar', on_click=reset_all_filters)

        # =========== Filtro General ============ #
        dict_filtros_generales_empresas_usuario = {'DEPARTAMENTO_EMP' : session_state['generales']['DEPARTAMENTO'],
                                    'MUNICIPIO_EMP' : session_state['generales']['MUNICIPIO'],
                                    'TAMANO' : session_state['generales']['TAMANO'],
                                    'CADENA_SEGMENTACION' : session_state['generales']['CADENA_SEGMENTACION'],
                                    'TRAYECTORIA_EXPORTADORA' : session_state['generales']['TRAYECTORIA_EXPORTADORA'],
                                    'INVERSION_EXTRANJERA' : session_state['generales']['INVERSION_EXTRANJERA'],
                                    'COD_CIIU_1' : session_state['generales']['COD_CIIU_1'],
                                    'DESCRIPCION_CIIU_1' : session_state['generales']['DESCRIPCION_CIIU_1'],
                                    'VALOR_AGREGADO_CIIU_1' : session_state['generales']['VALOR_AGREGADO_CIIU_1'],
                                    'CADENA_CIIU_1' : session_state['generales']['CADENA_CIIU_1'],
                                    'RANGO_ANTIGUEDAD' : session_state['generales']['RANGO_ANTIGUEDAD'],
                                    'RANGO_INGRESOS' : session_state['generales']['RANGO_INGRESOS'],
                                    'HA_EXPORTADO' : session_state['generales']['HA_EXPORTADO']}
            
        # =========== Filtro Empresas exportadoras ============ #
        dict_filtros_empresas_exportadoras_usuario = {'SECTOR' : session_state['exportadoras']['SECTOR'],
                            'SUBSECTOR' : session_state['exportadoras']['SUBSECTOR'],
                            'COD_POSICION_ARANCELARIA' : session_state['exportadoras']['COD_POSICION_ARANCELARIA'],
                            'DESC_POSICION_ARANCELARIA' : session_state['exportadoras']['DESC_POSICION_ARANCELARIA'],
                            'HUB' : session_state['exportadoras']['HUB'],
                            'PAIS_DESTINO' : session_state['exportadoras']['PAIS_DESTINO']}
        
        # =========== Búsqueda del usuario ============ #

        # Lógica de ejecución de la búsqueda
        if buscar:

            # Eliminar DataFrames y conteos previos de búsquedas de nits
            st.session_state.pop('df_segmentacion_nits', None)
            st.session_state.pop('df_segmentacion_nits_impresion', None)
            st.session_state.pop('df_segmentacion_nits_impresion_snowpark', None)
            st.session_state.pop('total_registros_nits', None)
            st.session_state.pop('payload_segmentacion_nits', None)
            st.session_state.pop('df_descarga_nits', None)

            # Ejecutar la búsqueda con un spinner
            with st.spinner("Ejecutando consulta... :surfing_woman:"):

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Combinar ambos diccionarios de filtros bajo las llaves "generales" y "exportadoras"
                payload = {
                    "generales": dict_filtros_generales_empresas_usuario,
                    "exportadoras": dict_filtros_empresas_exportadoras_usuario
                }

                # Convertir a cadena JSON
                payload_json = json.dumps(payload, ensure_ascii=False)

                # Guardar payload en Session State para futuras referencias
                session_state['payload_segmentacion'] = payload_json
                progress_bar.progress(20)
                
                # Registrar el evento de busqueda
                registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Tejido Empresarial de Colombia', detalle_evento='Búsqueda de empresas', filtros=st.session_state['payload_segmentacion'])
                progress_bar.progress(40)

                # Crear query
                sql_query = query_data_segmentacion(dict_columnas = dict_query_segmentacion, 
                                                    filtros_generales=dict_filtros_generales_empresas_usuario, 
                                                    filtros_emp_export=dict_filtros_empresas_exportadoras_usuario)
                
                # Ejecutar consulta y guardar resultado en Session State
                session_state['df_segmentacion'] = st.session_state.session.sql(sql_query)
                progress_bar.progress(60)

                # Contar registros
                session_state['total_registros'] = session_state['df_segmentacion'].count()
                progress_bar.progress(100)

                # Mostrar los resultados si hay datos disponibles
                if session_state['total_registros'] > 0:

                    # Elegir columnas para mostrar y guardar resultado en Session State (Solo se muestran las primeras 10 filas)
                    session_state['df_segmentacion_impresion_snowpark'] = session_state['df_segmentacion'].sort(col('"Ingresos operacionales (COP)"'), ascending=False).select(*ls_columnas_usuario_segmentacion).limit(10)

                    # Volver a pandas para transformación y visualización
                    session_state['df_segmentacion_impresion'] = transformar_numericas(session_state['df_segmentacion_impresion_snowpark'].to_pandas())

                    # Condición para mostrar el DataFrame
                    if not session_state['df_segmentacion_impresion'].empty:
                        
                        # TODO : Cambiar condiciones de impresión para evitar repetición
                        # Mostrar datos
                        # st.dataframe(session_state['df_segmentacion_impresion'])
                        st.dataframe(session_state['df_segmentacion_impresion_snowpark'].to_pandas())
                    
                        # Mostrar el número de registros del df
                        st.write(f"**Resultados:** {session_state['total_registros']:,} registros")

                    # En caso de que no hayan resultados para la consulta específica
                    else:
                        st.error("No se encontró información que cumpla con los filtros seleccionados.")              

                # En caso de que no hayan resultados para la consulta específica
                else:
                    st.error("No se encontró información que cumpla con los filtros seleccionados.")

        # =========== Flujo de descarga ============ #
        if preparar_descarga_boton:

            with st.spinner("Preparando descarga... :surfing_woman:"):

                # Crear lógica de preparación de descarga valida

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Lógica para segmentación general
                if 'df_segmentacion' in session_state and 'total_registros' in session_state and session_state['total_registros'] > 0 \
                    and 'df_segmentacion_impresion' in session_state and not session_state['df_segmentacion_impresion'].empty \
                    and 'payload_segmentacion' in session_state:
                    progress_bar.progress(20)

                    # TODO : Cambiar condiciones de impresión para evitar repetición
                    # Mostrar datos
                    # st.dataframe(session_state['df_segmentacion_impresion'])
                    st.dataframe(session_state['df_segmentacion_impresion_snowpark'].to_pandas())
                    progress_bar.progress(50)
                    
                    # Mostrar el número de registros del df
                    st.write(f"**Resultados:** {session_state['total_registros']:,} registros")

                    # Volver consulta a pandas para descarga
                    session_state['df_descarga'] = session_state['df_segmentacion'].to_pandas()
                    progress_bar.progress(80)

                    # Condición para habilitar el botón de descarga
                    if not session_state['df_descarga'].empty:

                        # Botón de descarga
                        descarga_tabla(
                            df=session_state['df_descarga'],
                            row_threshhold=100000,
                            label_descarga="Descargar resultados",
                            file_name='Resultados Segmentación de Empresas',
                            key_descarga='tabla_segmentacion',
                            sesion_activa=st.session_state.session,
                            tipo_evento="Descarga Segmentación",
                            pagina="Segmentación",
                            filtros=session_state['payload_segmentacion'])
                        progress_bar.progress(100)

    # Opción 2: Búsqueda de una empresa por razón social
    if vista == "Búsqueda de una empresa por razón social":

        # =========== Búsqueda por Razón Social ============ #
        st.markdown("##### **Búsqueda por razón social de empresa individual**")

        # Estructura de botones
        col_rs_input, col_rs_btn, col3, col4, _ = st.columns([3, 2, 2, 2, 1], vertical_alignment='bottom')

        with col_rs_input:
            st.text_input(
                "Buscar por nombre de empresa",
                key='_razon_social_input_widget',
                placeholder="Ejemplo: TECNOLOGÍA COLOMBIANA"
            )

        razon_social_boton = col_rs_btn.button(
            'Buscar por Razón Social',
            type='primary',
            use_container_width=True,
            key='buscar_razon_social_btn'
        )

        # Botón de preparación de descarga
        preparar_descarga_boton_razon_social = col3.button('Preparar descarga', type='primary', use_container_width=True, key='preparar_descarga_razon_social')

        # Botón de reinicio de filtros
        reinicio_razon_social = col4.button("Reiniciar resultados", type='primary', use_container_width=True, key='reiniciar_razon_social', on_click=reset_all_filters)

        # Al hacer clic en el botón, se guarda el término de búsqueda y se activa la bandera para ejecutar la búsqueda en el siguiente rerun

        if razon_social_boton:
            termino = st.session_state.get('_razon_social_input_widget', '').strip()
            if termino:
                # Guardar término confirmado y activar flag de búsqueda
                st.session_state['RAZON_SOCIAL_BUSQUEDA'] = termino
                st.session_state['BUSCAR_RAZON_SOCIAL'] = True

                # Limpiar resultados previos de otras búsquedas
                st.session_state.pop('df_segmentacion', None)
                st.session_state.pop('df_segmentacion_impresion', None)
                st.session_state.pop('df_segmentacion_impresion_snowpark', None)
                st.session_state.pop('total_registros', None)
                st.session_state.pop('payload_segmentacion', None)
                st.session_state.pop('df_descarga', None)
                st.session_state.pop('df_segmentacion_nits', None)
                st.session_state.pop('df_segmentacion_nits_impresion', None)
                st.session_state.pop('df_segmentacion_nits_impresion_snowpark', None)
                st.session_state.pop('total_registros_nits', None)
                st.session_state.pop('payload_segmentacion_nits', None)
                st.session_state.pop('df_descarga_nits', None)
        st.divider()

        # =========== Búsqueda por Razón Social ============ #
        if st.session_state['BUSCAR_RAZON_SOCIAL'] and st.session_state['RAZON_SOCIAL_BUSQUEDA']:

            with st.spinner("Ejecutando consulta... :surfing_woman:"):

                progress_bar = st.progress(0)

                termino_busqueda = st.session_state['RAZON_SOCIAL_BUSQUEDA']

                # Crear payload para trazabilidad
                payload_rs = {"razon_social": termino_busqueda}
                payload_rs_json = json.dumps(payload_rs, ensure_ascii=False)
                session_state['payload_segmentacion_rs'] = payload_rs_json
                progress_bar.progress(20)

                # Registrar evento
                registrar_evento(
                    sesion_activa=st.session_state.session,
                    tipo_evento='Búsqueda',
                    pagina='Tejido Empresarial de Colombia',
                    detalle_evento='Búsqueda por Razón Social',
                    filtros=session_state['payload_segmentacion_rs']
                )
                progress_bar.progress(40)

                # Crear y ejecutar query
                sql_query_rs = query_data_razon_social(
                    dict_columnas=dict_query_segmentacion,
                    termino_busqueda=termino_busqueda
                )
                session_state['df_segmentacion_rs'] = st.session_state.session.sql(sql_query_rs)
                progress_bar.progress(60)

                # Contar registros
                session_state['total_registros_rs'] = session_state['df_segmentacion_rs'].count()
                progress_bar.progress(100)

                if session_state['total_registros_rs'] > 0:

                    # Elegir columnas para mostrar y guardar resultado en Session State (Solo se muestran las primeras 10 filas)
                    session_state['df_segmentacion_rs_impresion_snowpark'] = session_state['df_segmentacion_rs'].sort(col('"Ingresos operacionales (COP)"'), ascending=False).select(*ls_columnas_usuario_segmentacion).limit(10)

                    # Volver a pandas para transformación y visualización
                    session_state['df_segmentacion_rs_impresion'] = transformar_numericas(session_state['df_segmentacion_rs_impresion_snowpark'].to_pandas())

                    # Condición para mostrar el DataFrame
                    if not session_state['df_segmentacion_rs_impresion'].empty:
                        
                        # TODO : Cambiar condiciones de impresión para evitar repetición
                        # Mostrar datos
                        # st.dataframe(session_state['df_segmentacion_rs_impresion'])
                        st.dataframe(session_state['df_segmentacion_rs_impresion_snowpark'].to_pandas())

                        # Mostrar el número de registros del df
                        st.write(f"**Resultados:** {session_state['total_registros_rs']:,} registros")

                    else:
                        st.error("No se encontró información para la empresa buscada.")

                # En caso de que no hayan resultados para la consulta específica
                else:
                    st.error("No se encontró información para la empresa buscada.")

                # Resetear la marca para no repetir la búsqueda en el siguiente rerun
                st.session_state['BUSCAR_RAZON_SOCIAL'] = False

        # =========== Flujo de descarga ============ #
        if preparar_descarga_boton_razon_social:

            with st.spinner("Preparando descarga... :surfing_woman:"):

                # Crear lógica de preparación de descarga valida

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Lógica para búsqueda por Razón Social
                if 'df_segmentacion_rs' in session_state and 'total_registros_rs' in session_state and session_state['total_registros_rs'] > 0 \
                    and 'df_segmentacion_rs_impresion' in session_state and not session_state['df_segmentacion_rs_impresion'].empty \
                    and 'payload_segmentacion_rs' in session_state:
                    progress_bar.progress(20)

                    # TODO : Cambiar condiciones de impresión para evitar repetición
                    # Mostrar datos
                    # st.dataframe(session_state['df_segmentacion_rs_impresion'])
                    st.dataframe(session_state['df_segmentacion_rs_impresion_snowpark'].to_pandas())
                    progress_bar.progress(50)

                    # Mostrar el número de registros del df
                    st.write(f"**Resultados:** {session_state['total_registros_rs']:,} registros")

                    # Volver consulta a pandas para descarga
                    session_state['df_descarga_rs'] = session_state['df_segmentacion_rs'].to_pandas()
                    progress_bar.progress(80)

                    # Condición para habilitar el botón de descarga
                    if not session_state['df_descarga_rs'].empty:

                        # Botón de descarga
                        descarga_tabla(
                            df=session_state['df_descarga_rs'],
                            row_threshhold=100000,
                            label_descarga="Descargar resultados",
                            file_name='Resultados Búsqueda por Razón Social',
                            key_descarga='tabla_segmentacion_rs',
                            sesion_activa=st.session_state.session,
                            tipo_evento="Descarga Razón Social",
                            pagina="Segmentación",
                            filtros=session_state['payload_segmentacion_rs'])
                        progress_bar.progress(100)

    # Opción 3: Búsqueda de una empresa por NIT
    if vista == "Búsqueda de una empresa por NIT":

        # =========== Búsqueda por NIT Individual ============ #
        st.markdown("##### **Búsqueda por NIT de empresa individual**")
        
        col_nit_input, col_nit_btn, col3, col4, _ = st.columns([3, 2, 2, 2, 1], vertical_alignment='bottom')

        with col_nit_input:
            st.text_input(
                "Buscar por NIT",
                key='_nit_individual_input_widget',
                placeholder="Ej: 900409346"
            )

        nit_individual_boton = col_nit_btn.button(
            'Buscar por NIT',
            type='primary',
            use_container_width=True,
            key='buscar_nit_individual_btn'
        )

        # Botón de preparación de descarga
        preparar_descarga_boton_nit_individual = col3.button('Preparar descarga', type='primary', use_container_width=True, key='preparar_descarga_nit_individual')

        # Botón de reinicio de filtros
        reinicio_nit_individual = col4.button("Reiniciar resultados", type='primary', use_container_width=True, key='reiniciar_nit_individual', on_click=reset_all_filters)

        if nit_individual_boton:
            termino = st.session_state.get('_nit_individual_input_widget', '').strip()
            if termino:
                # Guardar término confirmado y activar flag de búsqueda
                st.session_state['NIT_INDIVIDUAL_BUSQUEDA'] = termino
                st.session_state['BUSCAR_NIT_INDIVIDUAL'] = True

                # Limpiar resultados previos de otras búsquedas
                st.session_state.pop('df_segmentacion', None)
                st.session_state.pop('df_segmentacion_impresion', None)
                st.session_state.pop('df_segmentacion_impresion_snowpark', None)
                st.session_state.pop('total_registros', None)
                st.session_state.pop('payload_segmentacion', None)
                st.session_state.pop('df_descarga', None)
                st.session_state.pop('df_segmentacion_nits', None)
                st.session_state.pop('df_segmentacion_nits_impresion', None)
                st.session_state.pop('df_segmentacion_nits_impresion_snowpark', None)
                st.session_state.pop('total_registros_nits', None)
                st.session_state.pop('payload_segmentacion_nits', None)
                st.session_state.pop('df_descarga_nits', None)
                st.session_state.pop('df_segmentacion_rs', None)
                st.session_state.pop('df_segmentacion_rs_impresion', None)
                st.session_state.pop('df_segmentacion_rs_impresion_snowpark', None)
                st.session_state.pop('total_registros_rs', None)
                st.session_state.pop('payload_segmentacion_rs', None)
                st.session_state.pop('df_descarga_rs', None)
        st.divider()

        # =========== Búsqueda por NIT Individual ============ #
        if st.session_state['BUSCAR_NIT_INDIVIDUAL'] and st.session_state['NIT_INDIVIDUAL_BUSQUEDA']:

            with st.spinner("Ejecutando consulta... :surfing_woman:"):

                progress_bar = st.progress(0)

                termino_busqueda = st.session_state['NIT_INDIVIDUAL_BUSQUEDA']

                # Crear payload para trazabilidad
                payload_nit_ind = {"nit_individual": termino_busqueda}
                payload_nit_ind_json = json.dumps(payload_nit_ind, ensure_ascii=False)
                session_state['payload_segmentacion_nit_ind'] = payload_nit_ind_json
                progress_bar.progress(20)

                # Registrar evento
                registrar_evento(
                    sesion_activa=st.session_state.session,
                    tipo_evento='Búsqueda',
                    pagina='Tejido Empresarial de Colombia',
                    detalle_evento='Búsqueda por NIT Individual',
                    filtros=session_state['payload_segmentacion_nit_ind']
                )
                progress_bar.progress(40)

                # Crear y ejecutar query
                sql_query_nit_ind = query_data_nit_individual(
                    dict_columnas=dict_query_segmentacion,
                    termino_busqueda=termino_busqueda
                )
                session_state['df_segmentacion_nit_ind'] = st.session_state.session.sql(sql_query_nit_ind)
                progress_bar.progress(60)

                # Contar registros
                session_state['total_registros_nit_ind'] = session_state['df_segmentacion_nit_ind'].count()
                progress_bar.progress(100)

                if session_state['total_registros_nit_ind'] > 0:

                    # Elegir columnas para mostrar y guardar resultado en Session State (Solo se muestran las primeras 10 filas)
                    session_state['df_segmentacion_nit_ind_impresion_snowpark'] = session_state['df_segmentacion_nit_ind'].sort(col('"Ingresos operacionales (COP)"'), ascending=False).select(*ls_columnas_usuario_segmentacion).limit(10)

                    # Volver a pandas para transformación y visualización
                    session_state['df_segmentacion_nit_ind_impresion'] = transformar_numericas(session_state['df_segmentacion_nit_ind_impresion_snowpark'].to_pandas())

                    # Condición para mostrar el DataFrame
                    if not session_state['df_segmentacion_nit_ind_impresion'].empty:
                        
                        # TODO : Cambiar condiciones de impresión para evitar repetición
                        # Mostrar datos
                        # st.dataframe(session_state['df_segmentacion_nit_ind_impresion'])
                        st.dataframe(session_state['df_segmentacion_nit_ind_impresion_snowpark'].to_pandas())

                        # Mostrar el número de registros del df
                        st.write(f"**Resultados:** {session_state['total_registros_nit_ind']:,} registros")

                    else:
                        st.error("No se encontró información para el NIT buscado.")

                # En caso de que no hayan resultados para la consulta específica
                else:
                    st.error("No se encontró información para el NIT buscado.")

                # Resetear la marca para no repetir la búsqueda en el siguiente rerun
                st.session_state['BUSCAR_NIT_INDIVIDUAL'] = False

        # =========== Flujo de descarga ============ #
        if preparar_descarga_boton_nit_individual:

            with st.spinner("Preparando descarga... :surfing_woman:"):

                # Crear lógica de preparación de descarga valida

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Lógica para búsqueda por NIT Individual
                if 'df_segmentacion_nit_ind' in session_state and 'total_registros_nit_ind' in session_state and session_state['total_registros_nit_ind'] > 0 \
                    and 'df_segmentacion_nit_ind_impresion' in session_state and not session_state['df_segmentacion_nit_ind_impresion'].empty \
                    and 'payload_segmentacion_nit_ind' in session_state:
                    progress_bar.progress(20)

                    # TODO : Cambiar condiciones de impresión para evitar repetición
                    # Mostrar datos
                    # st.dataframe(session_state['df_segmentacion_nit_ind_impresion'])
                    st.dataframe(session_state['df_segmentacion_nit_ind_impresion_snowpark'].to_pandas())
                    progress_bar.progress(50)

                    # Mostrar el número de registros del df
                    st.write(f"**Resultados:** {session_state['total_registros_nit_ind']:,} registros")

                    # Volver consulta a pandas para descarga
                    session_state['df_descarga_nit_ind'] = session_state['df_segmentacion_nit_ind'].to_pandas()
                    progress_bar.progress(80)

                    # Condición para habilitar el botón de descarga
                    if not session_state['df_descarga_nit_ind'].empty:

                        # Botón de descarga
                        descarga_tabla(
                            df=session_state['df_descarga_nit_ind'],
                            row_threshhold=100000,
                            label_descarga="Descargar resultados",
                            file_name='Resultados Búsqueda por NIT',
                            key_descarga='tabla_segmentacion_nit_ind',
                            sesion_activa=st.session_state.session,
                            tipo_evento="Descarga NIT Individual",
                            pagina="Segmentación",
                            filtros=session_state['payload_segmentacion_nit_ind'])
                        progress_bar.progress(100)

                # En caso de que no hayan resultados para la consulta específica
                else:
                    st.error("No se encontró información para descargar.")

    # Opción 4: Búsqueda masiva por NITs
    if vista == "Búsqueda masiva por NITs":

        # Búsqueda masiva de NITs
        st.markdown("##### **Búsqueda masiva por NITs**")

        # Estructura de botones
        col2, col3, col4, _ = st.columns(4, vertical_alignment='bottom')

        # Botones de búsqueda
        nits_boton = col2.button('Buscar Nits', type='primary', use_container_width=True, key='buscar_nits')

        # Botón de preparación de descarga
        preparar_descarga_boton_nits = col3.button('Preparar descarga', type='primary', use_container_width=True, key='preparar_descarga_nits')

        # Botón de reinicio de filtros
        reinicio_nits = col4.button("Reiniciar resultados", type='primary', use_container_width=True, key='reiniciar_nits', on_click=reset_all_filters)

        # =========== Búsqueda por NITs ============ #
        if nits_boton:

            # Función para abrir el diálogo de carga de NITs
            buscar_nits()

            # Eliminar DataFrames y conteos previos de búsquedas de segmentación general
            st.session_state.pop('df_segmentacion', None)
            st.session_state.pop('df_segmentacion_impresion', None)
            st.session_state.pop('df_segmentacion_impresion_snowpark', None)
            st.session_state.pop('total_registros', None)
            st.session_state.pop('payload_segmentacion', None)
            st.session_state.pop('df_descarga', None)

        # Si el diálogo ya guardó NITs y pidió buscar, se ejecuta:
        if st.session_state['BUSCAR_NITS'] and st.session_state['NITS']:

            # Ejecutar la búsqueda con un spinner
            with st.spinner("Ejecutando consulta... :surfing_woman:"):

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Definir el filtro de NITs del usuario para realizar la búsqueda
                dict_filtros_nits_usuario = {'NIT': list(st.session_state['NITS'])}

                # Crear los filtros que en este caso son solo NITs
                payload_nits = {
                    "generales"    : dict_filtros_nits_usuario   # sólo NITs
                }

                # Convertir a cadena JSON
                payload_nits_json = json.dumps(payload_nits, ensure_ascii=False)

                # Guardar payload en Session State para futuras referencias
                session_state['payload_segmentacion_nits'] = payload_nits_json
                progress_bar.progress(20)

                # Registrar el evento de busqueda
                registrar_evento(sesion_activa=st.session_state.session, tipo_evento='Búsqueda', pagina='Tejido Empresarial de Colombia', detalle_evento='Búsqueda por NITs', filtros=st.session_state['payload_segmentacion_nits'])
                progress_bar.progress(40)

                # Crear query
                sql_query_nits = query_data_segmentacion(dict_columnas=dict_query_segmentacion,
                                                        filtros_generales=dict_filtros_nits_usuario,
                                                        filtros_emp_export={})
                progress_bar.progress(60)

                # Ejecutar consulta y guardar resultado en Session State
                session_state['df_segmentacion_nits'] = st.session_state.session.sql(sql_query_nits)

                # Contar registros
                session_state['total_registros_nits'] = session_state['df_segmentacion_nits'].count()
                progress_bar.progress(100)

                # Mostrar los resultados si hay datos disponibles
                if session_state['total_registros_nits'] > 0:

                    # Elegir columnas para mostrar y guardar resultado en Session State (Solo se muestran las primeras 10 filas)
                    session_state['df_segmentacion_nits_impresion_snowpark'] = session_state['df_segmentacion_nits'].sort(col('"Ingresos operacionales (COP)"'), ascending=False).select(*ls_columnas_usuario_segmentacion).limit(10)

                    # Volver a pandas para transformación y visualización
                    session_state['df_segmentacion_nits_impresion'] = transformar_numericas(session_state['df_segmentacion_nits_impresion_snowpark'].to_pandas())

                    # Condición para mostrar el DataFrame
                    if not session_state['df_segmentacion_nits_impresion'].empty:
                        
                        # TODO : Cambiar condiciones de impresión para evitar repetición
                        # Mostrar datos
                        # st.dataframe(session_state['df_segmentacion_nits_impresion'])
                        st.dataframe(session_state['df_segmentacion_nits_impresion_snowpark'].to_pandas())

                        # Mostrar el número de registros del df
                        st.write(f"**Resultados:** {session_state['total_registros_nits']:,} registros")

                    else:
                        st.error("No se encontró información para los NITs cargados.")

                    # Resetear la marca para no repetir la búsqueda en el siguiente rerun
                    st.session_state['BUSCAR_NITS'] = False

                # En caso de que no hayan resultados para la consulta específica
                else:
                    st.error("No se encontró información para los NITs cargados.")

        # =========== Flujo de descarga ============ #
        if preparar_descarga_boton_nits:

            with st.spinner("Preparando descarga... :surfing_woman:"):

                # Crear lógica de preparación de descarga valida

                # Barra de progreso y realiza la lógica pesada
                progress_bar = st.progress(0)

                # Lógica para búsqueda por NITs
                if 'df_segmentacion_nits' in session_state and 'total_registros_nits' in session_state and session_state['total_registros_nits'] > 0 \
                    and 'df_segmentacion_nits_impresion' in session_state and not session_state['df_segmentacion_nits_impresion'].empty \
                    and 'payload_segmentacion_nits' in session_state:
                    progress_bar.progress(20)

                    # TODO : Cambiar condiciones de impresión para evitar repetición
                    # Mostrar datos
                    # st.dataframe(session_state['df_segmentacion_nits_impresion'])
                    st.dataframe(session_state['df_segmentacion_nits_impresion_snowpark'].to_pandas())
                    progress_bar.progress(50)

                    # Mostrar el número de registros del df
                    st.write(f"**Resultados:** {session_state['total_registros_nits']:,} registros")

                    # Volver consulta a pandas para descarga
                    session_state['df_descarga_nits'] = session_state['df_segmentacion_nits'].to_pandas()
                    progress_bar.progress(80)

                    # Condición para habilitar el botón de descarga
                    if not session_state['df_descarga_nits'].empty:

                        # Botón de descarga
                        descarga_tabla(
                            df=session_state['df_descarga_nits'],
                            row_threshhold=100000,
                            label_descarga="Descargar resultados",
                            file_name='Resultados Segmentación de Empresas por NITs',
                            key_descarga='tabla_segmentacion_nits',
                            sesion_activa=st.session_state.session,
                            tipo_evento="Descarga NITs",
                            pagina="Segmentación",
                            filtros=session_state['payload_segmentacion_nits'])
                        progress_bar.progress(100)

                    # Resetear la marca para no repetir la búsqueda en el siguiente rerun
                    st.session_state['BUSCAR_NITS'] = False

































    

    



    
    

    
    
    



# ========== Footer ==========#
footer()   