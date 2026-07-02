"""Research endpoints — third-party investment research via provider MCP servers.

Uses the headless OAuth path (see research_agent / research_direct). Endpoints
surface clear errors when a provider has not completed its one-time login.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.agents import research_agent
from app.agents.research_agent import ResearchNotConfiguredError
from app.models.sources import Citation
from app.services.mcp_oauth import NotLoggedInError, OAuthError

logger = logging.getLogger(__name__)
router = APIRouter()


class ResearchRequest(BaseModel):
    query: str


class ResearchResponse(BaseModel):
    answer: str
    citations: list[Citation] = []


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (ResearchNotConfiguredError, NotLoggedInError)):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "RESEARCH_NOT_CONFIGURED", "message": str(exc)},
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"code": "OAUTH_ERROR", "message": str(exc)},
    )


@router.post("/research/query", response_model=ResearchResponse)
async def research_query(request: ResearchRequest) -> ResearchResponse:
    try:
        answer, citations = await research_agent.research(request.query)
    except (ResearchNotConfiguredError, NotLoggedInError, OAuthError) as exc:
        raise _http_error(exc) from exc
    return ResearchResponse(answer=answer, citations=citations)


@router.get("/research/providers")
async def research_providers() -> dict:
    return {"providers": research_agent.configured_providers()}


@router.get("/mandates/{mandate_id}/morningstar-xray", response_model=ResearchResponse)
async def morningstar_xray(mandate_id: str, period: str | None = Query(None)) -> ResearchResponse:
    try:
        answer, citations = await research_agent.portfolio_xray(mandate_id, period)
    except (ResearchNotConfiguredError, NotLoggedInError, OAuthError) as exc:
        raise _http_error(exc) from exc
    return ResearchResponse(answer=answer, citations=citations)


@router.get("/mandates/{mandate_id}/lseg-context", response_model=ResearchResponse)
async def lseg_context(mandate_id: str, period: str | None = Query(None)) -> ResearchResponse:
    try:
        answer, citations = await research_agent.lseg_market_context(mandate_id, period)
    except (ResearchNotConfiguredError, NotLoggedInError, OAuthError) as exc:
        raise _http_error(exc) from exc
    return ResearchResponse(answer=answer, citations=citations)

