# DML significa Data Manipulation Language o Lenguaje de Manipulación de Datos, en español. 
# Este lenguaje permite realizar diferentes acciones a los datos que se encuentran en una base de datos.
# Permite recuperar, almacenar, modificar, eliminar, insertar y actualizar datos de una base de datos.
# Elementos del DML (Data Manipulation Language)
    # SELECT: Utilizado para consultar registros de la base de datos que satisfagan un criterio determinado.
    # INSERT: Utilizado para cargar de datos en la base de datos en una única operación.
    # UPDATE: Utilizado para modificar los valores de los campos y registros especificados
    # DELETE: Utilizado para eliminar registros de una tabla de una base de datos.

# Librerías
import os
from snowflake.snowpark import Session
import pandas as pd

# Función para insertar datos en la tabla de auditoria
def registrar_evento_auditoria(sesion_activa, nombre_esquema_destino, nombre_tabla, numero_registros, mensaje):
    """
    Registra un evento en la base de datos Snowflake en la tabla de auditoría.

    Args:
    - sesion_activa: Objeto de sesión activa de conexión a Snowflake.
    - nombre_esquema_destino (str): Nombre del esquema de destino.
    - nombre_tabla (str): Nombre de la tabla de destino.
    - numero_registros (int): Número de registros cargados en la tabla.
    - mensaje (str): Mensaje de carga de Snowflake. 

    Raises:
    - Exception: Si ocurre algún error al ejecutar la consulta SQL.
    """
    try:
        # Eliminar comillas simples en el mensaje para evitar errores SQL
        mensaje = mensaje.replace("'", "")

        # Obtener el próximo ID llamando al procedimiento almacenado
        resultado_id = sesion_activa.sql("CALL SEGUIMIENTO.GET_NEXT_ID();").collect()

        # Extraer el valor del ID del resultado
        id_auditoria = resultado_id[0][0]  # Asumiendo que el ID es el primer valor en el resultado

        # Crear consulta SQL con valores directos en el INSERT
        query_insert = f"""
        INSERT INTO APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO.AUDITORIA_CARGUES (
            ID_AUDITORIA,
            NOMBRE_ESQUEMA_DESTINO, 
            NOMBRE_TABLA, 
            FECHA_CARGUE, 
            NUMERO_REGISTROS,
            MENSAJE
        ) 
        VALUES (
            {id_auditoria},
            '{nombre_esquema_destino}', 
            '{nombre_tabla}', 
            CONVERT_TIMEZONE('America/Los_Angeles', 'America/Bogota', CURRENT_TIMESTAMP), 
            {numero_registros},
            '{mensaje}'
        );
        """
        
        # Ejecutar la consulta SQL
        sesion_activa.sql(query_insert).collect()
        
        print("Evento de auditoría registrado con éxito.")
    
    except Exception as e:
        print(f"Error al registrar el evento de auditoría: {e}")
        raise  # Re-lanzar la excepción para manejo adicional si es necesario

def ejecutar_consulta_segura(query, session):
    """
    Ejecuta una consulta SQL sobre una tabla específica y devuelve los resultados como un DataFrame.
    Si la consulta no devuelve datos, retorna un DataFrame vacío.

    Parámetros:
    - query (str): Consulta SQL a ejecutar.
    - session: Objeto de conexión activo a Snowflake.

    Retorna:
    - DataFrame con los resultados de la consulta si tiene datos.
    - DataFrame vacío si no hay resultados.
    
    Excepciones:
    - Exception: Si ocurre un error durante la ejecución de la consulta.
    """
    try:
        # Ejecutar la consulta y recoger resultados
        resultados = session.sql(query).collect()

        # Verificar si hay datos en los resultados
        if resultados:
            # Convertir a DataFrame
            df = pd.DataFrame(resultados)
        else:
            # Si no hay resultados, devolver un DataFrame vacío
            df = pd.DataFrame()
        
        return df
    except Exception as e:
        # Manejo de errores en la ejecución de la consulta
        raise Exception(f"Error al ejecutar la consulta: {str(e)}")

def ejecutar_multiples_consultas(consultas, session, pais_seleccionado=None):
    """
    Ejecuta múltiples consultas SQL y almacena los resultados en un diccionario.
    Si una consulta no devuelve datos, guarda un DataFrame vacío en su lugar.

    Parámetros:
    - consultas (dict): Diccionario donde las claves son nombres descriptivos de las consultas 
                        y los valores son las consultas SQL a ejecutar.
    - session: Objeto de conexión activo a Snowflake.
    - pais_seleccionado (str, opcional): Nombre del país seleccionado, para usar como contexto en mensajes.

    Retorna:
    - dict: Diccionario donde las claves son los nombres de las consultas y los valores son DataFrames con los resultados.
    """
    # Inicializar el objeto para almacenar los resultados
    resultados = {}

    # Ejecutar cada consulta y almacenar los resultados
    for nombre_tabla, query in consultas.items():
        try:
            print(f"Ejecutando consulta para {nombre_tabla}...")
            
            # Usar la función robusta para ejecutar la consulta
            df_resultado = ejecutar_consulta_segura(query, session)
            
            if df_resultado.empty:
                print(f"No se encontraron datos en {nombre_tabla}" + 
                      (f" para el país: {pais_seleccionado}" if pais_seleccionado else "."))
            else:
                print(f"Datos obtenidos de {nombre_tabla}" + 
                      (f" para {pais_seleccionado}: {len(df_resultado)} filas." if pais_seleccionado else f": {len(df_resultado)} filas."))
            
            # Guardar los resultados en el diccionario
            resultados[nombre_tabla] = df_resultado
        except Exception as e:
            print(f"Error al ejecutar la consulta para {nombre_tabla}: {str(e)}")
            # Guardar un DataFrame vacío en caso de error
            resultados[nombre_tabla] = pd.DataFrame()

    return resultados
