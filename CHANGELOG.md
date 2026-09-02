# Registro de cambios

Todas las versiones relevantes de **Tejido Empresarial · ProColombia**.
Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · Versionado: [SemVer](https://semver.org/lang/es/).

Para un aplicativo de este tipo: **PATCH** corrige textos, estilos o errores; **MINOR** agrega funciones o secciones compatibles; **MAJOR** cambia la arquitectura o el contrato de datos.

---

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
