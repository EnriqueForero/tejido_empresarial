# Segmentación Empresarial — Streamlit App

## Descripción del Proyecto

Esta aplicación analítica desarrollada por **ProColombia** permite explorar y visualizar el tejido empresarial colombiano con énfasis en el potencial exportador. A través de cinco módulos analíticos interconectados, los usuarios pueden segmentar empresas, analizar destinos de exportación, evaluar valor agregado y estudiar la distribución geográfica de las exportaciones colombianas.

La aplicación se conecta a un data warehouse en **Snowflake** y expone los datos mediante una interfaz web construida con **Streamlit**, con visualizaciones interactivas de Plotly, mapas con Folium/GeoPandas, y exportación de resultados a Excel.

---

## Funcionalidades

| Página | Descripción |
|---|---|
| **Inicio** (`app.py`) | Página de bienvenida con descripción general de la herramienta |
| **Segmentación** | Análisis del tejido empresarial por segmentos de exportabilidad y servicios de ProColombia |
| **Empresas** | Métricas detalladas por empresa: exportaciones FOB, tamaño, sectores, top exportadores |
| **Destinos** | Análisis de destinos de exportación, comercio bilateral y diversificación de mercados |
| **Valor Agregado** | Seguimiento de métricas de valor agregado, análisis de productos y bienes/servicios |
| **Territorios** | Análisis geográfico por departamento y municipio con mapas interactivos |

La disponibilidad de datos por módulo es:
- **Exportaciones**: 2021–2025
- **Servicios, Oportunidades, Negociaciones**: 2023–2025

---

## Requisitos

- Python 3.8 o superior
- Acceso a la instancia de Snowflake (`my17686.us-east-2.aws`)
- Archivo `.env` con las variables de entorno (ver sección de configuración)
- Archivos de llave RSA (`rsa_key_1.der` y `rsa_key_2.der`) para autenticación

---

## Instalación y Ejecución Local

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd app-segmentacion-exportaciones

# 2. Crear y activar entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (ver sección siguiente)
# Crear el archivo .env en la raíz del proyecto

# 5. Ejecutar la aplicación
streamlit run app.py
```

---

## Configuración de Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```dotenv
SF_ACCOUNT=my17686.us-east-2.aws
SF_USER=USER_SERVICE_ANALITICA
SF_PRIVATE_KEY_PATH_1=rsa_key_1.der
SF_PRIVATE_KEY_PATH_2=rsa_key_2.der
SF_DATABASE=APP_SEGMENTACION_EXPORTACIONES
SF_SCHEMA=SEGMENTACION
SF_WAREHOUSE=APPS_WH
SF_ROLE=APP_SEGMENTACION_EXPORTACIONES
```

Los archivos `.env` y los archivos de llave (`.der`) están excluidos del repositorio por seguridad y deben solicitarse al equipo de desarrollo.

---

## Estructura del Proyecto

```
app-segmentacion-exportaciones/
│
├── app.py                              # Punto de entrada — página de inicio
│
├── pages/                              # Páginas de la aplicación (enrutamiento por query params)
│   ├── segmentacion.py
│   ├── empresas.py
│   ├── destinos.py
│   ├── valor_agregado.py
│   └── territorios.py
│
├── src/                                # Código fuente modular
│   │
│   ├── streamlit_analitica/            # Componentes y utilidades de la interfaz
│   │   ├── components.py               # navbar(), home_page(), footer()
│   │   └── helpers.py                  # get_icon(), get_image(), load_css()
│   │
│   ├── snowflake_analitica/            # Capa de integración con Snowflake
│   │   ├── config.py                   # Creación de sesión (autenticación por llaves RSA)
│   │   ├── streamlit_snowflake.py      # Puente Streamlit-Snowflake
│   │   ├── dml.py                      # Ejecución de consultas y registro de auditoría
│   │   ├── ddl.py                      # Definición de tablas
│   │   └── helpers.py                  # Utilidades de Snowflake
│   │
│   ├── pages_utils/                    # Utilidades específicas por página
│   │   ├── config.py                   # Columnas, años disponibles, clasificación de períodos
│   │   ├── utils.py                    # Filtros, formateo y helpers compartidos
│   │   ├── segmentacion_utils.py
│   │   ├── empresas_utils.py
│   │   ├── destinos_utils.py
│   │   ├── valor_agregado_utils.py
│   │   ├── mapas_departamentos_utils.py
│   │   └── mapas_municipios_utils.py
│   │
│   └── filtros_dinamicos_analitica/    # Componente de filtros en cascada
│       └── filtros_dinamicos.py        # Clase DynamicFilters
│
├── assets/                             # Recursos estáticos
│   ├── css/
│   │   └── styles.css                  # Estilos personalizados
│   ├── images/                         # Logos e íconos
│   └── docs/                           # Documentación interna
│
├── data/                               # Datos (excluidos del repositorio por tamaño)
│   ├── BIENES_Y_SERVICIOS_P.csv        # ~263 MB
│   ├── TEJIDO_EMPRESARIAL_P.csv        # ~767 MB
│   └── Mapas/                          # Shapefiles geoespaciales (departamentos y municipios)
│
├── setup/                              # Notebooks Jupyter para configuración inicial de BD
│   ├── 01 - Database creation/
│   ├── 02 - Table uploads/
│   ├── 03 - Roles and permissions/
│   └── 04 - Table definitions/
│
├── .streamlit/
│   ├── config.toml                     # Tema, configuración del servidor y cliente
│   └── snowflake_credentials.json      # Perfil de conexión alternativo (excluido del repo)
│
├── .devcontainer/
│   └── devcontainer.json               # Configuración para entorno Docker
│
├── .codesandbox/
│   └── tasks.json                      # Tareas de despliegue en CodeSandbox
│
├── requirements.txt                    # Dependencias Python
└── .env                                # Variables de entorno (excluido del repo)
```

---

## Arquitectura de la Aplicación

### Navegación

La aplicación utiliza parámetros de URL (`?page=1-6`) para el enrutamiento en lugar de la navegación nativa de Streamlit. La barra de navegación personalizada en `src/streamlit_analitica/components.py` controla el enrutamiento y se renderiza al inicio de cada página.

### Flujo de Datos

```
flujo_snowflake()
  └── Verifica/crea sesión Snowflake (timeout: 15 minutos)
        │
        ▼
load_filtros_*()
  └── Carga valores de filtros desde Snowflake (cacheados con @st.cache_data)
        │
        ▼
DynamicFilters
  └── Filtros multi-selección en cascada aplicados sobre DataFrames
        │
        ▼
query_data_*()
  └── Consultas SQL parametrizadas (protegidas contra inyección SQL)
        │
        ▼
Visualizaciones
  └── Plotly (gráficos interactivos), Folium + GeoPandas (mapas), Pandas (tablas)
        │
        ▼
registrar_evento()
  └── Registro de auditoría en Snowflake con cada interacción del usuario
        │
        ▼
descarga_tabla()
  └── Exportación a Excel formateado (openpyxl)
```

### Tablas en Snowflake

Base de datos: `APP_SEGMENTACION_EXPORTACIONES`, esquema: `SEGMENTACION`

| Tabla | Descripción |
|---|---|
| `TEJIDO_EMPRESARIAL_P_BASE_MUNICIPIOS_P` | Tejido empresarial por municipio |
| `BIENES_Y_SERVICIOS_P` | Bienes y servicios exportados |
| `BIENES_Y_SERVICIOS_P_TEJIDO_EMPRESARIAL_P` | Tabla combinada para análisis cruzado |

La autenticación con Snowflake se realiza mediante **llaves RSA** (dos llaves para rotación). La sesión se gestiona con un mecanismo de timeout de inactividad de 15 minutos.

---

## Opciones de Despliegue

| Entorno | Instrucción |
|---|---|
| **Local** | `streamlit run app.py` |
| **DevContainer** | Abrir en VS Code con Docker; configuración en `.devcontainer/devcontainer.json` |
| **CodeSandbox** | Tareas definidas en `.codesandbox/tasks.json` |
| **Streamlit Cloud** | Configuración lista en `.streamlit/config.toml` |

---

## Tecnologías Principales

- **Streamlit 1.40.1** — framework web
- **Snowflake Connector 3.12.3 / Snowpark 1.25.0** — integración con data warehouse
- **Pandas 2.2.3** — procesamiento de datos
- **Plotly 5.24.1** — visualizaciones interactivas
- **Folium 0.18.0 / GeoPandas 1.0.1** — mapas geoespaciales
- **Bootstrap 5.3.3** — estilos frontend (CDN)

---

## Contacto

Para consultas o sugerencias, comunicarse con el equipo de desarrollo de **ProColombia**.
