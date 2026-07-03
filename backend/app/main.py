"""FastAPI application factory for WealthGen — Portfolio Narrative Generator."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
