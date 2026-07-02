"""LSEG market-data connector (via MCP).

Thin, swappable interface (Bloomberg / Morningstar could replace it later).
Returns typed market facts with `lseg:`-prefixed source ids. Calls the live LSEG
MCP endpoint configured in settings — no mock data.
"""

from __future__ import annotations

import logging

import httpx

from app.infra.settings import get_settings
from app.models.market import FxMove, IndexReturn

logger = logging.getLogger(__name__)


class LsegConfigError(RuntimeError):
    """Raised when the LSEG MCP endpoint is not configured."""


def _endpoint() -> str:
    settings = get_settings()
    if not settings.lseg_mcp_url:
        raise LsegConfigError("LSEG_MCP_URL is not configured; set it in .env.")
    return settings.lseg_mcp_url


async def _call(tool: str, arguments: dict) -> dict:
    url = f"{_endpoint().rstrip('/')}/tools/{tool}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json={"arguments": arguments})
        resp.raise_for_status()
        return resp.json()


async def get_index_returns(period: str) -> list[IndexReturn]:
    data = await _call("get_index_returns", {"period": period})
    return [
        IndexReturn(
            name=row["name"],
            period_return=float(row["return"]),
            source_id=f"lseg:index:{row['name']}",
        )
        for row in data.get("results", [])
    ]


async def get_fx_moves(pairs: list[str]) -> list[FxMove]:
    data = await _call("get_fx_moves", {"pairs": pairs})
    return [
        FxMove(
            pair=row["pair"],
            change_pct=float(row["change_pct"]),
            source_id=f"lseg:fx:{row['pair']}",
        )
        for row in data.get("results", [])
    ]
