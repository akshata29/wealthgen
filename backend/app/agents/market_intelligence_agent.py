"""MarketIntelligenceAgent — assembles market context (Web IQ grounded).

Uses no client data. In `local` grounding mode it builds MarketContextFacts from
the synthetic dataset (index returns, FX, and VIX-derived themes); in `foundry_iq`
mode it takes index/FX numbers from the reference_data (Fabric) baseline and adds
live web themes from Web IQ. (LSEG MCP is disabled — placeholder credentials 401.)
"""

from __future__ import annotations

import logging

from app.infra.settings import get_settings
from app.models.market import FxMove, IndexReturn, MarketContextFacts
from app.services import market_context_sources, reference_data

logger = logging.getLogger(__name__)

AGENT_NAME = "MarketIntelligenceAgent"


async def build_context(period: str, commentary_type: str = "quarterly_review") -> MarketContextFacts:
    if get_settings().grounding_mode == "local":
        facts = _build_context_local(period)
    else:
        facts = await _build_context_foundry_iq(period)
    # Surface the real-world context an advisor reads — live web (Web IQ) blended
    # with the curated library. For event-driven briefs, anchor the live search on
    # the period's market event so the pulled commentary is about that event.
    event_topic = None
    if commentary_type == "event_driven":
        event = reference_data.get_vix_event(period)
        event_topic = event.headline if event else (facts.themes[0] if facts.themes else None)
    facts.context_sources = await market_context_sources.select_sources(
        period, commentary_type, themes=facts.themes, event_topic=event_topic
    )
    # Derive live themes from the SAME Web IQ search (no extra call) so the
    # 'Market Context' section reflects current web headlines when available.
    live_titles = [s.title for s in facts.context_sources if s.live and s.title][:5]
    if live_titles:
        facts.themes = live_titles
    return facts


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
    # Baseline from the authoritative reference data (Fabric): index/FX/themes are
    # present there, so the brief still grounds if LSEG or Web IQ are unavailable.
    # Web themes are derived from the single context-source search in build_context
    # (no separate Web IQ call here) to stay well under the API rate limit.
    baseline = _build_context_local(period)

    # LSEG MCP is disabled: the configured endpoint returns 401 (placeholder
    # credentials). Index/FX numbers come from the authoritative reference_data
    # (Fabric) baseline above. To re-enable, set real LSEG creds in .env and
    # restore the lseg_mcp.get_index_returns/get_fx_moves calls here.
    return MarketContextFacts(
        period=period,
        themes=baseline.themes,
        index_returns=baseline.index_returns,
        fx_moves=baseline.fx_moves,
    )
