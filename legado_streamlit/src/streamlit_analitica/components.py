# Librerias
import streamlit as st
from .helpers import get_icon, get_image

def navbar():
    """
    Función que construye la barra de navegación (navbar) de la aplicación,
    utilizando la estructura y componentes de Bootstrap.

    Descripción:
    ------------
    - Carga la imagen del logotipo desde 'static/images/icons.png' con la
      función get_image(), devolviendo una cadena en formato base64.
    - Carga los íconos en formato SVG (house, location, sources) para mostrarlos
      en el menú de navegación con la función get_icon().
    - Inyecta la hoja de estilos de Bootstrap (v5.3.3) y luego
      genera y renderiza la estructura HTML de la barra de navegación.
    - Usa st.markdown() con unsafe_allow_html=True para que Streamlit acepte
      código HTML y CSS incrustado.

    Parámetros:
    -----------
    Ninguno.

    Retorna:
    --------
    None
        Su propósito es inyectar la navbar en la aplicación Streamlit.

    Dependencias:
    -------------
    - get_image(), get_icon(): Funciones que retornan las imágenes
      en formato base64.
    - st.markdown: Permite inyectar HTML y CSS a la aplicación.

    Uso:
    ----
    - Se recomienda llamar a navbar() al inicio de la aplicación para que la
      barra de navegación permanezca fija en la parte superior.
    - Ejemplo:
        navbar()

    Nota:
    -----
    - El uso de 'unsafe_allow_html=True' es necesario para aceptar este tipo
      de contenido.
    """

    # Se asume que ya tienes definidas las funciones get_image() y get_icon().
    logo = get_image("assets/images/icons.png")
    # house = get_icon("assets/images/house-solid.svg")
    filter = get_icon("assets/images/filter-solid.svg")
    # building = get_icon("assets/images/building-solid.svg")
    # location = get_icon("assets/images/location-dot-solid.svg")
    # check = get_icon("assets/images/check-to-slot-solid.svg")
    # map1 = get_icon("assets/images/map-solid.svg")
    top = get_icon("assets/images/top-dot-solid.svg")

    st.markdown(f"""
        <!-- Hoja de estilos de Bootstrap (CDN) -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" 
            rel="stylesheet"
            integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" 
            crossorigin="anonymous">
        
        <nav class="navbar fixed-top navbar-expand-lg" style="margin-top: 0px; background-color: #646464;">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">
                    <img src="data:image/png;base64,{logo}" width="200" height="50">
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
                        data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent"
                        aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarSupportedContent">
                    <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                        <li class="nav-item" id="nav-item-segmentacion">
                            <a class="nav-link text-white" href="?page=2" target="_self">
                                <img src="data:image/svg+xml;base64,{filter}" width="20" height="20">
                                <span style="padding-left: 1px; font-size: 14px;">Tejido Empresarial</span>
                            </a>
                        </li>
                        <!-- Botón "Volver arriba" a la derecha -->
                    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
                        <li class="nav-item" id="nav-item-Top">
                            <a class="nav-link text-white" href="#top" target="_self">
                                <img src="data:image/svg+xml;base64,{top}" width="20" height="20">
                                <span style="padding-left: 2px; font-size: 14px;">Volver arriba</span>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        <!-- Bootstrap JS -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        """, unsafe_allow_html=True)

def home_page():    
    st.markdown("""
            <style>
                [data-testid="stVerticalBlock"] {
                    gap: 0.5rem;
                }
            </style>    
            <br>
            <h2 style="font-weight: bold; text-align: center; margin-top: 50px; margin-bottom:10px; margin-left: 60px;">Herramienta de Segmentación para Exportaciones 2.0</h2> 
            <br>
        """, unsafe_allow_html=True)
    
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = "Descripción&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&gt;"

    def update_card(option):
        st.session_state.selected_option = option

    card_content = {
        "Descripción&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&gt;": ("Descripción general", "Esta herramienta brinda acceso a información clave sobre el tejido empresarial colombiano, con un enfoque en productos y servicios no minero-energéticos. Está diseñada para apoyar la gestión comercial de nuestros asesores de exportaciones, proporcionando una fuente ágil y eficiente que facilita y optimiza los procesos de identificación, segmentación y priorización de empresas, contribuyendo a una atención estratégica más efectiva."),
        "Beneficios&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&gt;": ("Beneficios", """
        <ul style="margin-top: 0px;">
            <li style="font-size: 15px;">Segmentar empresas por múltiples criterios alineados con la estrategia, facilitando el cumplimiento de métricas.</li>
            <li style="font-size: 15px;">Facilitar la identificación y priorización de empresas según características que el asesor requiera.</li>
            <li style="font-size: 15px;">Detectar nuevas empresas para brindarles servicios ofrecidos por ProColombia.</li>
            <li style="font-size: 15px;">Identificar empresas objetivo para invitarlas a eventos específicos.</li>
            <li style="font-size: 15px;">Obtener un perfil de cada empresa con información como actividad económica, información financiera, historial exportador, relación con ProColombia y datos de contacto.</li>
            <li style="font-size: 15px;">Centralizar la información de distintas bases de datos empresariales en un solo lugar, reduciendo el tiempo y esfuerzo requerido en la búsqueda de empresas.</li>
        </ul>
        """),
        "Alcance y límites&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&gt;": ("Alcance y límites", """
        <ul style="margin-top: 0px;">
            <li style="font-size: 15px;">Abarca tanto empresas de bienes como de servicios.</li>
            <li style="font-size: 15px;">Información netamente cuantitativa que facilita la identificación y filtrado de empresas. Sin embargo, la segmentación final debe ser realizada por los asesores según sus propios criterios y aspectos cualitativos.</li>
            <li style="font-size: 15px;">No reemplaza otras bases de datos o herramientas desarrolladas por la Gerencia de Inteligencia Comercial.</li>
            <li style="font-size: 15px;">Este recurso no reemplaza los análisis de la Vicepresidencia de Planeación, sino que los complementa para una mejor toma de decisiones estratégicas.</li>
            <li style="font-size: 15px;">Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y, en consecuencia, no representan el total de la exportación de estos sectores en el país.</li>
        </ul>
        """),
    }

    st.markdown('''
        <style>
            /* Solo reglas de tamaño y posición exclusivas del home */
            button[data-testid="stBaseButton-primary"], .stDownloadButton>button {
                padding: 12px 20px; 
                font-size: 12px; 
                cursor: pointer; 
                width: 40%;
                margin-left: 300px;
                margin-top: 15px;
            }
            button[data-testid="stBaseButton-primary"]:focus, .stDownloadButton>button:focus {
                outline: none; 
            }
        </style>
    ''', unsafe_allow_html=True)

    col1, col2 = st.columns([0.40, 0.60])

    with col1:                  
        for option in card_content.keys():
            if st.button(option, type="primary"):
                update_card(option) 
                  
        with open("assets/docs/Metodología.docx", "rb") as file:
            met_button = st.download_button("Metodología&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&gt;", file, file_name="Metodología.docx", type="primary")   
            
        with open("assets/docs/Glosario.docx", "rb") as file:
            gls_button = st.download_button("Glosario&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&gt;", file, file_name="Glosario.docx")        

    with col2:
        title, text = card_content[st.session_state.selected_option]    
        st.markdown(f'''
            <div class="card" style="width: 70%; margin-left: 5px; margin-bottom: 40px; margin-top: 15px; height: 340px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 20px 20px;">
                <div class="card-body"> 
                    <h5 class="card-title" style="text-align:left; font-size: 16px; font-weight: bold; margin-top: 10px;">{title}</h5>
                    <p class="card-text" style="font-size: 15px; margin-top: 10px;">{text}</p>
                </div>
            </div>
        ''', unsafe_allow_html=True)     

def footer():
    """
    Agrega un pie de página personalizado en una aplicación de Streamlit.

    Esta función define y renderiza un pie de página con información de contacto, 
    enlaces de interés y secciones de los ejes estratégicos de ProColombia. Se 
    aplica CSS personalizado para ocultar el pie de página predeterminado de Streamlit 
    y agregar un nuevo diseño con una estructura más definida.

    Características:
    ----------------
    - Modifica el padding del contenedor principal de Streamlit.
    - Define estilos para enlaces con diferentes estados (normal, visitado, hover, activo).
    - Oculta el pie de página predeterminado (`footer{visibility:hidden;}`).
    - Crea un nuevo pie de página con:
        - Información de contacto de ProColombia.
        - Enlaces a los principales ejes estratégicos (Exportaciones, Inversión, Turismo, Marca País).
        - Enlaces de interés (Servicios al ciudadano, Sostenibilidad, PQRFS, Contacto).
    - Aplica estilos CSS para mejorar la presentación del contenido.

    Retorna:
    --------
    - Renderiza el pie de página en la aplicación de Streamlit usando `st.write()` con `unsafe_allow_html=True`.

    Ejemplo de uso:
    ---------------
    Llamar a la función `footer()` al final de la aplicación para que el pie de página se renderice correctamente.

    ```python
    import streamlit as st
    
    # Contenido de la app
    st.title("Mi Aplicación en Streamlit")

    # Renderizar el pie de página
    footer()
    ```

    """
        
    ft = """
    <style>
    [data-testid="stMainBlockContainer"] {
        padding: 25px 0px 0px 0px;
    }
    
    /* --- NUEVO: COLORES GLOBALES PARA BOTONES --- */
    button[data-testid="stBaseButton-primary"], .stDownloadButton>button {
        background-color: #485A68 !important; 
        color: white !important;
        border: none !important; 
        border-radius: 8px !important; 
        transition: background-color 0.3s ease !important; 
    }

    button[data-testid="stBaseButton-primary"]:hover, .stDownloadButton>button:hover {
        background-color: #FF4C4C !important; 
    }
    
    a:link , a:visited{
    color: #BFBFBF;  
    background-color: transparent;
    text-decoration: none;
    }

    a:hover,  a:active {
    color: #0283C3; 
    background-color: transparent;
    text-decoration: underline;
    }

    #page-container {
    position: relative;
    min-height: 10vh;
    }

    footer{
        visibility:hidden;
    }

    .footer {
    position: relative;
    left: 0;
    top:100px;
    bottom: 0;
    width: 100%;
    background-color: #646464;
    padding: 12px 380px;
    color: #808080; 
    text-align: left; 
    }
    
    .footer h5 {
        color: white; 
        font-size: 12px; 
        font-weight: bold;
    }
    
    .footer ul {
        list-style: none; 
        padding: 0; 
        margin: 0; 
    }
    
    .footer li {
        font-size: 12px;
        color: white; 
        line-height: 1.3; 
        padding-left: 0; 
        margin-left: 0;
    }
    
    .footer a   {
        color:white;
    }
    
    </style>

    <br><br><br>  <!-- Agregar espacio antes del pie de página -->
    <br><br><br>  <!-- Agregar espacio antes del pie de página -->


    <div id="page-container">

    <div class="footer">
        <div class="row" style="margin-left: 60px;">
                <div class="col-md-4">
                    <h5 style="margin-bottom: 3px;" >LÍNEAS DE ATENCIÓN</h5>
                    <ul>
                        <li>Calle 28 No 13A - 15 Piso 35-36</li>
                        <li>Bogotá - Colombia</li>
                        <li>+57 601 5600100</li>
                        <li>Fax: +57 601 5600104</li>
                        <li>Lun - Vi 8:30 A.M. - 5:30 P.M</li>
                    </ul>
                </div>
                <div class="col-md-3">
                    <h5 style="margin-bottom: 3px;">NUESTROS EJES</h5>
                    <ul>
                        <li><a href="https://procolombia.co/" target="_blank">Procolombia</a></li>
                        <li><a href="https://investincolombia.com.co/es" target="_blank">Inversión</a></li>
                        <li><a href="https://procolombia.co/colombiatrade" target="_blank">Exportaciones</a></li>
                        <li><a href="https://colombia.travel/es" target="_blank">Turismo</a></li>
                        <li><a href="https://colombia.co/" target="_blank">Marca País</a></li>
                    </ul>
                </div>
                <div class="col-md-4">
                    <h5 style="margin-bottom: 3px;">ENLACES DE INTERÉS</h5>
                    <ul>
                        <li><a href="https://procolombia.co/transparencia/glosario" target="_blank">Servicios al ciudadano</a></li>
                        <li><a href="https://procolombia.co/sostenibilidad" target="_blank">Informe de sostenibilidad</a></li>
                        <li><a href="https://procolombia.co/transparencia/preguntas-frecuentes" target="_blank">Preguntas frecuentes</a></li>
                        <li><a href="https://procolombia.co/transparencia/pqrfs" target="_blank">PQRFS</a></li>
                        <li><a href="https://procolombia.co/contacto" target="_blank">Contacto</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """
    return st.write(ft, unsafe_allow_html=True)