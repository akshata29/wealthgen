"""FastAPI application factory for WealthGen — Portfolio Narrative Generator."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.infra.settings import get_settings
from app.infra.telemetry import setup_telemetry
from app.routers import approvals, clients, commentary, export, health, ingest, research

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry()
    logger.info("WealthGen backend starting (env=%s)", settings.app_env)
    logger.info("Reference data source mode: %s", settings.data_source_mode)
    yield


app = FastAPI(
    title="WealthGen — Portfolio Narrative Generator API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(commentary.router, prefix="/api", tags=["commentary"])
app.include_router(approvals.router, prefix="/api", tags=["approvals"])
app.include_router(clients.router, prefix="/api", tags=["clients"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(research.router, prefix="/api", tags=["research"])


# --- Serve the built frontend (single App Service / container) --------------
# In production the Vite build is copied to app/static; FastAPI serves the SPA
# at "/" and its assets, while the API stays under "/api". If the build is not
# present (local dev with the Vite dev server), this block is skipped.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    _ASSETS_DIR = _STATIC_DIR / "assets"
    if _ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        # Serve a real static file (favicon, manifest, …) when it exists,
        # otherwise fall back to index.html for client-side routing.
        candidate = _STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")
