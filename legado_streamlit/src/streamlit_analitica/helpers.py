# Librerías
import base64
import streamlit as st

@st.cache_data(show_spinner=False)
def get_image(image_path):
    """
    Función que lee un archivo de imagen binario y lo convierte en una cadena base64.
    
    Parámetros:
    -----------
    image_path : str
        Ruta absoluta o relativa de la imagen a convertir.

    Retorna:
    --------
    str
        Cadena de texto en formato base64, útil para incrustar la imagen en componentes de Streamlit.
    
    Uso:
    ----
    Ideal para cargar imágenes estáticas que se mostrarán en Streamlit, evitando lecturas
    repetitivas y disminuyendo la latencia. Tras la lectura inicial, los resultados se almacenan
    en caché gracias a la anotación @st.cache_data.
    """

    # Se abre el archivo de imagen en modo binario (rb)
    with open(image_path, "rb") as image_file:
        # Se convierte el contenido a base64
        img_data = base64.b64encode(image_file.read()).decode()
    
    return img_data

@st.cache_data(show_spinner=False)
def get_icon(image_path):
    """
    Función que lee un archivo SVG (o cualquier archivo de texto) y lo convierte en una cadena base64.
    
    Parámetros:
    -----------
    image_path : str
        Ruta absoluta o relativa del archivo .svg a convertir.

    Retorna:
    --------
    str
        Cadena de texto en formato base64, conveniente para incrustar un ícono SVG en la interfaz.
    
    Uso:
    ----
    Recomendado para íconos SVG que se requieran en la aplicación. El uso de @st.cache_data
    permite que la conversión se realice una sola vez, optimizando el tiempo de ejecución.
    """

    # Se abre el archivo en modo lectura de texto (r)
    with open(image_path, "r") as file:
        svg_data = file.read()
        
    # Se codifica la cadena SVG en formato base64
    return base64.b64encode(svg_data.encode("utf-8")).decode("utf-8")

def limpiar_cache():
    """
    Función que limpia el caché de datos de Streamlit.

    Descripción:
    ------------
    - Utiliza el método st.cache_data.clear() para eliminar todo el contenido
      almacenado en la memoria caché de la aplicación.
    - Al invocar esta función, cualquier función con @st.cache_data deberá
      volver a procesar sus datos en la siguiente llamada.

    Parámetros:
    -----------
    No recibe parámetros.

    Retorna:
    --------
    None
        Esta función no retorna ningún valor.

    Uso:
    ----
    Ideal para situaciones en las que los datos o resultados cacheados
    requieren actualizarse, forzando a la aplicación a recalcular. Se puede
    invocar, por ejemplo, desde un botón en la interfaz de Streamlit:

        if st.button("Limpiar Caché"):
            limpiar_cache()

    Precaución:
    -----------
    - Al limpiar el caché, se incrementará el tiempo de procesamiento en la
      próxima ejecución de funciones cacheadas, ya que sus resultados
      deberán volver a ser generados.
    """
    st.cache_data.clear()  # Limpia el caché de datos de Streamlit

def load_css(file_name):
    """
    Carga el contenido de un archivo CSS y lo devuelve como una cadena de texto.

    Esta función lee un archivo de hojas de estilo en cascada (CSS) desde la ruta 
    especificada y devuelve su contenido en forma de string. Es útil para insertar 
    estilos personalizados en una aplicación de Streamlit mediante `st.markdown(unsafe_allow_html=True)`.

    Parámetros:
    -----------
    file_name : str
        Ruta del archivo CSS que se desea cargar.

    Retorna:
    --------
    str
        Contenido del archivo CSS como una cadena de texto.

    Excepciones:
    ------------
    - FileNotFoundError: Se lanza si el archivo no existe en la ruta especificada.
    - IOError: Se lanza si ocurre un error al leer el archivo.

    Ejemplo de uso:
    ---------------
    ```python
    import streamlit as st

    # Cargar el archivo CSS
    css_content = load_css("styles.css")

    # Aplicar los estilos en la app de Streamlit
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    ```
    """
    with open(file_name) as f:
        return f.read()
    
# Para formato separador de miles intercambiando punto y coma
def formato_miles(valor, decimales=0):
    # f"{x:,.{decimales}f}" crea el separador con coma,
    # luego intercambiamos '.' por ',' y la coma original por '.'
    return (
        f"{valor:,.{decimales}f}"
        .replace(',', 'X')   # Primer swap: ',' -> 'X'
        .replace('.', ',')  # Segundo swap: '.' -> ','
        .replace('X', '.')  # Tercer swap: 'X' -> '.'
    )
