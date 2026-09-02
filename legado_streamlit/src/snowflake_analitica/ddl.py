# DDL significa Data Definition Language o Lenguaje de Definición de Datos, en español. 
# Este lenguaje permite definir las tareas de las estructuras que almacenarán los datos.
# Sentencias de DDL (Data Definition Language)
    # CREATE: Utilizado para crear nuevas tablas, campos e índices.
    # ALTER: Utilizado para modificar las tablas agregando campos o cambiando la definición de los campos.
    # DROP: Empleado para eliminar tablas e índices.
    # TRUNCATE: Empleado para eliminar todos los registros de una tabla.
    # COMMENT: Utilizado para agregar comentarios al diccionario de datos.
    # RENAME: Tal como su nombre lo indica es utilizado para renombrar objetos.

# Módulos
from .helpers import get_session_info, update_session_params, clean_column_name

# Liberías
import pandas as pd
import time
from snowflake.snowpark import Session

def generate_create_table_script(nombre_tabla, df):
    """
    Genera un script SQL para crear una tabla en Snowflake basado en el DataFrame dado.
    Los nombres de las columnas se limpian de caracteres especiales y se convierten a mayúsculas.

    Parámetros:
    - nombre_tabla (str): Nombre de la tabla a crear.
    - df (pandas.DataFrame): DataFrame de Pandas que contiene las columnas y tipos de datos.

    Retorna:
    - str: Script SQL para crear la tabla en Snowflake.

    Ejemplo de uso:
    --------------
    # Crear un DataFrame de ejemplo
    data = {'columna 1': [1, 2], 'columna2ñ': ['texto1', 'texto2'], 'columna con tildes': [True, False]}
    df = pd.DataFrame(data)
    
    # Generar el script SQL
    nombre_tabla = 'mi_tabla_ejemplo'
    script_sql = generate_create_table_script(nombre_tabla, df)
    
    # Imprimir el script SQL
    print(script_sql)
    """

    # Mapeo de tipos de datos Python/Numpy/Pandas a SQL (Snowflake)
    tipo_datos_map = {
        # Tipos numéricos
        'float64': 'FLOAT',    # Numpy/Pandas float
        'int64': 'FLOAT',      # Numpy/Pandas integer
        'float': 'FLOAT',      # Python float
        'int': 'FLOAT',        # Python int

        # Tipos de cadenas
        'object': 'STRING',    # Pandas object, usualmente strings
        'str': 'STRING',       # Python string

        # Tipos booleanos
        'bool': 'BOOLEAN',     # Python boolean
        'bool_': 'BOOLEAN',    # Numpy boolean

        # Tipos de fecha y tiempo
        'datetime64': 'DATETIME',        # Numpy/Pandas datetime
        'datetime64[ns]': 'DATETIME',    # Numpy/Pandas datetime con precisión de nanosegundos
        'datetime.date': 'DATE',         # Python date
        'datetime.datetime': 'DATETIME', # Python datetime

        # Tipos de datos estructurados (más complejos)
        'list': 'ARRAY',       # Listas podrían mapearse a arrays en SQL
        'dict': 'JSON',        # Diccionarios podrían mapearse a JSON en SQL
        'tuple': 'ARRAY',      # Tuplas podrían mapearse a arrays en SQL
        'set': 'ARRAY',        # Sets podrían mapearse a arrays en SQL

        # Tipos de datos binarios
        'bytes': 'BLOB'        # Python bytes
    }

    # Iniciar la sentencia SQL para crear la tabla
    create_table_query = f'CREATE OR REPLACE TABLE {nombre_tabla} (\n'
    
    # Añadir las columnas y sus tipos basándose en el DataFrame y el diccionario de tipos
    for col, dtype in df.dtypes.items():
        # Limpiar el nombre de la columna
        col_limpio = clean_column_name(col)
        
        # Obtener el tipo de datos correspondiente en SQL, o usar 'STRING' por defecto
        snowflake_type = tipo_datos_map.get(str(dtype), 'STRING')
        create_table_query += f"  {col_limpio} {snowflake_type},\n"
    
    # Remover la última coma, cerrar el paréntesis y agregar el punto y coma final
    create_table_query = create_table_query.rstrip(',\n') + "\n);"

    return create_table_query


def upload_dataframe_to_snowflake(sesion_activa, df, nombre_tabla, role=None, warehouse=None, database=None, schema=None, create_table=True, overwrite=False, ram_gb=32):
    """
    Carga un DataFrame de Pandas a Snowflake.
    El proceso incluye crear la tabla basada en la estructura del DataFrame (opcional), cambiar la sesión si es necesario, y luego cargar los datos.

    Parámetros:
    - sesion_activa: Objeto de sesión de Snowflake activo.
    - df (pandas.DataFrame): DataFrame de Pandas que se va a cargar.
    - nombre_tabla (str): Nombre de la tabla en Snowflake donde se va a cargar el DataFrame.
    - role (str, opcional): Nuevo rol a utilizar. Si no se especifica, no se cambia.
    - warehouse (str, opcional): Nuevo warehouse a utilizar. Si no se especifica, no se cambia.
    - database (str, opcional): Nueva base de datos a utilizar. Si no se especifica, no se cambia.
    - schema (str, opcional): Nuevo esquema a utilizar. Si no se especifica, no se cambia.
    - create_table (bool, opcional): Si es True, se crea la tabla desde cero. Si es False, se hace un append de los datos.
    - overwrite (bool, opcional): Si es True, reemplaza los datos existentes en la tabla. Si es False, los datos se añaden.
    - ram_gb (int, opcional): Cantidad de RAM en GB asignada al proceso de carga (por defecto 32 GB).

    Retorna:
    - mensajes (list): Lista de mensajes que describen el proceso de carga.

    Combinaciones de `create_table` y `overwrite`:
    ---------------------------------------------
    - `create_table=True`, `overwrite=False`: Crea la tabla desde cero y añade datos. Si la tabla existe, lanzará un error.
    - `create_table=False`, `overwrite=False`: Hace append de los datos a la tabla existente, sin sobrescribir los anteriores.
    - `create_table=True`, `overwrite=True`: Crea la tabla desde cero, sobrescribiendo cualquier dato anterior.
    - `create_table=False`, `overwrite=True`: Hace append de los datos, pero sobrescribe cualquier dato existente en la tabla.
    """
    mensajes = []

    # Actualizar parámetros de la sesión si es necesario
    update_session_params(sesion_activa, role=role, warehouse=warehouse, database=database, schema=schema)

    # Verificar si se debe crear la tabla desde cero
    if create_table:
        # Generar el script para crear la tabla
        create_table_sql = generate_create_table_script(nombre_tabla, df)

        try:
            # Ejecutar el script para crear la tabla en Snowflake
            sesion_activa.sql(create_table_sql).collect()
            mensajes.append(f"Tabla '{nombre_tabla}' creada exitosamente en Snowflake.")
        except Exception as e:
            mensajes.append(f"Error al crear la tabla '{nombre_tabla}': {e}")
            return mensajes
    else:
        mensajes.append(f"Realizando append de los datos a la tabla existente '{nombre_tabla}'.")

    # Calcular el tamaño recomendado de chunk basado en la memoria asignada
    memory_per_row = df.memory_usage(deep=True).sum() / len(df)
    memory_allocated = ram_gb * 1024 ** 3  # RAM asignada en bytes
    chunk_size_recomendado = int(memory_allocated // memory_per_row)

    # Cargar el DataFrame a Snowflake
    try:
        start_time = time.time()

        # Escribir el DataFrame a Snowflake usando write_pandas
        snowpark_df = sesion_activa.write_pandas(
            df=df, 
            table_name=nombre_tabla, 
            quote_identifiers=False, 
            chunk_size=chunk_size_recomendado, 
            database=database, 
            schema=schema, 
            auto_create_table=False,  # No se crea automáticamente
            overwrite=overwrite        # Permite overwrite si se desea
        )

        end_time = time.time()

        # Confirmar que el proceso fue exitoso
        if snowpark_df:
            mensajes.append(f"DataFrame cargado exitosamente en la tabla '{nombre_tabla}'.")
            mensajes.append(f"Tiempo de carga: {end_time - start_time:.2f} segundos.")
        else:
            mensajes.append(f"Error al cargar el DataFrame en la tabla '{nombre_tabla}'.")
    except Exception as e:
        mensajes.append(f"Se produjo un error durante la carga: {e}")

    finally:
        mensajes.append("Proceso terminado.")
    
    return mensajes