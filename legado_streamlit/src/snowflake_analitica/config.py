# Librerías
import os
import json
import toml
import snowflake.connector
from snowflake.snowpark import Session

def create_session_from_json(json_file_path):
    """
    Crea una sesión y conexión a Snowflake a partir de un archivo JSON con credenciales.

    Parámetros:
    - json_file_path (str): Ruta absoluta al archivo JSON que contiene las credenciales de Snowflake.

    Retorna:
    - tuple: (snowflake_session, snowflake_connection) 

    Arroja:
    - FileNotFoundError: Si el archivo JSON no se encuentra en la ruta proporcionada.
    - ValueError: Si algún parámetro obligatorio no se encuentra en el archivo JSON o está vacío.

    Ejemplo de uso:
    --------------
    # Definir la ruta al archivo JSON
    json_file_path = "/ruta/al/archivo/snowflake_credentials.json"
    
    # Crear la sesión y conexión a Snowflake
    session, connection = create_session_from_json(json_file_path)

    # Usar la sesión o conexión para interactuar con Snowflake
    print("Conexión establecida con éxito")
    
    # Cerrar la conexión al finalizar
    connection.close()
    """
    # Verificar si el archivo JSON existe
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"El archivo JSON no fue encontrado en la ruta proporcionada: {json_file_path}")
    
    # Leer las credenciales desde el archivo JSON
    with open(json_file_path, 'r') as file:
        credentials = json.load(file)

    # Verificar si los campos obligatorios están presentes y no vacíos
    required_fields = ["ACCOUNT_SNOWFLAKE", "USER_SNOWFLAKE", "PASSWORD_SNOWFLAKE", "ROLE_SNOWFLAKE", "WAREHOUSE"]
    for field in required_fields:
        if not credentials.get(field):
            raise ValueError(f"El campo obligatorio '{field}' está ausente o vacío en el archivo JSON.")
    
    # Definir los parámetros de conexión usando las credenciales del archivo JSON
    connection_parameters = {
        "account": credentials.get("ACCOUNT_SNOWFLAKE"),
        "user": credentials.get("USER_SNOWFLAKE"),
        "password": credentials.get("PASSWORD_SNOWFLAKE"),
        "role": credentials.get("ROLE_SNOWFLAKE"),
        "warehouse": credentials.get("WAREHOUSE"),
        # Se verifica que database y schema sean opcionales y no estén vacíos antes de agregarlos
        "database": credentials.get("DATABASE_SNOWFLAKE") if credentials.get("DATABASE_SNOWFLAKE") else None,
        "schema": credentials.get("SCHEMA_SNOWFLAKE") if credentials.get("SCHEMA_SNOWFLAKE") else None
    }

    # Eliminar claves que sean None para evitar errores en la creación de la sesión
    connection_parameters = {k: v for k, v in connection_parameters.items() if v is not None}

    # Crear la sesión de Snowflake utilizando snowpark
    snowflake_session = Session.builder.configs(connection_parameters).create()

    # Obtener el objeto de conexión
    snowflake_connection = snowflake_session.connection

    return snowflake_session, snowflake_connection


def create_session_from_toml(toml_file_path, section=None):
    """
    Crea una sesión y conexión a Snowflake a partir de un archivo TOML con credenciales.

    Parámetros:
    - toml_file_path (str): Ruta absoluta al archivo TOML que contiene las credenciales de Snowflake.
    - section (str, opcional): Nombre de la sección en el archivo TOML donde se encuentran las credenciales.
                             La lógica espera que las secciones sean anidadas, como 'connections.snowflake'.

    Retorna:
    - tuple: (snowflake_session, snowflake_connection)

    Arroja:
    - FileNotFoundError: Si el archivo TOML no se encuentra en la ruta proporcionada.
    - ValueError: Si algún parámetro obligatorio no se encuentra en el archivo TOML o está vacío.

    Ejemplo de uso:
    --------------
    # Definir la ruta al archivo TOML
    toml_file_path = "/ruta/al/archivo/snowflake_credentials.toml"
    
    # Crear la sesión y conexión a Snowflake (con sección anidada)
    session, connection = create_session_from_toml(toml_file_path, section="connections.snowflake")

    # Crear la sesión y conexión a Snowflake (sin sección)
    session, connection = create_session_from_toml(toml_file_path)

    # Cerrar la conexión al finalizar
    connection.close()
    """
    
    # Verificar si el archivo TOML existe
    if not os.path.exists(toml_file_path):
        raise FileNotFoundError(f"El archivo TOML no fue encontrado en la ruta proporcionada: {toml_file_path}")
    
    # Leer las credenciales desde el archivo TOML
    credentials = toml.load(toml_file_path)
    
    # Si se proporciona una sección, navegar a través de las claves anidadas (e.g., connections.snowflake)
    if section:
        try:
            # Separar las claves si hay subniveles, por ejemplo "connections.snowflake"
            keys = section.split('.')
            for key in keys:
                credentials = credentials.get(key)
                if credentials is None:
                    raise ValueError(f"La sección '{section}' no fue encontrada en el archivo TOML.")
        except Exception as e:
            raise ValueError(f"Error al navegar por las secciones del archivo TOML: {e}")
    
    # Verificar si los campos obligatorios están presentes y no vacíos
    required_fields = ["account", "user", "password", "role", "warehouse"]
    for field in required_fields:
        if not credentials.get(field):
            raise ValueError(f"El campo obligatorio '{field}' está ausente o vacío en la sección '{section}' del archivo TOML.")
    
    # Definir los parámetros de conexión usando las credenciales del archivo TOML
    connection_parameters = {
        "account": credentials.get("account"),
        "user": credentials.get("user"),
        "password": credentials.get("password"),
        "role": credentials.get("role"),
        "warehouse": credentials.get("warehouse"),
        # Se verifica que database y schema sean opcionales y no estén vacíos antes de agregarlos
        "database": credentials.get("database") if credentials.get("database") else None,
        "schema": credentials.get("schema") if credentials.get("schema") else None
    }

    # Eliminar claves que sean None para evitar errores en la creación de la sesión
    connection_parameters = {k: v for k, v in connection_parameters.items() if v is not None}

    # Crear la sesión de Snowflake utilizando snowpark
    snowflake_session = Session.builder.configs(connection_parameters).create()

    # Obtener el objeto de conexión
    snowflake_connection = snowflake_session.connection

    return snowflake_session, snowflake_connection