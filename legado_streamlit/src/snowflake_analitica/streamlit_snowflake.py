# Librerías
import streamlit as st
import time
from datetime import datetime, timedelta
from snowflake.snowpark import Session
import os
from dotenv import load_dotenv
import base64

def _load_private_key(key_num: int) -> bytes | None:
    """
    Lee la llave privada como bytes desde una env var base64 (para Railway u
    otros entornos sin filesystem persistente) o, como respaldo, desde la ruta
    en disco indicada por SF_PRIVATE_KEY_PATH_{key_num} (uso local).
    """
    b64 = os.getenv(f'SF_PRIVATE_KEY_B64_{key_num}')
    if b64:
        return base64.b64decode(b64)
    path = os.getenv(f'SF_PRIVATE_KEY_PATH_{key_num}')
    if path:
        with open(path, "rb") as key_file:
            return key_file.read()
    return None

# Inicializar variables de sesión si no existen
if 'session' not in st.session_state:
    st.session_state.session = None  # Sesión inicializada como None
if 'last_activity_time' not in st.session_state:
    st.session_state.last_activity_time = datetime.now()  # Última actividad es el momento actual

# Definir tiempo de espera de sesión (15 minutos)
SESSION_TIMEOUT = timedelta(minutes=15)

# Variable de módulo: recuerda qué llave funcionó en la última conexión exitosa
# Se resetea a 1 en cada reinicio del proceso (comportamiento esperado)
_last_working_key: int = 1

# Función para crear una nueva sesión con Snowflake
def create_session(retries=5, wait=10):
    """
    Crea y configura una sesión de Snowflake con reintentos en caso de fallos.

    Parámetros
        - **retries**: Número máximo de intentos para establecer la conexión (por defecto 5).
        - **wait**: Tiempo de espera en segundos entre reintentos (por defecto 10).

    Retorna:
        - **Session**: Objeto de sesión de Snowflake si la conexión es exitosa.
        - **None**: Si todos los intentos fallan.

    Excepciones:
        - **ValueError**: Si alguna variable de entorno requerida está vacía o no definida.

    Acciones:
        - Inicia con la llave que funcionó la última vez dentro del mismo proceso.
        - Cambia a la llave de respaldo si se detecta un error de token JWT, sin esperar.
        - El sleep solo aplica a errores transitorios de red, no a errores de credenciales.

    Ejemplo de uso:
        session = create_session(retries=3, wait=5)
    """
    global _last_working_key
    load_dotenv()

    # Elegir llave de inicio según último éxito; la otra es el respaldo
    primary_key_num = _last_working_key
    fallback_key_num = 2 if primary_key_num == 1 else 1

    primary_key_passphrase = os.getenv(f'SF_PRIVATE_KEY_PASSPHRASE_{primary_key_num}')

    private_key = _load_private_key(primary_key_num)
    if not private_key:
        raise ValueError("La llave privada del usuario de servicio no está definida (ni SF_PRIVATE_KEY_B64_* ni SF_PRIVATE_KEY_PATH_*).")

    session_config = {
        "account": os.getenv('SF_ACCOUNT'),
        "user": os.getenv('SF_USER'),
        "private_key": private_key,
        "private_key_passphrase": primary_key_passphrase,
        "database": os.getenv('SF_DATABASE'),
        "schema": os.getenv('SF_SCHEMA'),
        "warehouse": os.getenv('SF_WAREHOUSE'),
        "role": os.getenv('SF_ROLE'),
        "query_tag": "SEGMENTACION_APP"
    }

    if any(value is None or value == '' for value in session_config.values()):
        raise ValueError("Una o más variables de entorno están indefinidas o vacías.")

    success = False
    key_switched = False  # Evita releer la llave de respaldo en intentos repetidos
    with st.spinner("Conectándote con Snowflake... :woman-running:"):
        for attempt in range(retries):
            try:
                session = Session.builder.configs(session_config).create()
                success = True
                _last_working_key = fallback_key_num if key_switched else primary_key_num
                break

            except Exception as e:
                print(f"Intento {attempt + 1} de {retries} fallido: \n{str(e)}")
                is_jwt_error = 'JWT token is invalid' in str(e)

                if is_jwt_error and not key_switched:
                    print(f"Error de token JWT, intentando con SF_PRIVATE_KEY_PATH_{fallback_key_num}")
                    fallback_key_passphrase = os.getenv(f'SF_PRIVATE_KEY_PASSPHRASE_{fallback_key_num}')
                    fallback_key = _load_private_key(fallback_key_num)

                    if not fallback_key or not fallback_key_passphrase:
                        print("Las variables de entorno para la llave de respaldo no están definidas correctamente.")
                        return None

                    session_config["private_key"] = fallback_key
                    session_config["private_key_passphrase"] = fallback_key_passphrase
                    key_switched = True

                # Solo esperar en errores transitorios de red, no en errores de credenciales
                if attempt < retries - 1 and not is_jwt_error:
                    time.sleep(wait)

    if success:
        return session
    else:
        raise RuntimeError("Todos los intentos de conexión con Snowflake fallaron.")
    
# Función para verificar si la sesión ha expirado
def check_session():
    """
    Verifica si la sesión actual ha expirado. Si es así, cierra la sesión.
    También asegura aquí las claves en st.session_state para evitar AttributeError
    cuando la página se recarga o al cambiar entre páginas.
    """
    # Asegurar claves necesarias en session_state (evita KeyError/AttributeError)
    if 'session' not in st.session_state:
        st.session_state['session'] = None
    if 'last_activity_time' not in st.session_state:
        st.session_state['last_activity_time'] = datetime.now()

    # Verificar expiración usando las claves garantizadas arriba
    last = st.session_state.get('last_activity_time', datetime.now())
    if (datetime.now() - last) > SESSION_TIMEOUT:
        sess = st.session_state.get('session')
        if sess:
            try:
                sess.close()  # Cerrar la sesión expirada si existe
            except Exception:
                pass
        st.session_state['session'] = None


@st.cache_resource(ttl=780, show_spinner=False)
def _cached_session():
    return create_session()

# Función para obtener la sesión activa
def get_session():
    """
    Obtiene la sesión activa desde el caché del proceso y la sincroniza
    en st.session_state.session para compatibilidad con el resto del código.
    """
    st.session_state.session = _cached_session()

# Función para actualizar el tiempo de última actividad
def update_last_activity():
    """
    Actualiza el tiempo de última actividad de la sesión al momento actual.
    """
    st.session_state.last_activity_time = datetime.now()  # Registrar última actividad

def flujo_snowflake():
    """
    Gestiona el flujo para interactuar con Snowflake.
    Obtiene la sesión desde el caché del proceso; si falla, muestra error al usuario.
    """
    try:
        get_session()
    except Exception:
        st.error("No se pudo conectar con Snowflake. Por favor recarga la página.")
        st.stop()

# Función para insertar datos en la tabla de seguimiento
def registrar_evento(sesion_activa, tipo_evento, pagina, detalle_evento, filtros):
    """
    Registra un evento en la base de datos Snowflake.

    Args:
        sesion_activa: Sesión activa de conexión a la base de datos.
        tipo_evento (str): Tipo de evento ('selección' o 'descarga').
        pagina (str): Página de la aplicación.
        detalle_evento (str): Detalle del evento (por ejemplo, 'buscar datos', 'selección país', etc).
        filtros (str): Cadena JSON que contiene los filtros (ya preparada, por ejemplo usando json.dumps con ensure_ascii=False)
    """
    try:

        # Crear consulta para el insert
        query_insert = f"""
        INSERT INTO APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO.EVENTOS 
            (TIPO_EVENTO, PAGINA, DETALLE_EVENTO, FILTROS, FECHA_HORA) 
        VALUES 
            ('{tipo_evento}', '{pagina}', '{detalle_evento}', '{filtros}', 
            CONVERT_TIMEZONE('America/Los_Angeles', 'America/Bogota', CURRENT_TIMESTAMP));
        """
        # Ejecutar la consulta SQL con los valores
        sesion_activa.sql(query_insert).collect()      
    except Exception as e:
        st.write(f"Error al registrar evento: {e}")