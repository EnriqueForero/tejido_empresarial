# Código Streamlit original (referencia)

Esta carpeta contiene, sin modificaciones, el aplicativo Streamlit `tejido-empresarial-app-main` (2026-09-01) del cual se migró la experiencia a React + FastAPI.

- **No se despliega**: el `Dockerfile` y `railway.toml` de la raíz del repositorio construyen únicamente la versión React.
- **Para qué sirve**: consultar la lógica original de filtros, consultas y descargas; comparar comportamientos; recuperar módulos deshabilitados (Empresas, Destinos, Valor Agregado, Territorios) si en el futuro se decide migrarlos.
- **Equivalencias**: ver `../MIGRACION_REACT.md`.

Para ejecutarlo localmente (opcional): `pip install -r requirements.txt` y `streamlit run app.py` dentro de esta carpeta, con el `.env` de Snowflake.
