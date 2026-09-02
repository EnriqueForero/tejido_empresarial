# Migración de Streamlit a React · notas técnicas

## Resultado

- El runtime de producción ya no ejecuta Streamlit. Railway construye el frontend React con Node 22 y ejecuta FastAPI (uvicorn) como único proceso en el puerto que asigna la plataforma.
- La capa de datos se mantuvo en Python y Snowflake. Los cambios de backend se limitaron a lo necesario para que la interfaz React funcione: exponer las operaciones por HTTP, validar solicitudes, paginar la vista previa, generar el Excel formateado, entregar la ficha por NIT y servir el frontend compilado.
- El código Streamlit original se conserva íntegro en `legado_streamlit/` para trazabilidad y consulta.

## Equivalencia funcional

| Streamlit (original) | React (esta versión) |
|---|---|
| Portada con «Descripción», «Beneficios» y «Alcance y límites» en tarjetas | Portada animada (tejido → tres ejes) y las mismas tres secciones como pestañas accesibles; cifras del aplicativo; fuentes y cortes. |
| Página «Tejido Empresarial de Colombia» con radio de cuatro vistas | Página «Consultar» con cuatro modos (segmentar, razón social, NIT, lote de NIT) en una barra segmentada; la URL refleja la consulta. |
| 13 filtros generales en 4 columnas (`DynamicFilters`) y 6 filtros de exportación | 19 filtros agrupados en 6 grupos, dependientes entre sí, con búsqueda dentro de cada lista, ayuda contextual (notas metodológicas del original), fichas de selección y cajón lateral en celular. |
| Botones «Buscar», «Preparar descarga» y «Reiniciar» | Un solo botón «Buscar»; la descarga es un paso directo; «Limpiar todo» reinicia criterios sin perder el modo. |
| Vista previa de 10 filas con 12 columnas (`st.dataframe`) | Vista previa paginada (25/50/100) con 15 variables clave, orden por columna, búsqueda local, selector de columnas, columnas fijas; tarjetas en celular. |
| Sin ficha individual | Ficha completa por NIT (`/empresa/<NIT>`): indicadores, gráfico de exportaciones por periodo y 63 variables por secciones; descarga individual. |
| Excel plano `Resultados Segmentación de Empresas.xlsx` (una hoja, sin formato) | Libro con `Resumen`, `Ficha_Empresa` (una empresa), `Vista_Principal`, `Datos_Completos` y `Diccionario`; nombre descriptivo con tipo de consulta, criterio, fecha y número de empresas. |
| Glosario como enlace a OneDrive | Sección «Glosario» navegable (búsqueda, secciones, fuentes, uso) con descarga del archivo original; el mismo diccionario acompaña cada Excel. |
| Metodología como descarga `.docx` | Sección «Metodología» (propósito, fuentes y cortes, definiciones clave, alcance y límites, transferencia) más descarga del documento. |
| Bootstrap por CDN, tema gris `#646464` | Sistema de diseño ProColombia digital (Célula de IA · GIC): azul noche, ámbar, Jost / Maven Pro / IBM Plex Mono, tipografías empaquetadas sin CDN, logos MinCIT · ProColombia. |
| Registro de eventos en `SEGUIMIENTO.EVENTOS` | Igual, en segundo plano (no bloquea la respuesta). |
| Sesión Snowflake por proceso con llaves RSA y rotación | Igual (`backend/database.py`), con reintentos y reconexión ante errores. |

Las páginas Empresas, Destinos, Valor Agregado y Territorios estaban deshabilitadas en la navegación del original (`app.py` sólo redirige a Segmentación) y permanecen en `legado_streamlit/pages/` sin cambios.

## Contrato de datos

- Las 63 columnas exportadas conservan los alias legibles del aplicativo original (`QUERY_COLUMNS`).
- Los filtros generales consultan `TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P`; los de exportación restringen NIT mediante `PUBLIC.BIENES_Y_SERVICIOS_P`, como el original.
- Los resultados se ordenan por ingresos operacionales descendentes, como el original.
- Los campos de contacto se incluyen por defecto (como el original); `EXPORT_INCLUDE_CONTACT_FIELDS=false` los retira.
- Los parámetros de periodo viven en `backend/config.py`, con la misma convención de comentarios «REEMPLAZAR cuando haya nuevo mes» de `legado_streamlit/src/pages_utils/config.py`.

## Decisiones

1. **Un solo servicio.** FastAPI sirve la API y el frontend compilado; no hay CDN ni segundo servicio en Railway.
2. **npm en lugar de pnpm.** `package-lock.json` y `npm ci` evitan depender de corepack en la imagen.
3. **Acceso abierto por defecto**, igual que el original, con opción de HTTP Basic para dominios públicos.
4. **Modo demostración** (`APP_DEMO_MODE=true`) con datos sintéticos para probar la experiencia completa sin Snowflake.
5. **Definiciones complementarias** para los dos rangos derivados que el glosario institucional no describe; se marcan explícitamente y no se presentan como definiciones institucionales.
