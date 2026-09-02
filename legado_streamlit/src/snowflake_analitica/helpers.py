# Librerías
from snowflake.snowpark import Session
import re
import unicodedata

def get_session_info(sesion_activa):
    """
    Retorna la ubicación actual de la sesión de Snowflake en un diccionario descriptivo.

    Parámetros:
    - sesion_activa: Objeto de sesión de Snowflake activo.

    Retorna:
    - dict: Diccionario con la información de la cuenta, rol, usuario, warehouse, base de datos y esquema actuales.
            Si ocurre un error al obtener alguno de los valores, se asignará "N/A" en su lugar.

    Arroja:
    - ValueError: Si la sesión proporcionada es inválida o es None.

    Ejemplo de uso:
    --------------
    # Crear la sesión (debes haber creado una sesión previamente)
    session = create_session_from_json("/ruta/al/archivo/snowflake_credentials.json")

    # Obtener la información de la sesión
    info_sesion = get_session_info(session)

    # Imprimir la información de la sesión
    print(info_sesion)
    """

    # Validar que la sesión proporcionada no sea None
    if sesion_activa is None:
        raise ValueError("La sesión de Snowflake proporcionada es inválida o None.")
    
    # Inicializar un diccionario con valores predeterminados "N/A"
    # para cada clave que queremos obtener de la sesión.
    session_info = {
        "account": "N/A",     # Cuenta de Snowflake
        "role": "N/A",        # Rol actual del usuario
        "user": "N/A",        # Usuario actual conectado
        "warehouse": "N/A",   # Almacén de datos actual (Warehouse)
        "database": "N/A",    # Base de datos actual
        "schema": "N/A"       # Esquema actual dentro de la base de datos
    }

    # Intentar obtener la cuenta actual de la sesión activa
    try:
        session_info["account"] = sesion_activa.get_current_account()
    except Exception as e:
        print(f"Error al obtener la cuenta: {e}")

    # Intentar obtener el rol actual de la sesión activa
    try:
        session_info["role"] = sesion_activa.get_current_role()
    except Exception as e:
        print(f"Error al obtener el rol: {e}")

    # Intentar obtener el usuario actual de la sesión activa
    try:
        session_info["user"] = sesion_activa.get_current_user()
    except Exception as e:
        print(f"Error al obtener el usuario: {e}")

    # Intentar obtener el Warehouse actual de la sesión activa
    try:
        session_info["warehouse"] = sesion_activa.get_current_warehouse()
    except Exception as e:
        print(f"Error al obtener el warehouse: {e}")

    # Intentar obtener la base de datos actual de la sesión activa
    try:
        session_info["database"] = sesion_activa.get_current_database()
    except Exception as e:
        print(f"Error al obtener la base de datos: {e}")

    # Intentar obtener el esquema actual de la sesión activa
    try:
        session_info["schema"] = sesion_activa.get_current_schema()
    except Exception as e:
        print(f"Error al obtener el esquema: {e}")

    # Retornar el diccionario con toda la información obtenida de la sesión
    return session_info

def update_session_params(sesion_activa, role=None, warehouse=None, database=None, schema=None):
    """
    Actualiza los parámetros de la sesión activa de Snowflake.
    El usuario puede cambiar uno o varios de los siguientes valores: role, warehouse, database, schema.
    
    Parámetros:
    - sesion_activa: Objeto de sesión de Snowflake activo.
    - role (str, opcional): Nuevo rol a utilizar. Si no se especifica, no se cambia.
    - warehouse (str, opcional): Nuevo warehouse a utilizar. Si no se especifica, no se cambia.
    - database (str, opcional): Nueva base de datos a utilizar. Si no se especifica, no se cambia.
    - schema (str, opcional): Nuevo esquema a utilizar. Si no se especifica, no se cambia.
    
    Arroja:
    - ValueError: Si la sesión proporcionada es inválida o es None.
    - Exception: Si ocurre un error al intentar cambiar alguno de los parámetros.

    Ejemplo de uso:
    --------------
    # Cambiar solo el warehouse y el schema
    update_session_params(sesion_activa, warehouse="nuevo_warehouse", schema="nuevo_schema")
    """

    # Validar que la sesión proporcionada no sea None
    if sesion_activa is None:
        raise ValueError("La sesión de Snowflake proporcionada es inválida o None.")
    
    # Cambiar el rol, si se proporciona
    if role:
        try:
            sesion_activa.use_role(role)
            print(f"Rol cambiado a: {role}")
        except Exception as e:
            print(f"Error al cambiar el rol a '{role}': {e}")
    
    # Cambiar el warehouse, si se proporciona
    if warehouse:
        try:
            sesion_activa.use_warehouse(warehouse)
            print(f"Warehouse cambiado a: {warehouse}")
        except Exception as e:
            print(f"Error al cambiar el warehouse a '{warehouse}': {e}")
    
    # Cambiar la base de datos, si se proporciona
    if database:
        try:
            sesion_activa.use_database(database)
            print(f"Base de datos cambiada a: {database}")
        except Exception as e:
            print(f"Error al cambiar la base de datos a '{database}': {e}")
    
    # Cambiar el esquema, si se proporciona
    if schema:
        try:
            sesion_activa.use_schema(schema)
            print(f"Esquema cambiado a: {schema}")
        except Exception as e:
            print(f"Error al cambiar el esquema a '{schema}': {e}")


def clean_column_name(nombre_col):
    """
    Limpia el nombre de la columna eliminando caracteres especiales, tildes y espacios,
    convierte el nombre a mayúsculas, reemplaza dos guiones bajos seguidos por uno solo,
    convierte '*' en 'ESTRELLA', y elimina los caracteres '(', ')'.
    
    Parámetros:
    - nombre_col (str): Nombre original de la columna.

    Retorna:
    - str: Nombre de la columna limpio y en mayúsculas.
    """
    # Convertir a mayúsculas
    nombre_col = nombre_col.upper()
    
    # Eliminar acentos y caracteres especiales
    nombre_col = unicodedata.normalize('NFKD', nombre_col).encode('ascii', 'ignore').decode('ascii')
    
    # Eliminar los caracteres '(', ')' y convertir '*' en 'ESTRELLA'
    nombre_col = re.sub(r'\*', '_ESTRELLA', nombre_col)  # Reemplazar '*' por 'ESTRELLA'
    nombre_col = re.sub(r'[()]', '', nombre_col)        # Eliminar '(' y ')'
    
    # Reemplazar cualquier carácter no alfanumérico (excepto guiones bajos) por guiones bajos
    nombre_col = re.sub(r'[^A-Z0-9_]', '_', nombre_col)
    
    # Reemplazar dos o más guiones bajos consecutivos por un solo guion bajo
    nombre_col = re.sub(r'__+', '_', nombre_col)
    
    return nombre_col


def ejecutar_script_sql_snowpark(session_activa, sql_script):
    """
    Elimina comentarios y líneas en blanco de un script SQL, lo divide en comandos individuales
    y ejecuta cada comando en la base de datos de Snowflake utilizando Snowpark Session.

    Parámetros:
    - session_activa (snowflake.snowpark.Session): La sesión activa de Snowflake.
    - sql_script (str): El script SQL a ejecutar.

    Retorna:
    - resultados (list): Lista de resultados de cada comando ejecutado exitosamente.
    """
    resultados = []

    # Eliminar los comentarios y las líneas en blanco
    sql_script = re.sub(r'--.*', '', sql_script)  # Elimina comentarios
    sql_script = re.sub(r'\s+', ' ', sql_script)  # Elimina líneas en blanco y múltiples espacios
    
    # Dividir el script en comandos individuales
    sql_commands = sql_script.split(';')
    
    # Ejecuta cada comando y almacena los resultados
    for command in sql_commands:
        command = command.strip()
        if command:
            try:
                # Ejecutar el comando SQL utilizando Snowpark Session
                result_df = session_activa.sql(command).collect()  # Ejecuta y recoge los resultados
                resultados.append(result_df)
                print(f"Ejecutado con éxito: {command[:100]}...")  # Muestra los primeros 100 caracteres del comando
            except Exception as e:
                print(f"Error al ejecutar: {command[:100]}...")
                print(f"Error: {e}")
    
    return resultados



