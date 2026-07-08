"""Advisory workspace endpoints — clients, portfolios, performance, and events.

Read-only views over the synthetic Fabric IQ dataset (see reference_data). These
back the client/portfolio list, the templated performance widgets (benchmark /
sector / index compare), the next-best-action panel, and the event feed.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.models.portfolio import (
    ClientSummary,
    Holding,
    Mandate,
    NextBestAction,
    PerformanceReport,
    PositioningChange,
    VixEvent,
)
from app.services import reference_data
from app.services.reference_data import DatasetNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


def _guard(fn):
    """Translate a missing dataset into a clear 503 for the frontend."""
    try:
        return fn()
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "NO_DATASET", "message": str(exc)},
        ) from exc


@router.get("/periods")
async def periods() -> dict:
    return _guard(lambda: {"periods": reference_data.list_periods(), "latest": reference_data.latest_period()})


@router.get("/clients", response_model=list[ClientSummary])
async def clients() -> list[ClientSummary]:
    return _guard(reference_data.list_clients)


@router.get("/clients/{client_id}", response_model=ClientSummary)
async def client(client_id: str) -> ClientSummary:
    result = _guard(lambda: reference_data.get_client(client_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    return result


@router.get("/mandates", response_model=list[Mandate])
async def mandates(client_id: str | None = Query(None)) -> list[Mandate]:
    return _guard(lambda: reference_data.list_mandates(client_id))


@router.get("/mandates/{mandate_id}", response_model=Mandate)
async def mandate(mandate_id: str) -> Mandate:
    result = _guard(lambda: reference_data.get_mandate(mandate_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    return result


def _resolve_period(period: str | None) -> str:
    return period or reference_data.latest_period()


@router.get("/mandates/{mandate_id}/performance", response_model=PerformanceReport)
async def performance(mandate_id: str, period: str | None = Query(None)) -> PerformanceReport:
    def _build() -> PerformanceReport | None:
        return reference_data.build_performance_report(mandate_id, _resolve_period(period))

    result = _guard(_build)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "No performance for that mandate/period."},
        )
    return result


@router.get("/mandates/{mandate_id}/holdings", response_model=list[Holding])
async def holdings(mandate_id: str, period: str | None = Query(None)) -> list[Holding]:
    return _guard(lambda: reference_data.get_holdings(mandate_id, _resolve_period(period)))


@router.get("/mandates/{mandate_id}/positioning", response_model=list[PositioningChange])
async def positioning(mandate_id: str, period: str | None = Query(None)) -> list[PositioningChange]:
    return _guard(lambda: reference_data.get_positioning(mandate_id, _resolve_period(period)))


@router.get("/mandates/{mandate_id}/next-best-actions", response_model=list[NextBestAction])
async def next_best_actions(mandate_id: str, period: str | None = Query(None)) -> list[NextBestAction]:
    return _guard(lambda: reference_data.next_best_actions(mandate_id, period))


@router.get("/events/vix", response_model=list[VixEvent])
async def vix_events(triggers_only: bool = Query(False)) -> list[VixEvent]:
    return _guard(lambda: reference_data.get_vix_events(only_triggers=triggers_only))


@router.get("/events/scan")
async def scan_events(period: str = Query(...)) -> list[dict]:
    """Scan for market events in the period and the mandates whose holdings they affect.

    Powers event-driven testing: each result lists the event and the client
    portfolios holding an affected fund (with weights), ready to generate an
    event-driven brief for.
    """
    from app.services import market_events

    return _guard(lambda: market_events.scan(period))


@router.get("/events/live")
async def live_events(limit: int = Query(3)):
    """Detect CURRENT market events from the live web (Web IQ).

    The autonomous watcher’s live feed. Returns citeable context sources; an empty
    list means Web IQ is unconfigured or rate-limited (fall back to the scenario).
    """
    from app.services import market_events

    return await market_events.scan_live(limit=limit)
