"""Health and non-secret settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.infra.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/settings")
async def settings_info() -> dict:
    """Non-secret configuration for the frontend settings page."""
    s = get_settings()
    return {
        "jurisdictions": s.jurisdictions,
        "default_audience": s.default_audience,
        "endpoints": {
            "foundry": bool(s.foundry_endpoint),
            "search": bool(s.search_endpoint),
            "content_understanding": bool(s.cu_endpoint),
            "cosmos": bool(s.cosmos_endpoint),
            "content_safety": bool(s.content_safety_endpoint),
            "lseg": bool(s.lseg_mcp_url),
            "fabric": bool(s.fabric_workspace_id),
        },
    }
