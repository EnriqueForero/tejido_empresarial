# Guía de transferencia · Tejido Empresarial (React + FastAPI en Railway)

Objetivo: que cualquier persona del equipo pueda desplegar, operar y actualizar el aplicativo sin conocimiento previo del proyecto. Tiempo estimado del primer despliegue: 20 minutos.

## 1. Qué recibe

```text
tejido-empresarial-react/
├── backend/               API FastAPI (Python) · consultas Snowflake · Excel · glosario
│   ├── config.py          ← único archivo que se edita cuando cambian los cortes de información
│   └── resources/         glosario .xlsx y metodología .docx (reemplazables)
├── frontend/              Interfaz React + TypeScript (Vite)
├── scripts/               utilidades: reformatear Excel plano, vista previa de libros
├── tests/                 pruebas automáticas del backend (pytest)
├── notebooks/             demo efímera en Colab y publicación a GitHub
├── DIAGNOSTICO_RAILWAY.md diagnóstico cuando el aplicativo no consulta datos
├── setup/                 cuadernos de creación/carga de la base (sin cambios)
├── legado_streamlit/      aplicativo Streamlit original, íntegro, sólo como referencia
├── Dockerfile             imagen única: compila React y ejecuta FastAPI
├── railway.toml           configuración de Railway (builder Dockerfile, health check)
├── .env.example           todas las variables documentadas
└── README.md              documentación técnica completa
```

## 2. Camino recomendado: Drive → Colab → GitHub → Railway

Si trabaja desde Google Drive, los dos cuadernos de `notebooks/` automatizan el
ciclo completo y son la vía probada:

1. **Revisar antes de publicar** — `Demo_Efimera_TejidoEmpresarial.ipynb`:
   compila el frontend, levanta la API y entrega una URL pública temporal.
   Empiece con `MODO_DATOS="demo"`; para la validación final use
   `MODO_DATOS="snowflake"` con los secretos `SF_*` en Colab (la URL queda
   protegida con contraseña automáticamente).
2. **Publicar** — `Publicacion_GitHub_TejidoEmpresarial.ipynb`: valida la
   estructura, bloquea llaves y secretos, corre las pruebas del backend,
   compila el frontend, hace `commit`, `push` y `tag vX.Y.Z`, y verifica que el
   SHA remoto coincida.
3. **Desplegar** — Railway, conectado al repositorio, redespliega en cada push.

Antes de publicar por primera vez: repositorio creado y vacío en GitHub, y el
secreto `GITHUB_TOKEN` cargado en Colab (🔑 Secretos, con acceso del cuaderno).
Suba la versión en la Celda A y registre los cambios en `CHANGELOG.md`: el
notebook aborta si el tag ya existe o si el CHANGELOG no menciona la versión.

## 3. Despliegue en Railway (primera vez, sin Colab)

1. **Repositorio.** Suba la carpeta a un repositorio Git privado. No incluya `.env`, `*.der` ni `node_modules` (ya están en `.gitignore`).
2. **Servicio.** En Railway: *New Project → Deploy from GitHub repo*. Railway detecta `railway.toml` y usa el `Dockerfile`.
3. **Variables.** En *Variables* del servicio, pegue:
   - `SF_ACCOUNT`, `SF_USER`, `SF_DATABASE`, `SF_SCHEMA`, `SF_WAREHOUSE`, `SF_ROLE` (los mismos de la versión Streamlit).
   - `SF_PRIVATE_KEY_B64_1` con la llave RSA en Base64 (PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("rsa_key_1.der"))`). Si la llave tiene frase, `SF_PRIVATE_KEY_PASSPHRASE_1`.
   - Opcional: `SF_PRIVATE_KEY_B64_2` (respaldo), `PUBLIC_ORIGIN` (URL pública), `APP_BASIC_USER` + `APP_BASIC_PASSWORD` (protege todo el aplicativo con usuario y contraseña).
4. **Dominio.** *Settings → Networking → Generate Domain* (o dominio propio).
5. **Verificación.** Abra `https://SU-DOMINIO/estado`. La página comprueba la conexión sola y responde con una de cuatro
   frases: *Datos reales*, *Modo demostración*, *Conexión con problemas* o *Sin conexión a datos*. Si no es *Datos reales*,
   ahí mismo indica qué corregir en Railway. Después abra la portada, haga una búsqueda por razón social y descargue un Excel.

Cuando el estado no sea *Datos reales*, pulse **«Ver diagnóstico detallado»**: recorre entorno → conector → llave → sesión →
tablas y señala el paso exacto que falla con el mensaje real de Snowflake. El procedimiento completo, escrito paso a paso para
alguien sin experiencia en despliegues, está en [`DIAGNOSTICO_RAILWAY.md`](DIAGNOSTICO_RAILWAY.md).

Para quien prefiera las direcciones técnicas: `/api/health` (estado rápido), `/api/health?deep=true` (prueba real contra
Snowflake) y `/api/diagnostico` (paso a paso, protegido con HTTP Basic o `APP_DIAG_TOKEN`).

## 4. Operación diaria

- **Acceso.** Igual que el original, el aplicativo es abierto salvo que configure `APP_BASIC_USER` y `APP_BASIC_PASSWORD`. Recomendado para dominios públicos, porque la descarga incluye datos de contacto.
- **Límites.** Vista previa hasta 10.000 empresas navegables; descarga hasta `EXPORT_MAX_ROWS` (5.000 por defecto). Si un segmento supera el límite, la interfaz pide refinar filtros.
- **Auditoría.** Búsquedas, fichas y descargas se registran en `APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO.EVENTOS` en segundo plano (como antes).
- **Rendimiento.** Las tablas de filtros se cargan una vez por proceso y se reutilizan; las consultas de vista previa piden sólo 15 columnas y paginan en Snowflake.

## 5. Actualizar cortes de información (mensual / anual)

Edite `backend/config.py`:

1. **PASO 1** · `EXPORTACIONES_ANIOS_DISPONIBLES = (2021, "Enero a Junio 2026")`, `RUES_CORTE`, `SUPERSOCIEDADES_ANIO`, `GLOSARIO_FECHA`.
2. **PASO 2** · En `EXPORT_VALUE_COLUMNS`, reemplace la entrada del corrido anterior por la nueva (por ejemplo `EXPO_ENE_JUN_2026` → `Exportaciones totales de la empresa Enero - Junio 2026 (FOB USD)`). Al cerrar el año, elimine el corrido y agregue `EXPO_2026`.
3. Si el glosario cambió, reemplace `backend/resources/2026_09_01_Glosario_variables_Aplicativo.xlsx` y ajuste `GLOSSARY_PATH` en `backend/glossary.py` si el nombre cambia.
4. Ejecute `pytest -q` y vuelva a desplegar (push al repositorio).

Etiquetas de filtros, metadatos de la portada, hoja `Resumen` del Excel y el diccionario se actualizan solos.

## 6. Cambios de interfaz

- Textos institucionales de la portada: `frontend/src/paginas/Inicio.tsx`.
- Colores y tipografías: `frontend/src/estilos/base.css` (variables `:root`).
- Logos: `frontend/src/assets/logos/` (lockup MinCIT · ProColombia).
- Agrupación y ayuda de filtros: `backend/config.py` (`GENERAL_FILTERS`, `EXPORT_FILTERS`, `help`).
- Columnas de la vista previa: `PREVIEW_COLUMNS` en `backend/config.py`.

Tras cualquier cambio: `cd frontend && npm run build` (o simplemente desplegar; Docker compila).

## 7. Lista de verificación de entrega

- [ ] `pytest -q` → 35 pruebas aprobadas.
- [ ] `cd frontend && npm run build` sin errores.
- [ ] `/estado` en Railway muestra «Datos reales».
- [ ] Búsqueda por filtros con opciones dependientes (elegir departamento reduce municipios).
- [ ] Búsqueda por razón social, NIT y lote de NIT.
- [ ] Ficha de empresa abre desde la tabla y desde la URL `/empresa/<NIT>`.
- [ ] Descarga Excel: hojas `Resumen`, `Vista_Principal`, `Datos_Completos`, `Diccionario` (y `Ficha_Empresa` para una empresa).
- [ ] Vista en celular: menú, cajón de filtros y tarjetas de resultados.
- [ ] (Con Colab) La demo efímera abre y la publicación termina con el SHA verificado.

## 8. Soporte

Documentación técnica: `README.md`. Cuadernos: `notebooks/`. Validación realizada: `VALIDACION.md`. Notas de migración desde Streamlit: `MIGRACION_REACT.md`. Código original: `legado_streamlit/`.
