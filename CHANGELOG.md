# Registro de cambios

Todas las versiones relevantes de **Tejido Empresarial · ProColombia**.
Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · Versionado: [SemVer](https://semver.org/lang/es/).

Para un aplicativo de este tipo: **PATCH** corrige textos, estilos o errores; **MINOR** agrega funciones o secciones compatibles; **MAJOR** cambia la arquitectura o el contrato de datos.

---

## [3.3.0] — 2026-09-02

### Agregado
- **Página «Estado del aplicativo» (`/estado`)**: dice en una frase si el aplicativo consulta datos reales o de demostración, con una pastilla de color en el encabezado visible desde cualquier página (en móvil, un punto de color junto al menú). Al abrirse comprueba la conexión sola, así que da un veredicto sin que nadie pulse nada. Incluye botones para volver a probar y para ver el diagnóstico paso a paso, el detalle del servicio (versión, origen configurado, última conexión correcta, conector, llave, variables faltantes) y las instrucciones concretas para Railway. Acepta `/estado?token=…` para ejecutar el diagnóstico automáticamente.
- **`/api/health` distingue «configurado» de «conectado»**: el servicio sólo afirma que está conectado después de que Snowflake haya respondido de verdad, y devuelve la marca de tiempo de esa última conexión correcta (`verified`, `verified_at`). Antes bastaba con tener las variables puestas para mostrarse en verde.
- **`/api/diagnostico`**: recorre paso a paso entorno → conector → llave → sesión → tablas y devuelve el error real de cada paso, sin exponer secretos, con una recomendación concreta para el primero que falla. En producción exige autenticación HTTP Basic o `APP_DIAG_TOKEN`.
- `/api/health` ahora informa si el conector está instalado, su versión, qué variables `SF_*` faltan y de dónde sale la llave.
- `DIAGNOSTICO_RAILWAY.md`: guía de verificación y solución de fallos de conexión en Railway.
- Variables `APP_DIAG_TOKEN` y `LOG_LEVEL`.
- Pruebas: 18 nuevas sobre normalización de llaves, reporte de configuración, estados del health y el endpoint de diagnóstico (35 en total).
- El build de validación del notebook de publicación instala `cryptography` y, si falla, imprime el final del registro con la causa exacta en lugar de un «Comando falló (1)» sin contexto.

### Corregido
- **La llave privada se normaliza antes de usarla.** Antes, un Base64 con un salto de línea o un espacio al final —lo más frecuente al pegar variables en Railway— hacía fallar la conexión con un mensaje genérico. Ahora se aceptan Base64 con espacios y saltos, PEM pegado directamente, Base64 de un PEM y archivos `.der`/`.p8`; si la llave está cifrada se descifra con la frase configurada y se entrega al conector en DER PKCS8.
- Los errores de conexión dejan de ser genéricos: el mensaje incluye la causa real reportada por Snowflake (sin secretos) y apunta a `/api/diagnostico`.
- Los registros del servicio se envían explícitamente a la salida estándar para que aparezcan en Railway.
- Los avisos de la interfaz usaban una caja flexible que separaba las palabras en negrita; ahora el texto fluye normalmente.
- El estado de la conexión se comparte con `useSyncExternalStore`: antes, si la página `/estado` llegaba por carga diferida en el momento justo, se quedaba indefinidamente en «Consultando el estado…» mientras el encabezado ya mostraba el resultado.
- El health profundo hace un solo intento (antes reintentaba tres veces con espera creciente y tardaba casi medio minuto en responder que no había conexión).
- Las pruebas se omiten con elegancia cuando el entorno no trae `cryptography` o el conector de Snowflake, en lugar de interrumpir toda la ejecución.

## [3.2.0] — 2026-09-02

### Agregado
- `notebooks/Demo_Efimera_TejidoEmpresarial.ipynb`: demostración efímera desde Google Colab (compila el frontend, levanta FastAPI y expone una URL temporal con TryCloudflare). Dos modos de datos: demostración sintética y Snowflake real, este último protegido con usuario y contraseña automáticos.
- `notebooks/Publicacion_GitHub_TejidoEmpresarial.ipynb`: publicación desde Google Drive a GitHub con validaciones, build de validación (frontend y backend), tag `vX.Y.Z` y verificación post-push.
- `.github/workflows/build.yml`: integración continua que ejecuta las pruebas del backend y compila el frontend en cada push y pull request.
- `CHANGELOG.md` (este archivo).

### Cambiado
- El conector de Snowflake se importa de forma tolerante: el modo demostración funciona en entornos donde `snowflake-snowpark-python` no está instalado (por ejemplo Colab con Python 3.12). En producción no cambia nada: `requirements-api.txt` lo instala y `/api/health` reporta el estado real.

## [3.1.0] — 2026-09-02

### Agregado
- Migración completa de la interfaz de Streamlit a **React 19 + TypeScript (Vite 8)** con el sistema de diseño de la familia digital ProColombia (azul noche, ámbar, Jost / Maven Pro / IBM Plex Mono).
- Portada institucional con animación del tejido empresarial convergiendo en los ejes de Exportaciones, Inversión y Turismo.
- Página de consulta con cuatro modos (segmentación, razón social, NIT, lote de NIT), 19 filtros dependientes agrupados con ayuda contextual y consulta compartible por URL.
- Resultados con orden por columna, búsqueda local, selector de columnas, paginación configurable y tarjetas en celular.
- Ficha de empresa (`/empresa/<NIT>`) con indicadores, gráfico de exportaciones por periodo y las 63 variables por secciones.
- Glosario navegable a partir del archivo institucional de variables y sección de metodología.
- Descarga Excel en un paso con hojas `Resumen`, `Ficha_Empresa`, `Vista_Principal`, `Datos_Completos` y `Diccionario`, con nombres descriptivos.
- API FastAPI (`/api/*`) que conserva la lógica de consulta a Snowflake, con auditoría en segundo plano y modo de demostración sintético.
- Imagen Docker única (Node 22 compila, Python 3.11 sirve) y configuración de Railway con health check.
- Documentación: `README.md`, `GUIA_TRANSFERENCIA.md`, `MIGRACION_REACT.md`, `VALIDACION.md` y utilidades en `scripts/`.

### Conservado
- Código Streamlit original íntegro en `legado_streamlit/`, fuera del despliegue.
- Alias, tablas, orden y semántica de las consultas del aplicativo original.
