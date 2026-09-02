# Validación · Tejido Empresarial React 3.1.0

Fecha: 2 de septiembre de 2026. Entorno: Windows 11, Python 3.10.5 (venv), Node 22.23.2 (portable), Chrome headless para capturas.

## Comprobaciones ejecutadas

| Área | Resultado |
|---|---|
| `pytest -q` | 17 pruebas aprobadas: API en modo demo (metadatos, filtros dependientes, búsqueda por filtros/razón social/NIT/lote, ficha por NIT, glosario, exportación, SPA, rutas desconocidas, filtros no permitidos), generación SQL (listas blancas, escape, paginación, NIT sólo dígitos), Excel (estructura de hojas, paneles congelados, autofiltro, identificadores como texto, secciones de la ficha, estados del diccionario, nombres de archivo, neutralización de fórmulas). |
| `python -m compileall backend scripts` | Sin errores. |
| `tsc -b` + `vite build` | Sin errores de tipos; bundle principal 266 kB (84 kB gzip) más páginas cargadas bajo demanda. |
| Servidor real (uvicorn, `APP_DEMO_MODE=true`) | `/api/health`, `/api/metadata`, búsquedas, ficha, glosario y exportación responden correctamente; SPA servida desde FastAPI con cabeceras de seguridad. |
| Recorrido en navegador (1440 px) | Portada con animación, consulta (4 modos), filtros dependientes verificados en vivo (Antioquia → Itagüí, Medellín, Rionegro), resultados con tabla, orden, columnas y paginación, ficha de empresa, glosario, metodología. Sin errores de consola. |
| Recorrido en navegador (375–390 px) | Encabezado con menú, portada, modos en dos columnas, resultados en tarjetas, ficha en una columna, botón flotante de filtros. Sin desbordamiento horizontal. |
| Excel generado | Revisado con openpyxl y vista HTML: hojas `Resumen`, `Ficha_Empresa` (una empresa), `Vista_Principal` (paneles C7, autofiltro), `Datos_Completos` (paneles D7), `Diccionario` (63 definiciones validadas/complementarias; columnas ajenas al glosario marcadas como pendientes). |
| Archivos de salida suministrados | Los tres libros originales fueron regenerados con el nuevo formato en `salidas-ejemplo-formateadas/` mediante `scripts/reformatear_excel.py`. |

## Capturas

Carpeta `previews/` del paquete de entrega: portada (escritorio y móvil), consulta, resultados, búsqueda por razón social, lote de NIT, ficha de empresa, glosario, metodología y vistas previas de los Excel.

## Validaciones que requieren el entorno del propietario

- **Snowflake.** No se dispuso de credenciales en este entorno; la conexión, la rotación de llaves y las consultas se validaron por revisión estática y pruebas unitarias del SQL generado. Verifique en Railway con `/api/health?deep=true`.
- **Docker.** El equipo de validación no tiene Docker Engine; la imagen no se construyó localmente. El `Dockerfile` fue revisado paso a paso (npm ci + build, pip install, usuario sin privilegios, health check) y la compilación del frontend que alimenta la imagen se ejecutó con éxito.
- **Descarga en navegador real.** El flujo de descarga (blob → archivo) se verificó a nivel de API y de código; confirme en el navegador institucional que el archivo se guarda con el nombre esperado.

## Decisiones de esta versión

- Acceso abierto por defecto, como la versión Streamlit; HTTP Basic opcional.
- Campos de contacto incluidos por defecto en la descarga, como la versión Streamlit; excluibles por variable.
- Dos rangos derivados sin definición en el glosario institucional se documentan como «definición complementaria del aplicativo».
