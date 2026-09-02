# Librerías
import streamlit as st
import pandas as pd
from io import BytesIO
from src.snowflake_analitica import registrar_evento
import plotly.graph_objects as go
from openpyxl.cell.rich_text import TextBlock, CellRichText
from openpyxl.cell.text import InlineFont

@st.cache_data(show_spinner="Cargando filtros generales para empresas...")
def load_filtros_generales(_session) -> pd.DataFrame:
    """
    Carga los filtros generales desde una tabla en Snowflake y los convierte en un DataFrame de pandas.

    Esta función utiliza la caché de Streamlit para evitar recargar los datos en cada ejecución,
    mejorando el rendimiento de la aplicación. Se muestra un spinner con el mensaje
    "Cargando filtros desde Snowflake…" mientras se ejecuta la consulta.

    Parámetros:
    ----------
    session : snowflake.snowpark.Session
        Sesión activa de Snowflake desde la cual se ejecuta la consulta SQL.

    Retorna:
    -------
    pd.DataFrame
        DataFrame que contiene los datos de la tabla 
        APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_GENERALES.
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_GENERALES_TEJIDO_EMPRESARIAL_COMPLETO
    """
    return pd.DataFrame(_session.sql(query).collect())


@st.cache_data(show_spinner="Cargando filtros generales para exportadoras...")
def load_filtros_exportadoras(_session) -> pd.DataFrame:
    """
    Carga los filtros para empresas exportadoras desde una tabla en Snowflake y los convierte en un DataFrame de pandas.

    Esta función utiliza la caché de Streamlit para evitar recargar los datos en cada ejecución,
    mejorando el rendimiento de la aplicación. Se muestra un spinner con el mensaje
    "Cargando filtros desde Snowflake…" mientras se ejecuta la consulta.

    Parámetros:
    ----------
    session : snowflake.snowpark.Session
        Sesión activa de Snowflake desde la cual se ejecuta la consulta SQL.

    Retorna:
    -------
    pd.DataFrame
        DataFrame que contiene los datos de la tabla 
        APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_EXPORTADORAS
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_EXPORTADORAS
    """
    return pd.DataFrame(_session.sql(query).collect())

@st.cache_data(show_spinner="Cargando filtros de bienes...")
def load_filtros_bienes(_session) -> pd.DataFrame:
    """
    Carga los filtros de exportaciones de bienes desde una tabla en Snowflake y los convierte en un DataFrame de pandas.

    Esta función utiliza la caché de Streamlit para evitar recargar los datos en cada ejecución,
    mejorando el rendimiento de la aplicación. Se muestra un spinner con el mensaje
    "Cargando filtros desde Snowflake…" mientras se ejecuta la consulta.

    Parámetros:
    ----------
    session : snowflake.snowpark.Session
        Sesión activa de Snowflake desde la cual se ejecuta la consulta SQL.

    Retorna:
    -------
    pd.DataFrame
        DataFrame que contiene los datos de la tabla 
        APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_BIENES.
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_BIENES
    """
    return pd.DataFrame(_session.sql(query).collect())

@st.cache_data(show_spinner="Cargando filtros de departamentos...")
def load_filtros_departamentos_servicios(_session) -> pd.DataFrame:
    """
    Carga los filtros de servicios desde una tabla en Snowflake y los convierte en un DataFrame de pandas.
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_DEPARTAMENTOS_SERVICIOS
    """
    return pd.DataFrame(_session.sql(query).collect())

@st.cache_data(show_spinner="Cargando filtros de departamentos...")
def load_filtros_departamentos_exportaciones(_session) -> pd.DataFrame:
    """
    Carga los filtros de exportaciones desde una tabla en Snowflake y los convierte en un DataFrame de pandas.
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_DEPARTAMENTOS_EXPORTACIONES
    """
    return pd.DataFrame(_session.sql(query).collect())


@st.cache_data(show_spinner="Cargando filtros de municipios...")
def load_filtros_municipios_exportaciones(_session) -> pd.DataFrame:
    """
    Carga los filtros de exportaciones desde una tabla en Snowflake y los convierte en un DataFrame de pandas.
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_MUNICIPIOS_EXPORTACIONES
    """
    return pd.DataFrame(_session.sql(query).collect())

@st.cache_data(show_spinner="Cargando filtros de municipios...")
def load_filtros_municipios_socioec(_session) -> pd.DataFrame:
    """
    Carga los filtros de exportaciones desde una tabla en Snowflake y los convierte en un DataFrame de pandas.
    """
    query = """
        SELECT *
        FROM APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.FILTROS_MUNICIPIOS_SOCIOEC
    """
    return pd.DataFrame(_session.sql(query).collect())

def get_filtered_df(
    columnas_filtros: list[str],
    base_df: pd.DataFrame,
    excluye: str | None = None
) -> pd.DataFrame:
    """
    Filtra ``base_df`` según las selecciones guardadas en ``st.session_state``.

    El filtrado es un AND lógico entre columnas.  Cuando se está calculando
    la lista de opciones para *una* columna concreta, se pasa su nombre en
    ``excluye`` para **no** auto‑filtrarse con esa misma columna.

    Args:
        columnas_filtros (list[str]): Columnas que participan como filtros.
        base_df (pd.DataFrame):      DataFrame original sin filtrar.
        excluye (str | None):        Columna que se ignora en esta llamada.

    Returns:
        pd.DataFrame: DataFrame resultante con los filtros activos.
    """
    df_tmp = base_df
    for col in columnas_filtros:
        if col == excluye:
            continue
        valores = st.session_state[col]
        if valores:                               # aplica sólo si hay selección
            df_tmp = df_tmp[df_tmp[col].isin(valores)]
    return df_tmp

def transformar_numericas(df):
    """
    Toma un DataFrame y transforma las columnas numéricas (tipo float, decimal, etc.) 
    aplicando la siguiente lógica de formateo:
    
        1. Se formatea el número usando la sintaxis f"{valor:,.0f}" para generar separadores
           de miles (por defecto sin decimales).
        2. Se realiza el siguiente intercambio:
             - Se reemplaza la coma (,) por el caracter temporal 'X'
             - Se reemplaza el punto (.) por coma (,)
             - Se reemplaza 'X' por punto (.)
    
    Esto resulta en que los números tengan puntos como separador de miles y coma como 
    separador decimal.
    
    Parámetros:
        df (pd.DataFrame): DataFrame a transformar.
        
    Retorna:
        pd.DataFrame: Nuevo DataFrame con las columnas numéricas transformadas a cadenas
                      con el formato indicado.
    
    Ejemplo de uso:
        >>> data = {'A': [1000.55, 2000.75, None], 'B': ['texto', 'más texto', 'sin cambio']}
        >>> df = pd.DataFrame(data)
        >>> df_transformado = transformar_numericas(df)
        >>> print(df_transformado)
                A           B
          0  1.001       texto
          1  2.001   más texto
          2   None  sin cambio
    """
    # Se crea una copia del DataFrame para no modificar el original
    df_transformado = df.copy()
    
    # Iterar sobre cada columna del DataFrame
    for col in df_transformado.columns:
        # Verificar si la columna es de tipo numérico (incluye float, decimal, int, etc.)
        if pd.api.types.is_numeric_dtype(df_transformado[col]):
            # Aplicar la lógica de formateo a cada valor numérico.
            # Se usa un lambda que primero formatea el número y luego realiza los reemplazos.
            df_transformado[col] = df_transformado[col].apply(
                lambda x: (f"{x:,.0f}").replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else x
            )
    
    return df_transformado

def format_espanol(x: int | float, decimales=2) -> str:
    """
    Formatea un número (entero o flotante) a una cadena con formato numérico en español.

    La función convierte el número `x` en una cadena de texto que incluye:
      - Un separador de miles con punto ('.').
      - Un separador decimal con coma (',') si se especifican decimales.
    
    Para lograr esto, se formatea inicialmente el número usando el formateo de cadenas de Python,
    que incluye comas para separar los miles y puntos para los decimales (estilo inglés), y luego se
    intercambian estos caracteres para adaptarlos al formato español.

    Parámetros:
      x : int | float
          El número a formatear.
      decimales : int, opcional
          La cantidad de decimales que se desean en la representación. Por defecto es 2.
          - Si `decimales` es mayor que 0, se formatea el número con la cantidad indicada de decimales.
          - Si `decimales` es 0, se formatea el número sin decimales.

    Retorna:
      str: Una cadena que representa el número con formato español.
      
    Ejemplos:
      >>> format_espanol(1234567.891)
      '1.234.567,89'
      
      >>> format_espanol(1234567.891, 0)
      '1.234.568'
      
    Notas:
      - En el caso de que `decimales` sea mayor que 0, el proceso es el siguiente:
          1. Se aplica el formateo {x:,.{decimales}f}, que genera una cadena con separador de miles (',')
             y separador decimal ('.'), por ejemplo, "1,234,567.89".
          2. Se intercambian primero las comas por un carácter temporal ('?'),
             luego los puntos por comas, y finalmente el carácter temporal por puntos.
      - Si `decimales` es 0, se reemplazan las comas generadas (separadores de miles) por puntos.
    """
    if decimales > 0:
        return f"{x:,.{decimales}f}".replace(',', '?').replace('.', ',').replace('?', '.')
    else:
        return f"{x:,.{decimales}f}".replace(',', '.')


@st.cache_resource(show_spinner=False)
def convert_to_csv(df: pd.DataFrame):
    """
    Convierte un DataFrame de Pandas a un archivo CSV codificado en UTF-8.

    La función genera un CSV a partir del DataFrame recibido utilizando el separador
    tab ('|'), separador de decimales (',') y sin incluir el índice, devolviendo el resultado como una cadena
    de bytes (UTF-8).

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame a convertir en CSV.

    Retorna:
    --------
    bytes
        CSV generado a partir del DataFrame codificado en UTF-8.
    """
    return df.to_csv(index = False, sep='|', decimal=',').encode("utf-8")


@st.cache_data(show_spinner=False)
def convert_to_excel(df: pd.DataFrame, nota: str = "", agregar_nota: bool = False) -> BytesIO:
    """
    Genera un archivo Excel a partir de un DataFrame y devuelve un objeto BytesIO.
    Agrega una nota en la celda A1 con la palabra "Nota: " en negrita.
    """
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Se crea la hoja vacía inicial (mantengo tu lógica)
        pd.DataFrame().to_excel(writer, sheet_name="Sheet1", index=False, header=False)
        
        if agregar_nota and nota:
            df.to_excel(writer, sheet_name="Sheet1", index=False, header=True, startrow=2)
            ws = writer.sheets["Sheet1"]
            
            # Crear el formato de texto enriquecido (Rich Text)
            fuente_negrita = InlineFont(b=True)
            texto_enriquecido = CellRichText(
                TextBlock(font=fuente_negrita, text="Nota: "),
                f"{nota}" # El resto del texto en formato normal
            )
            
            ws["A1"] = texto_enriquecido
        else:
            df.to_excel(writer, sheet_name="Sheet1", index=False, header=True, startrow=0)
            
    buffer.seek(0)
    return buffer

@st.fragment
def descarga_tabla(
    df: pd.DataFrame,
    row_threshhold: int = 1500,
    label_descarga: str = "Descargar",
    file_name: str = 'resultado',
    key_descarga: str = 'tabla',
    sesion_activa = None,
    tipo_evento: str = "",
    pagina: str = "",
    filtros: str = "",
    nota: str = "",
    agregar_nota: bool = False
) -> None:
    """
    Genera un botón de descarga en Streamlit que permite al usuario descargar el contenido de un DataFrame.
    
    Dependiendo de la cantidad de filas del DataFrame, el botón generará un archivo Excel o CSV,
    y al mismo tiempo registrará un evento en Snowflake usando la función `registrar_evento`.
    
    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame que se desea descargar.

    row_threshhold : int, opcional (default=1500)
        Umbral de filas para determinar el formato de descarga. Si el DataFrame tiene menos filas que este
        valor, se exporta a Excel; de lo contrario, se exporta a CSV.
    
    label_descarga : str, opcional (default="Descargar")
        Texto que se mostrará en el botón de descarga.
    
    file_name : str, opcional (default="resultado")
        Nombre base del archivo que se descargará. La extensión se añadirá según el formato utilizado.
    
    key_descarga : str, opcional (default="tabla")
        Clave única para el botón en Streamlit para evitar colisiones en la caché de widgets.
    
    sesion_activa : snowflake.snowpark.session.Session
        Sesión activa de conexión a la base de datos Snowflake que se usará para registrar el evento.
    
    tipo_evento : str
        Tipo de evento (por ejemplo, "Búsqueda", "Descarga") que se utilizará al registrar el evento.
    
    pagina : str
        Nombre o identificador de la página de la aplicación desde la cual se realiza la descarga.
    
    filtros : str
        Información en formato string (puede ser un JSON o una concatenación de filtros) que se registra 
        como detalle de filtros aplicados en el evento.
    
    Retorna
    -------
    None
    
    Comportamiento
    --------------
    - Si el DataFrame tiene menos filas que `row_threshhold`, se convierte a Excel utilizando la función
      `convert_to_excel`, se asigna el MIME type correspondiente, y se define un evento de descarga de archivo Excel.
    - Si el DataFrame tiene un número de filas mayor o igual al umbral, se convierte a CSV utilizando la función
      `convert_to_csv`, se asigna el MIME type correspondiente, y se define un evento de descarga de archivo CSV.
    - Al presionar el botón se llama a la función `registrar_evento` para dejar constancia del evento en Snowflake.
    
    Nota:
    -----
    Se asume que las funciones `convert_to_excel` y `convert_to_csv` están definidas en el contexto o importadas
    en el módulo actual.
    """
    
    # Seleccionar el formato de exportación basado en la cantidad de filas
    if len(df) < row_threshhold:
        export = convert_to_excel(df, nota=nota, agregar_nota=agregar_nota)
        mime = "application/vnd.ms-excel"
        extension = '.xlsx'
        detalle_evento = 'Descarga Archivo Excel'
    else:
        export = convert_to_csv(df)
        mime = "text/csv"
        extension = '.csv'
        detalle_evento = 'Descarga Archivo CSV'
    
    # Crear el botón de descarga
    st.download_button(
        label=label_descarga,
        data=export,
        on_click=registrar_evento,
        args=(
            sesion_activa,
            tipo_evento,
            pagina,
            detalle_evento,
            filtros
        ),
        file_name=file_name + extension,
        mime=mime,
        use_container_width=True,
        key=key_descarga
    )


@st.cache_data(show_spinner=False)
def read_file_content(file):
    """
    Lee el contenido de un archivo y lo decodifica en texto.

    Parámetros
        - **file**: Archivo cargado, generalmente un objeto tipo `BytesIO` o similar.

    Retorna:
        - **contenido**: Contenido del archivo decodificado como una cadena de texto en formato UTF-8.
    """
    return file.read().decode("utf-8")

def format_espanol(x: int | float, decimales=2) -> str:
    """
    Formatea un número (entero o flotante) a una cadena con formato numérico en español.

    La función convierte el número `x` en una cadena de texto que incluye:
      - Un separador de miles con punto ('.').
      - Un separador decimal con coma (',') si se especifican decimales.
    
    Para lograr esto, se formatea inicialmente el número usando el formateo de cadenas de Python,
    que incluye comas para separar los miles y puntos para los decimales (estilo inglés), y luego se
    intercambian estos caracteres para adaptarlos al formato español.

    Parámetros:
      x : int | float
          El número a formatear.
      decimales : int, opcional
          La cantidad de decimales que se desean en la representación. Por defecto es 2.
          - Si `decimales` es mayor que 0, se formatea el número con la cantidad indicada de decimales.
          - Si `decimales` es 0, se formatea el número sin decimales.

    Retorna:
      str: Una cadena que representa el número con formato español.
      
    Ejemplos:
      >>> format_espanol(1234567.891)
      '1.234.567,89'
      
      >>> format_espanol(1234567.891, 0)
      '1.234.568'
    """
    if decimales > 0:
        return f"{x:,.{decimales}f}".replace(',', '?').replace('.', ',').replace('?', '.')
    else:
        return f"{x:,.{decimales}f}".replace(',', '.')

def milify(n: int | float) -> str:
    """
    Convierte un número a una representación estandarizada en millones con el sufijo 'M',
    formateada según la convención en español.
    
    Para evitar la confusión visual en tablas y gráficos, esta función unifica la 
    escala a millones (M) y ajusta dinámicamente la precisión decimal según la 
    magnitud del valor:
    
      - Valores >= 100.000: Se muestran con 1 decimal.
      - Valores entre 10.000 y 99.999: Se muestran con 2 decimales.
      - Valores < 10.000: Se muestran con 3 decimales.
    
    La función depende de `format_espanol` para aplicar correctamente los separadores 
    de miles (punto) y decimales (coma).
    
    Parámetros:
    -----------
    n : int | float
        El número a formatear.
    
    Retorna:
    --------
    str
        Una cadena que representa el número en millones ('M') con la precisión 
        decimal correspondiente.
    
    Ejemplos:
    ---------
    >>> milify(1500000)
    '1,5 M'
    
    >>> milify(50000)
    '0,05 M'
    
    >>> milify(9500)
    '0,010 M'
    """
    n = float(n)
    valor_en_millones = n / 1e6
    abs_n = abs(n)
    
    if abs_n >= 100000:
        return format_espanol(valor_en_millones, 1) + " M"
    elif abs_n >= 10000:
        return format_espanol(valor_en_millones, 2) + " M"
    elif abs_n == 0:
        return "0 M"
    else:
        return format_espanol(valor_en_millones, 3) + " M"
    
def mostrar_resultado_en_streamlit(resultado, fuente, llave):

    """
    Muestra un resultado en Streamlit según el tipo de dato recibido.
    - Si el resultado es un gráfico de Plotly (go.Figure), se visualiza con st.plotly_chart y se añade una leyenda con la fuente.
    - Si es una cadena de texto, se despliega usando st.write junto a una leyenda con la fuente.
    - Para otros tipos, se muestra una advertencia indicando que el tipo de resultado no es reconocido.
    """

    # Caso 1: Gráfico de Plotly
    if isinstance(resultado, go.Figure):
        st.plotly_chart(resultado, use_container_width=True, key=llave)
        st.caption(f'Fuente: {fuente}')

    # Caso 2: Cadena de texto
    elif isinstance(resultado, str):
        st.error("No se encontro información que cumpla con los filtros seleccionados.")
        st.caption(f'Fuente: {fuente}')

    # Caso 3: Tipo no soportado
    else:
        st.warning(f"Tipo de resultado no reconocido o no soportado: {type(resultado)}")