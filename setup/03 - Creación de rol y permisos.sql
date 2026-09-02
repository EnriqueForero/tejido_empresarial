-- ===========================================
-- Configuración y asignación de roles y permisos para Aplicación de Segmentación de Exportaciones
-- ===========================================

-- 1. Establecer el rol de seguridad para poder administrar roles
USE ROLE SECURITYADMIN;  
-- Se utiliza el rol SECURITYADMIN, que tiene privilegios para gestionar la seguridad y roles en Snowflake.

-- 2. Seleccionar el Warehouse adecuado para la ejecución de las consultas
USE WAREHOUSE WH_PROCOLOMBIA_ANALITICA;  
-- Se selecciona el warehouse WH_PROCOLOMBIA_ANALITICA para procesar las operaciones.

-- ======================================================
-- Creación del rol APP_SEGMENTACION_EXPORTACIONES para la Aplicación
-- ======================================================
-- Se crea (o reemplaza, si ya existe) el rol APP_SEGMENTACION_EXPORTACIONES, asignándole un comentario descriptivo.
CREATE OR REPLACE ROLE "APP_SEGMENTACION_EXPORTACIONES" 
    COMMENT = "Este es un rol creado para la aplicación de Segmentación de Exportaciones de Analítica, tiene permisos de lectura a todas las tablas y vistas de APP_SEGMENTACION_EXPORTACIONES y puede insertar datos a la tabla de seguimiento";

-- ======================================================
-- Definición de la jerarquía de roles
-- ======================================================
-- Se asigna el rol APP_SEGMENTACION_EXPORTACIONES al rol SYSADMIN para integrarlo correctamente en el árbol de permisos.
GRANT ROLE APP_SEGMENTACION_EXPORTACIONES TO ROLE "SYSADMIN";
-- Se asigna el rol APPS_MANAGER al rol APP_SEGMENTACION_EXPORTACIONES para incluirlo en la jerarquía de roles de aplicaciones.
GRANT ROLE APPS_MANAGER TO ROLE "APP_SEGMENTACION_EXPORTACIONES";

-- Se muestra la lista de roles para verificar la creación y asignación del rol APP_SEGMENTACION_EXPORTACIONES.
SHOW ROLES;

-- ======================================================
-- Cambio de rol para asignar permisos a nivel de base de datos
-- ======================================================
-- Se cambia el rol actual a ACCOUNTADMIN, rol con máximos privilegios administrativos en Snowflake.
USE ROLE ACCOUNTADMIN;

-- Seleccionar la base de datos donde se encuentran los objetos a los que se asignarán permisos.
USE DATABASE APP_SEGMENTACION_EXPORTACIONES;

-- ======================================================
-- Otorgamiento de permisos de lectura (SELECT) para cada objeto y vista específica
-- ======================================================
-- Permisos sobre la base de datos:
GRANT USAGE ON DATABASE APP_SEGMENTACION_EXPORTACIONES TO ROLE APP_SEGMENTACION_EXPORTACIONES;
-- Se otorga el permiso de USAGE sobre la base de datos APP_SEGMENTACION_EXPORTACIONES para que el rol pueda acceder a ella.

-- Permisos sobre todos los esquemas:
GRANT USAGE ON ALL SCHEMAS IN DATABASE APP_SEGMENTACION_EXPORTACIONES TO ROLE APP_SEGMENTACION_EXPORTACIONES;
-- Permite al rol APP_SEGMENTACION_EXPORTACIONES utilizar todos los esquemas dentro de la base de datos APP_SEGMENTACION_EXPORTACIONES.

-- PUBLIC:
-- Se conceden permisos de SELECT en todas y futuras tablas del esquema PUBLIC.
GRANT SELECT ON FUTURE TABLES IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.PUBLIC TO ROLE APP_SEGMENTACION_EXPORTACIONES;
GRANT SELECT ON ALL TABLES IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.PUBLIC TO ROLE APP_SEGMENTACION_EXPORTACIONES;

-- SEGMENTACION:
-- Se otorgan permisos de SELECT en todas y futuras tablas del esquema SEGMENTACION.
GRANT SELECT ON FUTURE TABLES IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION TO ROLE APP_SEGMENTACION_EXPORTACIONES;
GRANT SELECT ON ALL TABLES IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION TO ROLE APP_SEGMENTACION_EXPORTACIONES;

-- SEGUIMIENTO:
-- Se otorgan permisos de SELECT en todas y futuras tablas del esquema SEGUIMIENTO.
GRANT SELECT ON FUTURE TABLES IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO TO ROLE APP_SEGMENTACION_EXPORTACIONES;
GRANT SELECT ON ALL TABLES IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO TO ROLE APP_SEGMENTACION_EXPORTACIONES;

-- Permitir el acceso a futuras vistas creadas a todos los esquemas.
GRANT SELECT ON FUTURE VIEWS IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.PUBLIC TO ROLE APP_SEGMENTACION_EXPORTACIONES;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION TO ROLE APP_SEGMENTACION_EXPORTACIONES;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO TO ROLE APP_SEGMENTACION_EXPORTACIONES;

-- ======================================================
-- Otorgamiento de permisos de escritura en la tabla de seguimiento
-- ======================================================
-- Se concede al rol APP_SEGMENTACION_EXPORTACIONES los permisos de SELECT, INSERT, UPDATE y DELETE sobre la tabla de seguimiento.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO.EVENTOS TO ROLE APP_SEGMENTACION_EXPORTACIONES;

-- ======================================================
-- Verificación de permisos asignados al rol APP_SEGMENTACION_EXPORTACIONES
-- ======================================================
-- Se muestran todos los permisos (grants) asignados al rol APP_SEGMENTACION_EXPORTACIONES para confirmar que la configuración es correcta.
SHOW GRANTS TO ROLE APP_SEGMENTACION_EXPORTACIONES;

-- ======================================================
-- Asignación del rol APP_SEGMENTACION_EXPORTACIONES a un usuario de servicio
-- ======================================================
-- Se otorga el rol APP_SEGMENTACION_EXPORTACIONES al usuario USER_SERVICE_ANALITICA, permitiéndole acceder a los permisos definidos.
GRANT ROLE APP_SEGMENTACION_EXPORTACIONES TO USER USER_SERVICE_ANALITICA;