# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**Tejido Empresarial · ProColombia** — company segmentation app for ProColombia's Exportaciones / Inversión / Turismo business axes. React 19 + TypeScript (Vite 8) frontend, FastAPI backend querying Snowflake, single Docker image deployed on Railway. The original Streamlit app lives untouched in `legado_streamlit/` (reference only, not deployed).

## Commands

```bash
# Backend (Python 3.11; 3.10 works)
pip install -r requirements-dev.txt
APP_DEMO_MODE=true uvicorn backend.main:app --reload --port 8000   # synthetic data, no Snowflake
pytest -q                                                           # 35 tests

# Frontend (Node 22)
cd frontend && npm ci && npm run dev      # http://localhost:5173, proxies /api → :8000
cd frontend && npm run build              # tsc -b + vite build → frontend/dist (served by FastAPI)

# Docker (what Railway runs)
docker build -t tejido . && docker run --rm -p 8080:8080 -e APP_DEMO_MODE=true tejido

# Utilities
python scripts/reformatear_excel.py ENTRADA.xlsx --dir SALIDA/     # old flat Excel → new formatted workbook
python scripts/vista_previa_excel.py LIBRO.xlsx salida.html          # HTML preview of a workbook

# Colab notebooks (notebooks/) — run in Google Colab, not locally
#   Demo_Efimera_TejidoEmpresarial.ipynb        build + uvicorn + TryCloudflare public URL
#   Publicacion_GitHub_TejidoEmpresarial.ipynb  Drive → GitHub (validations, tests, build, tag)
```

## Architecture

```
backend/
  config.py     ← THE file to edit when data cuts change (PASO 1 periods, PASO 2 export columns).
                  Also: filter definitions (key/query_column/label/group/help), QUERY_COLUMNS (63 aliases
                  identical to the original app), PREVIEW_COLUMNS, COLUMN_SECTIONS, DATA_SOURCES, table names.
  models.py     Pydantic request models; SearchMode = filters | business_name | nit | batch_nits.
  queries.py    SQL generation (allowlisted columns, sql_literal escaping). Same semantics as the original:
                general filters on table A, export filters via NIT subquery on BIENES_Y_SERVICIOS_P (B).
  database.py   SnowflakeService: RSA key auth, key rotation (JWT error → fallback key), retries, log_event.
                normalizar_llave() accepts base64-of-DER (whitespace tolerated), raw PEM, base64-of-PEM and
                .der/.p8 files; decrypts with SF_PRIVATE_KEY_PASSPHRASE_N and hands the connector plain PKCS8 DER.
                diagnostico() walks entorno → conector → llave → sesión → tablas and returns the real error per step.
  exporter.py   xlsxwriter workbook: Resumen · Ficha_Empresa (1 company) · Vista_Principal · Datos_Completos · Diccionario.
  glossary.py   Reads resources/2026_09_01_Glosario_variables_Aplicativo.xlsx (sheet Explicacion_Variables);
                adds SUPPLEMENTARY_DEFINITIONS for derived range columns; links variables to filters/preview.
  demo.py       14 synthetic companies + dependent filter options (APP_DEMO_MODE=true).
  main.py       FastAPI app: middleware (size limit, optional HTTP Basic, security headers/CSP),
                /api/* endpoints, SPA fallback serving frontend/dist.

frontend/src/
  main.tsx, App.tsx          BrowserRouter; routes / , /consultar, /glosario, /metodologia, /empresa/:nit
  api.ts, tipos.ts, formato.ts, hooks.ts
  componentes/               Encabezado, Pie, Interfaz (Revelar, ContadorAnimado, Aviso, Ayuda…), TejidoPortada (hero SVG),
                             ModoBusqueda, PanelFiltros, SelectorFiltro, CargaNits, Resultados, DescargaExcel
  paginas/                   Inicio, Consultar, Glosario, Metodologia, FichaEmpresa, Estado
  estilos/                   base.css (tokens, buttons, cards), estructura.css (header/footer/menu), portada.css,
                             consulta.css, resultados.css, paginas.css

notebooks/      Colab: ephemeral demo + GitHub publisher. The publisher's Celda A holds repo,
                markers, required files and build commands; version is synced in BOTH
                frontend/package.json and backend/config.py (APP_VERSION).
.github/workflows/build.yml   CI: pytest (demo mode) + npm run build.
```

## Conventions

- UI language is Spanish (Colombia); identifiers in code are Spanish in the frontend, English in the backend.
- Design tokens mirror the `celula-ia-gic` reference app: `--tinta #011627`, `--cinta #ffa400`, Jost (display), Maven Pro (body), IBM Plex Mono (data). Fonts are bundled via `@fontsource`; no CDNs.
- All motion respects `prefers-reduced-motion`. Reveal/counter components have timeout fallbacks.
- Never put credentials or SQL in the frontend. Filters/columns are allowlisted in `backend/config.py`.
- Contact fields are included in exports by default (as in Streamlit); `EXPORT_INCLUDE_CONTACT_FIELDS=false` removes them.
- Access is open unless `APP_BASIC_USER` and `APP_BASIC_PASSWORD` are both set.
- Excel: identifiers as text, COP without decimals, FOB USD with 2 decimals, navy header + amber accent, frozen panes, autofilter, print setup. Tests in `tests/test_exporter.py` pin this structure.

## Troubleshooting a deployment

`/api/health` reports connector presence, version, missing `SF_*` vars and key sources.
`/api/diagnostico` (Basic auth, `APP_DIAG_TOKEN`, or APP_ENV=development) runs the full chain and
returns the first failing step plus a concrete recommendation.
The `/estado` page renders all of that for non-technical users (header badge + «probar conexión» +
step checklist); `/estado?token=…` auto-runs the diagnostic. See `DIAGNOSTICO_RAILWAY.md`.

## Snowflake objects (unchanged)

- `APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION.TEJIDO_EMPRESARIAL_COMPLETO_BASE_MUNICIPIOS_P` (companies, alias A)
- `APP_SEGMENTACION_EXPORTACIONES.PUBLIC.BIENES_Y_SERVICIOS_P` (export filters, alias B)
- `…SEGMENTACION.FILTROS_GENERALES_TEJIDO_EMPRESARIAL_COMPLETO`, `…SEGMENTACION.FILTROS_EXPORTADORAS` (filter option tables)
- `APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO.EVENTOS` (audit log)

## Environment

See `.env.example`. Required for real data: `SF_ACCOUNT`, `SF_USER`, `SF_DATABASE`, `SF_SCHEMA`, `SF_WAREHOUSE`, `SF_ROLE` and one private key (`SF_PRIVATE_KEY_B64_1` or `SF_PRIVATE_KEY_PATH_1`).
