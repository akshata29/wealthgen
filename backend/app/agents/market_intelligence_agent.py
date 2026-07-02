"""MarketIntelligenceAgent — assembles market context (Web IQ + LSEG grounded).

Uses no client data. In `local` grounding mode it builds MarketContextFacts from
the synthetic dataset (index returns, FX, and VIX-derived themes); in `foundry_iq`
mode it combines LSEG index/FX facts with web-grounded themes.
"""

from __future__ import annotations

import json
import logging

from app.agents.prompts import MARKET_SYSTEM
from app.infra.settings import get_settings
from app.models.market import FxMove, IndexReturn, MarketContextFacts
from app.services import foundry_iq, lseg_mcp, reference_data

logger = logging.getLogger(__name__)

AGENT_NAME = "MarketIntelligenceAgent"
DEFAULT_FX_PAIRS = ["GBP/USD", "EUR/USD"]


async def build_context(period: str) -> MarketContextFacts:
    if get_settings().grounding_mode == "local":
        return _build_context_local(period)
    return await _build_context_foundry_iq(period)


def _build_context_local(period: str) -> MarketContextFacts:
    index_returns = [
        IndexReturn(name=i.index_name, period_return=i.period_return_pct, source_id=i.source_id)
        for i in reference_data.get_index_returns(period)
    ]
    fx_moves = [
        FxMove(pair=pair, change_pct=change, source_id=sid)
        for pair, change, sid in reference_data.get_fx_moves(period)
    ]
    event = reference_data.get_vix_event(period)
    themes: list[str] = []
    if event:
        themes.append(event.headline)
        themes.append(f"Volatility regime: {event.regime} (VIX {event.vix_close:.0f}).")
    return MarketContextFacts(
        period=period,
        themes=themes,
        index_returns=index_returns,
        fx_moves=fx_moves,
    )


async def _build_context_foundry_iq(period: str) -> MarketContextFacts:
    index_returns = await lseg_mcp.get_index_returns(period)
    fx_moves = await lseg_mcp.get_fx_moves(DEFAULT_FX_PAIRS)

    agent = foundry_iq.ensure_agent(AGENT_NAME, MARKET_SYSTEM)
    prompt = (
        f"For the reporting period '{period}', list the dominant market themes from the "
        "web (Web IQ). Return a JSON object with a 'themes' string array only."
    )
    text, _ = foundry_iq.run_agent(agent, prompt)
    themes = _slice_themes(text)

    return MarketContextFacts(
        period=period,
        themes=themes,
        index_returns=index_returns,
        fx_moves=fx_moves,
    )


def _slice_themes(text: str) -> list[str]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return []
    try:
        payload = json.loads(text[start : end + 1])
        themes = payload.get("themes", [])
        return [str(t) for t in themes if t]
    except json.JSONDecodeError:
        logger.warning("MarketIntelligenceAgent returned unparseable themes.")
        return []
