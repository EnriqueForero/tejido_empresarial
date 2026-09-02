# Tejido Empresarial · ProColombia

Aplicativo web para identificar, segmentar y comprender el tejido empresarial colombiano en apoyo a los ejes de **Exportaciones, Inversión y Turismo** de ProColombia (Gerencia de Inteligencia Comercial).

Esta versión reemplaza la interfaz Streamlit por **React 19 + TypeScript (Vite 8)** y conserva la lógica de datos en **Python / FastAPI** con conexión a **Snowflake**. Un único contenedor Docker compila el frontend y sirve la API y la interfaz desde el mismo origen, listo para **Railway**.

## Qué incluye

| Área | Detalle |
|---|---|
| Portada | Animación institucional del tejido empresarial conectando los tres ejes; cifras del aplicativo; descripción, beneficios y alcance del original. |
| Consulta | Cuatro modos: segmentación con 19 filtros dependientes agrupados, razón social, NIT y lote de NIT (archivo o lista pegada). URL compartible por consulta. |
| Resultados | Vista previa legible (15 variables clave), orden por columna, búsqueda local, selector de columnas, 25/50/100 por página; tarjetas en celular. |
| Ficha de empresa | `/empresa/<NIT>`: indicadores, gráfico de exportaciones por periodo y las 63 variables agrupadas por secciones. |
| Descarga | Excel en un solo paso con hojas `Resumen`, `Ficha_Empresa` (una empresa), `Vista_Principal`, `Datos_Completos` y `Diccionario`; nombres descriptivos con fecha y criterio. |
| Glosario | Lectura estructurada del archivo institucional de variables con búsqueda, secciones, fuentes y uso en el aplicativo. Descarga del original. |
| Metodología | Fuentes y cortes, definiciones clave, alcance y límites, guía de transferencia. Descarga del documento metodológico. |
| Diseño | Sistema visual de la familia digital ProColombia (Célula de IA · GIC): azul noche `#011627`, ámbar `#FFA400`, Jost / Maven Pro / IBM Plex Mono, logos MinCIT · ProColombia, movimiento respetuoso de `prefers-reduced-motion`. |

## Arquitectura

```text
Navegador ──▶ React + TypeScript (frontend/)        páginas: Inicio · Consultar · Glosario · Metodología · Ficha
                 │  /api/*
                 ▼
             FastAPI (backend/)                      un proceso uvicorn sirve API + frontend compilado
                 ├── config.py      parámetros de periodo, filtros, columnas y secciones (ÚNICO archivo a editar por corte)
                 ├── queries.py     SQL parametrizado (misma lógica del original)
                 ├── database.py    sesión Snowflake con llaves RSA y rotación
                 ├── exporter.py    libro Excel profesional (xlsxwriter)
                 ├── glossary.py    lectura del glosario institucional
                 ├── demo.py        datos sintéticos (APP_DEMO_MODE=true)
                 └── resources/     glosario .xlsx y metodología .docx
```

El código Streamlit original se conserva íntegro en `legado_streamlit/` como referencia; no participa en el despliegue. Los cuadernos de creación de la base de datos siguen en `setup/`.

## Ejecución local

Requisitos: Node.js 20.19 o superior (recomendado 22), Python 3.11 (3.10 también funciona).

```bash
# 1. Frontend (terminal A)
cd frontend
npm ci
npm run dev            # http://localhost:5173 · redirige /api a http://127.0.0.1:8000

# 2. API (terminal B), en la raíz del repositorio
python -m venv .venv
.venv\Scripts\activate          # Windows   |   source .venv/bin/activate  (macOS/Linux)
pip install -r requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
```

Para probar toda la experiencia **sin Snowflake**, active el modo de demostración con datos sintéticos:

```bash
# PowerShell
$env:APP_DEMO_MODE="true"; uvicorn backend.main:app --reload --port 8000
# Bash
APP_DEMO_MODE=true uvicorn backend.main:app --reload --port 8000
```

Para servir el frontend compilado desde FastAPI (como en producción): `cd frontend && npm run build` y abra `http://127.0.0.1:8000`.

## Variables de entorno

Copie `.env.example` a `.env` sólo en desarrollo. En Railway configure las variables desde el panel del servicio.

| Variable | Obligatoria | Uso |
|---|:-:|---|
| `SF_ACCOUNT`, `SF_USER`, `SF_DATABASE`, `SF_SCHEMA`, `SF_WAREHOUSE`, `SF_ROLE` | Sí | Conexión a Snowflake (mismos valores que la versión Streamlit). |
| `SF_PRIVATE_KEY_B64_1` | Sí* | Llave RSA DER en Base64 (recomendada en Railway). |
| `SF_PRIVATE_KEY_PASSPHRASE_1` | No | Frase de la llave 1, si está cifrada. |
| `SF_PRIVATE_KEY_B64_2`, `SF_PRIVATE_KEY_PASSPHRASE_2` | No | Segunda llave para rotación/respaldo. |
| `SF_PRIVATE_KEY_PATH_1`, `SF_PRIVATE_KEY_PATH_2` | Sí* | Alternativa local: ruta al archivo `.der`. |
| `APP_ENV` | No | `production` (por defecto) o `development` (habilita `/api/docs`). |
| `APP_DEMO_MODE` | No | `true` sólo para demostración con datos sintéticos. |
| `PUBLIC_ORIGIN` | Recomendable | URL pública HTTPS para metadatos sociales. |
| `EXPORT_MAX_ROWS` | No | Máximo de empresas por Excel (por defecto 5.000; hasta 20.000). |
| `EXPORT_INCLUDE_CONTACT_FIELDS` | No | `true` por defecto (igual que Streamlit). `false` retira dirección, teléfono, correo y representante legal. |
| `MAX_REQUEST_BYTES` | No | Tamaño máximo del cuerpo HTTP (2 MB por defecto). |
| `APP_BASIC_USER`, `APP_BASIC_PASSWORD` | No | Si se configuran ambas, todo el aplicativo pide usuario y contraseña (HTTP Basic). Vacías = acceso abierto, como el original. |

\* Configure al menos una llave (Base64 o ruta). Conversión a Base64: PowerShell `[Convert]::ToBase64String([IO.File]::ReadAllBytes("rsa_key_1.der"))` · macOS/Linux `base64 -w 0 rsa_key_1.der`.

## Publicación y demostración desde Google Colab

La carpeta `notebooks/` trae dos cuadernos listos para usar con el proyecto en
Google Drive (`/content/drive/MyDrive/ProColombia/tejido_empresarial_react`):

| Notebook | Para qué |
|---|---|
| `Demo_Efimera_TejidoEmpresarial.ipynb` | Compila el frontend, levanta la API en Colab y expone una **URL pública temporal** (TryCloudflare) para revisar el aplicativo antes de desplegarlo. Modo de datos sintéticos o Snowflake real; con datos reales protege la URL con usuario y contraseña generados al vuelo. |
| `Publicacion_GitHub_TejidoEmpresarial.ipynb` | Publica de Drive a **GitHub** (`EnriqueForero/tejido_empresarial`) con validaciones, pruebas del backend, compilación del frontend, `commit`, `push`, tag `vX.Y.Z` y verificación del SHA remoto. |

Flujo recomendado: revisar con la demo efímera → publicar con el notebook →
Railway redespliega solo en cada push.

## Despliegue en Railway

1. Suba este directorio a un repositorio Git (sin `.env` ni llaves).
2. En Railway, cree un servicio desde el repositorio: detecta `railway.toml` y construye el `Dockerfile` (Node 22 compila React; Python 3.11 ejecuta FastAPI).
3. Configure las variables `SF_*` y la llave en Base64. Opcionalmente `APP_BASIC_USER`/`APP_BASIC_PASSWORD` y `PUBLIC_ORIGIN`.
4. Despliegue. Railway inyecta `PORT`; el health check usa `/api/health`.
5. Verifique `https://SU-DOMINIO/api/health?deep=true` (prueba real de Snowflake), una búsqueda y una descarga.

La guía paso a paso, con la lista de verificación, está en [`GUIA_TRANSFERENCIA.md`](GUIA_TRANSFERENCIA.md).

## Actualizar los cortes de información

Cuando llegue un nuevo mes o se cierre un año, edite **sólo** `backend/config.py` (bloques *PASO 1* y *PASO 2*) siguiendo los comentarios del archivo, reemplace el glosario en `backend/resources/` si cambió y vuelva a desplegar. Etiquetas de filtros, metadatos, Excel y glosario se derivan de esos parámetros.

## Calidad y pruebas

```bash
# Backend: 17 pruebas (API en modo demo, SQL, Excel, glosario)
pip install -r requirements-dev.txt
pytest -q

# Frontend: tipos + build de producción
cd frontend && npm run build

# Imagen Docker
docker build -t tejido-empresarial .
docker run --rm -p 8080:8080 -e APP_DEMO_MODE=true tejido-empresarial
```

La integración continua (`.github/workflows/build.yml`) repite estas dos
comprobaciones en cada push y pull request.

Herramientas adicionales en `scripts/`:

- `reformatear_excel.py`: convierte un Excel plano (como los de la versión Streamlit) al nuevo formato con resumen y diccionario.
- `vista_previa_excel.py`: genera una vista HTML de cualquier libro para revisar el formato sin abrir Excel.

## Endpoints

| Método | Ruta | Propósito |
|---|---|---|
| `GET` | `/api/health` (`?deep=true`) | Estado del servicio; con `deep` prueba Snowflake. |
| `GET` | `/api/metadata` | Filtros, columnas, secciones, fuentes, cortes y límites. |
| `POST` | `/api/filters/options` | Opciones dependientes según las selecciones actuales. |
| `POST` | `/api/companies/search` | Vista previa paginada (15 variables clave). |
| `GET` | `/api/companies/{nit}` | Ficha completa de una empresa por NIT exacto. |
| `POST` | `/api/companies/export` | Excel formateado con todos los resultados permitidos. |
| `GET` | `/api/glossary` | Glosario estructurado. |
| `GET` | `/api/resources/glossary.xlsx` · `/api/resources/methodology.docx` | Documentos institucionales. |

## Seguridad

- El navegador nunca recibe credenciales ni SQL; los filtros y columnas provienen de listas blancas y los valores se escapan como literales.
- Cabeceras `Content-Security-Policy`, `X-Frame-Options`, `Referrer-Policy` y `Permissions-Policy`; límite de tamaño de solicitud.
- Autenticación HTTP Basic opcional para toda la aplicación.
- Las cadenas que Excel podría interpretar como fórmulas se neutralizan; los identificadores se escriben como texto.
- La auditoría de eventos en `SEGUIMIENTO.EVENTOS` se registra en segundo plano y nunca bloquea al usuario.
