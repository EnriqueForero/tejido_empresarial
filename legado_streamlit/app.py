#============= Bibliotecas =============#
# Bibliotecas Externas
import streamlit as st
# Módulos Propios
from src.streamlit_analitica import navbar, home_page, footer

# ================== Configuración inicial ====================
# Configuración básica de la página en Streamlit.
st.set_page_config(
    page_title="Inicio",
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="assets/images/cubo.png"
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
    st.query_params.page = '2' # Página predeterminada si no hay parámetro 'page' en la URL.

# ================== navbar =========================
# Llamada al componente de navegación personalizada (barra de navegación).  
navbar()

# Redirección condicional según el valor del parámetro 'page' en la URL.
if st.query_params.page == '2':
    st.switch_page("pages/segmentacion.py") # Redirige a la página de segmentación. 
# if st.query_params.page == '3':
#     st.switch_page("pages/empresas.py") # Redirige a la página de empresas
# if st.query_params.page == '4':
#     st.switch_page("pages/destinos.py") # Redirige a la página de destinos
# if st.query_params.page == '5':
#     st.switch_page("pages/valor_agregado.py") # Redirige a la página de valor agregado
# if st.query_params.page == '6':
#     st.switch_page("pages/territorios.py") # Redirige a la página de territorios

# ========== Home page ==========#

# Marcador para volver al inicio    
st.markdown("<a id='top'></a>", unsafe_allow_html=True)

# Contenido
home_page()

# ========== Footer ==========#
footer()