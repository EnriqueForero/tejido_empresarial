# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────────────────
# Etapa 1 · Compilar el frontend React (Node 22 LTS, requerido por Vite 8)
# ─────────────────────────────────────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Etapa 2 · Servir API + frontend compilado desde un único proceso (FastAPI)
# Railway inyecta PORT; uvicorn lo lee. Sin Node en la imagen final.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production
WORKDIR /app
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt \
    && addgroup --system app \
    && adduser --system --ingroup app app
COPY backend/ ./backend/
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist
RUN chown -R app:app /app
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/api/health', timeout=4)" || exit 1
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
