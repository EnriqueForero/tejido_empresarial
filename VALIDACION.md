# Validación · Tejido Empresarial React 3.3.0

Fecha: 2 de septiembre de 2026. Entorno: Windows 11, Python 3.10.5 (venv), Node 22.23.2 (portable), Chrome headless para capturas.

## Comprobaciones ejecutadas

| Área | Resultado |
|---|---|
| `pytest -q` | 35 pruebas aprobadas: API en modo demo (metadatos, filtros dependientes, búsqueda por filtros/razón social/NIT/lote, ficha por NIT, glosario, exportación, SPA, rutas desconocidas, filtros no permitidos), generación SQL (listas blancas, escape, paginación, NIT sólo dígitos), Excel (estructura de hojas, paneles congelados, autofiltro, identificadores como texto, secciones de la ficha, estados del diccionario, nombres de archivo, neutralización de fórmulas). |
| `python -m compileall backend scripts` | Sin errores. |
| `tsc -b` + `vite build` | Sin errores de tipos; bundle principal 266 kB (84 kB gzip) más páginas cargadas bajo demanda. |
| Servidor real (uvicorn, `APP_DEMO_MODE=true`) | `/api/health`, `/api/metadata`, búsquedas, ficha, glosario y exportación responden correctamente; SPA servida desde FastAPI con cabeceras de seguridad. |
| Recorrido en navegador (1440 px) | Portada con animación, consulta (4 modos), filtros dependientes verificados en vivo (Antioquia → Itagüí, Medellín, Rionegro), resultados con tabla, orden, columnas y paginación, ficha de empresa, glosario, metodología. Sin errores de consola. |
| Recorrido en navegador (375–390 px) | Encabezado con menú, portada, modos en dos columnas, resultados en tarjetas, ficha en una columna, botón flotante de filtros. Sin desbordamiento horizontal. |
| Excel generado | Revisado con openpyxl y vista HTML: hojas `Resumen`, `Ficha_Empresa` (una empresa), `Vista_Principal` (paneles C7, autofiltro), `Datos_Completos` (paneles D7), `Diccionario` (63 definiciones validadas/complementarias; columnas ajenas al glosario marcadas como pendientes). |
| Archivos de salida suministrados | Los tres libros originales fueron regenerados con el nuevo formato en `salidas-ejemplo-formateadas/` mediante `scripts/reformatear_excel.py`. |
| Notebook de demo efímera | Ejecutada su lógica fuera de Colab: localización del proyecto por marcadores, preparación del entorno con contraseña generada, arranque de la API, verificación de `/api/health` y de la portada, prueba de humo (metadatos, búsqueda, ficha, Excel de 25 kB, glosario), bloqueo con HTTP 401 sin credenciales y apagado limpio. |
| Normalización de la llave privada | 10 pruebas con una llave RSA generada al vuelo: Base64 de DER con espacios y saltos de línea, DER cifrado con la frase correcta, DER cifrado sin frase y con frase equivocada (mensajes claros), PEM pegado directamente, Base64 de un PEM, valor que no es Base64, y redacción de secretos en los mensajes. |
| Endpoint `/api/diagnostico` | 5 pruebas: cerrado con 403 en un despliegue sin protección, abierto con `APP_DIAG_TOKEN` correcto y cerrado con uno incorrecto, abierto con HTTP Basic, señalamiento del paso `llave_1` cuando el valor no sirve, y `/api/health` reportando las variables faltantes sin exponer valores. |
| Diagnóstico contra una conexión real que falla | Ejecutado con una cuenta inexistente y una llave válida: los pasos `entorno`, `conector` y `llave_1` pasan, `sesion` falla con el código real de Snowflake (290404) y el conjunto responde en 10 segundos. |
| Página `/estado` en modo demostración | Insignia azul «Modo demostración» en el encabezado, tarjeta con la explicación, tres pasos para salir del modo demostración y detalle del servicio con los campos marcados «No aplica en modo demostración». |
| Página `/estado` con Snowflake mal configurado | Al abrirla comprueba la conexión sola (sin pulsar nada) y en unos segundos pasa a «Conexión con problemas»; con `?token=…` ejecuta el diagnóstico y muestra `✓ Variables`, `✓ Conector`, `✓ Llave privada 1` y `✗ Sesión establecida con Snowflake` con el error real y la recomendación. El encabezado cambia a la insignia ámbar al mismo tiempo. |
| Estado honesto de la conexión | Con todas las variables presentes pero sin ninguna consulta hecha, `/api/health` responde `configured` y la interfaz dice «Sin verificar»; sólo después de que Snowflake responde pasa a `connected` y «Datos reales». Cubierto por dos pruebas automáticas. |
| Insignia en móvil (390 px) | Punto de color junto al botón de menú, enlazado a `/estado`; la página completa se lee sin desbordamiento horizontal (`scrollWidth` = `innerWidth` = 375). |
| Notebook de publicación | Ejecutada su lógica sin tocar GitHub: configuración, detección de ambigüedad entre dos copias del proyecto, sincronización de la versión en `frontend/package.json` y `backend/config.py`, disciplina de CHANGELOG, pre-flight (134 archivos · 2,9 MB), bloqueo de una llave `.der` y de un `.env`, detección de un token de GitHub incrustado, y los cuatro comandos de build reales (pip, pytest, `npm ci`, `npm run build`) en 92 s con limpieza posterior. |

## Capturas

Carpeta `previews/` del paquete de entrega: portada (escritorio y móvil), consulta, resultados, búsqueda por razón social, lote de NIT, ficha de empresa, glosario, metodología, vistas previas de los Excel y las tres vistas nuevas de la página de estado (modo demostración, diagnóstico paso a paso y versión móvil).

## Validaciones que requieren el entorno del propietario

- **Snowflake.** No se dispuso de credenciales en este entorno; la conexión, la rotación de llaves y las consultas se validaron por revisión estática y pruebas unitarias del SQL generado. Verifique en Railway abriendo `/estado`: la página hace la prueba sola y dice si el aplicativo quedó conectado.
- **Docker.** El equipo de validación no tiene Docker Engine; la imagen no se construyó localmente. El `Dockerfile` fue revisado paso a paso (npm ci + build, pip install, usuario sin privilegios, health check) y la compilación del frontend que alimenta la imagen se ejecutó con éxito.
- **Descarga en navegador real.** El flujo de descarga (blob → archivo) se verificó a nivel de API y de código; confirme en el navegador institucional que el archivo se guarda con el nombre esperado.

## Lo que no se pudo probar de los notebooks

- La ejecución **dentro de Colab** (montaje de Drive, instalación de Node por
  `apt-get`, túnel de TryCloudflare y lectura de secretos) requiere el entorno
  de Colab; se validó toda la lógica que no depende de él.
- El **push real a GitHub** requiere el `GITHUB_TOKEN`. La celda
  `diagnosticar_token()` está incluida precisamente para separar las causas de
  un fallo de credenciales antes de publicar.

## Decisiones de esta versión

- Acceso abierto por defecto, como la versión Streamlit; HTTP Basic opcional.
- Campos de contacto incluidos por defecto en la descarga, como la versión Streamlit; excluibles por variable.
- Dos rangos derivados sin definición en el glosario institucional se documentan como «definición complementaria del aplicativo».
