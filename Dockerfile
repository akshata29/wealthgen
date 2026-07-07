# syntax=docker/dockerfile:1
# WealthGen — single-image build: React (Vite) frontend + FastAPI backend.
# The backend serves the built SPA at "/" and the API under "/api".

# ---------------------------------------------------------------------------
# Stage 1 — build the frontend
# ---------------------------------------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2 — backend runtime (Python 3.11 + Microsoft ODBC Driver 18 for Fabric)
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS backend
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONIOENCODING=utf-8

# Microsoft ODBC Driver 18 for SQL Server (required by pyodbc / Fabric SQL) +
# build deps for pyodbc.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg ca-certificates \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -sSL https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Backend source (see .dockerignore for exclusions — .env/.venv are NOT copied;
# runtime config comes from App Service application settings).
COPY backend/ ./

# Built frontend -> served by FastAPI from app/static.
COPY --from=frontend /fe/dist ./app/static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
