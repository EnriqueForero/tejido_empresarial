# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py

# Database setup (one-time, Jupyter notebooks in order)
# setup/01 - Database creation
# setup/02 - Table uploads
# setup/03 - Roles and permissions
# setup/04 - Table definitions
```

## Environment Setup

The app requires a `.env` file (gitignored) with Snowflake credentials:

```
SF_ACCOUNT=<snowflake_account>
SF_USER=<service_account>
SF_PRIVATE_KEY_PATH_1=<path_to_rsa_key_1.der>
SF_PRIVATE_KEY_PASSPHRASE_1=<passphrase_1>
SF_PRIVATE_KEY_PATH_2=<path_to_rsa_key_2.der>
SF_PRIVATE_KEY_PASSPHRASE_2=<passphrase_2>
SF_DATABASE=APP_SEGMENTACION_EXPORTACIONES
SF_SCHEMA=SEGMENTACION
SF_WAREHOUSE=APPS_WH
SF_ROLE=APP_SEGMENTACION_EXPORTACIONES
```

RSA key files (`.der`) are gitignored and must be provided separately. The app automatically falls back to `SF_PRIVATE_KEY_PATH_2` if the first key produces a JWT token error.

## Architecture

**Purpose**: Colombian export segmentation analytics app for ProColombia. Allows analysis of the Colombian business fabric by export potential, destinations, value-added, and territory.

### Multi-Page Structure

Navigation uses query parameters (`?page=1-6`) rather than Streamlit's native page routing. The custom navbar in `src/streamlit_analitica/components.py` drives routing. Each page file contains its own `st.set_page_config()` call and a full set of `st.switch_page()` redirects for all other pages.

```
app.py                → Entry point, home page (page=1)
pages/
  segmentacion.py     → Company segmentation analysis (page=2)
  empresas.py         → Company-level metrics and top exporters (page=3)
  destinos.py         → Export destinations and bilateral trade (page=4)
  valor_agregado.py   → Value-added metrics and product analysis (page=5)
  territorios.py      → Geographic analysis (departments/municipalities) (page=6)
```

### Data Flow

1. `flujo_snowflake()` — checks/creates the Snowflake session with a 15-minute inactivity timeout (defined in `src/snowflake_analitica/streamlit_snowflake.py`, called at the top of every page)
2. `load_filtros_*()` — `@st.cache_data`-decorated functions that fetch filter values from Snowflake filter tables
3. `DynamicFilters` (`src/filtros_dinamicos_analitica/filtros_dinamicos.py`) — cascading multi-select filters applied to DataFrames
4. `query_data_*()` — builds parameterized SQL queries, executed via `ejecutar_consulta_segura()` (returns empty DataFrame on no results)
5. Visualizations rendered with Plotly, Folium, and GeoPandas
6. `registrar_evento()` — writes user interaction events to `SEGUIMIENTO.EVENTOS` in Snowflake
7. `descarga_tabla()` — exports formatted Excel files via openpyxl

### Key Source Modules

| Module | Purpose |
|---|---|
| `src/snowflake_analitica/streamlit_snowflake.py` | `flujo_snowflake()`, `create_session()`, `registrar_evento()` — RSA key auth with retry logic |
| `src/snowflake_analitica/config.py` | Alternative session creation from JSON/TOML credentials (password-based, used in setup notebooks) |
| `src/snowflake_analitica/dml.py` | `ejecutar_consulta_segura()`, `registrar_evento_auditoria()` |
| `src/pages_utils/config.py` | Column name mappings, available year ranges, and period lists — **update here when adding new data years** |
| `src/pages_utils/utils.py` | `load_filtros_*()` cached functions, `descarga_tabla()`, `mostrar_resultado_en_streamlit()` |
| `src/pages_utils/*_utils.py` | Per-page logic: filter lists, query builders, chart renderers |
| `src/streamlit_analitica/components.py` | `navbar()`, `home_page()`, `footer()` |
| `src/filtros_dinamicos_analitica/filtros_dinamicos.py` | `DynamicFilters` class |

### Snowflake Schemas

**`APP_SEGMENTACION_EXPORTACIONES.SEGMENTACION`** — analytics data:
- `TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P` — enterprise fabric by municipality (used by Segmentación, Empresas)
- `BIENES_Y_SERVICIOS_P` — goods and services (used by Segmentación)
- `BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P` — joined table for cross-analysis (used by Destinos, Valor Agregado, Territorios)
- `FILTROS_GENERALES`, `FILTROS_EXPORTADORAS`, `FILTROS_BIENES` — pre-computed filter value tables loaded at page startup
- `DEPARTAMENTOS_EXPORTACIONES`, `DEPARTAMENTOS_SERVICIOS`, `MUNICIPIOS_EXPORTACIONES` — territorial tables (used by Territorios)

**`APP_SEGMENTACION_EXPORTACIONES.SEGUIMIENTO`** — observability:
- `EVENTOS` — user interaction log written by `registrar_evento()`
- `AUDITORIA_CARGUES` — data load audit log written by `registrar_evento_auditoria()`

### UI Conventions

- Bootstrap 5.3.3 loaded via CDN inline `st.markdown()` on every page; custom styles in `assets/css/styles.css`
- Streamlit's default sidebar navigation is hidden; custom navbar is used instead
- `streamlit-option-menu` used for tab-style navigation within pages

### Extending Data Years

When new export data becomes available, update `src/pages_utils/config.py`:
1. Adjust the year range tuples (e.g., `exportaciones_anios_disponibles = (2021, 2026)`)
2. Add the new year's column to each `COLS_VARIABLES_*` dict (e.g., `'EXPO_2026': 'Exportaciones 2026 (FOB USD)'`)
3. Add the new year's string to `periodos_cerrados` / `periodos_corridos` lists
4. Mirror changes in the corresponding `*_usuario` lists that duplicate dict values for display
