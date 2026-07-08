"""Market-event scan — the testable core of event-driven commentary.

Detects candidate market events for a period (from the curated event bulletins,
which carry affected tickers) and cross-references them against every mandate's
actual holdings. The result answers: "which clients hold something this event
affects, and should get an event-driven brief?"

This is the on-demand form of an autonomous market watcher: a scheduler could
call `scan()` on a timer (or on a Web IQ news trigger) and auto-queue briefs for
the affected mandates. See scripts/scan_events.py for a CLI/demo runner.
"""

from __future__ import annotations

import logging

from app.models.context import AffectedHolding
from app.services import market_context_sources, reference_data, web_iq

logger = logging.getLogger(__name__)


async def scan_live(limit: int = 3) -> list[dict]:
    """Detect CURRENT market events from the live web (Web IQ) AND cross-reference
    each to the actual portfolios it affects.

    Returns a list of {event, affected_tickers, affected_mandate_count,
    total_mandates, affected_mandates}. Empty when Web IQ is unconfigured or
    rate-limited (the caller falls back to the synthetic scenario event).
    """
    try:
        period = reference_data.latest_period()
    except reference_data.DatasetNotFoundError as exc:
        logger.warning("Reference data unavailable for live scan (%s); using default period.", exc)
        period = "Q2-2026"
    sources = await web_iq.get_context_sources(
        period,
        themes=[],
        commentary_type="event_driven",
        event_topic="breaking market-moving events today affecting equities, rates, and commodities",
        limit=limit,
    )
    if not sources:
        return []

    try:
        mandates = reference_data.list_mandates()
        holdings_by_mandate = {
            m.mandate_id: reference_data.get_holdings(m.mandate_id, period) for m in mandates
        }
    except reference_data.DatasetNotFoundError as exc:
        # Reference data momentarily unavailable (e.g. transient Fabric drop) —
        # return the live events without holdings impact rather than 500.
        logger.warning("Reference data unavailable for live-event cross-ref (%s).", exc)
        return [
            {
                "event": s.model_dump(mode="json"),
                "affected_tickers": _extract_affected_tickers(f"{s.title} {s.summary}"),
                "affected_mandate_count": 0,
                "total_mandates": 0,
                "affected_mandates": [],
            }
            for s in sources
        ]
    names = {m.mandate_id: m.display_name for m in mandates}

    results: list[dict] = []
    for src in sources:
        tickers = _extract_affected_tickers(f"{src.title} {src.summary}")
        affected_mandates: list[dict] = []
        for mandate_id, holdings in holdings_by_mandate.items():
            matched = [
                AffectedHolding(ticker=h.ticker, instrument=h.instrument, weight=h.weight)
                for h in holdings
                if h.ticker in tickers
            ]
            if matched:
                affected_mandates.append(
                    {
                        "mandate_id": mandate_id,
                        "display_name": names.get(mandate_id, mandate_id),
                        "affected_holdings": [h.model_dump() for h in matched],
                    }
                )
        results.append(
            {
                "event": src.model_dump(mode="json"),
                "affected_tickers": tickers,
                "affected_mandate_count": len(affected_mandates),
                "total_mandates": len(mandates),
                "affected_mandates": affected_mandates,
            }
        )
    return results


# Theme/keyword -> the real ETF sleeve (ticker) it maps to. Used to connect a
# free-text web event to the funds the portfolios actually hold.
_EVENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "IXC": ("energy", "oil", "crude", "opec", "brent", "wti", "gas prices", "middle east", "geopolit"),
    "IAU": ("gold", "bullion", "precious metal", "safe haven", "safe-haven"),
    "IEF": ("treasury", "treasuries", "10-year", "10 year", "yield curve", "duration", "rate cut", "rate-cut"),
    "AGG": ("aggregate bond", "bond market", "fixed income", "bond yields", "rate hike"),
    "LQD": ("investment grade", "investment-grade", "corporate bond", "credit spread", "credit market"),
    "IEMG": ("emerging market", "emerging-market", "china", "em equities", "emerging economies"),
    "IJR": ("small cap", "small-cap", "russell 2000"),
    "IEFA": ("international", "eafe", "europe", "eurozone", "japan", "developed market", "overseas"),
    "ESGU": ("esg", "sustainable", "responsible investing"),
    "IVV": ("s&p 500", "s&p500", "sp 500", "large cap", "large-cap", "wall street", "nasdaq", "dow jones"),
}
_BROAD_EQUITY_HINTS = ("stock", "equit", "market", "index", "shares", "earnings")


def _extract_affected_tickers(text: str) -> list[str]:
    """Map free-text event content to the ETF sleeves (tickers) it affects."""
    t = text.lower()
    hits = [ticker for ticker, kws in _EVENT_KEYWORDS.items() if any(kw in t for kw in kws)]
    if not hits and any(w in t for w in _BROAD_EQUITY_HINTS):
        hits.append("IVV")  # broad equity fallback so a market event usually maps
    return hits



def scan(period: str) -> list[dict]:
    """Return candidate events for the period with the mandates they affect.

    Each item: {event: {...}, affected_mandates: [{mandate_id, display_name,
    affected_holdings: [{ticker, instrument, weight}]}]}.
    """
    library = market_context_sources._load_library()
    events = [
        src
        for src in library
        if period in src.periods
        and "event_driven" in src.commentary_types
        and src.affected_tickers
    ]
    if not events:
        return []

    mandates = reference_data.list_mandates()
    # Cache holdings per mandate for this period.
    holdings_by_mandate = {m.mandate_id: reference_data.get_holdings(m.mandate_id, period) for m in mandates}
    mandate_names = {m.mandate_id: m.display_name for m in mandates}

    results: list[dict] = []
    for ev in events:
        affected_mandates: list[dict] = []
        for mandate_id, holdings in holdings_by_mandate.items():
            matched = [
                AffectedHolding(ticker=h.ticker, instrument=h.instrument, weight=h.weight)
                for h in holdings
                if h.ticker in ev.affected_tickers
            ]
            if matched:
                affected_mandates.append(
                    {
                        "mandate_id": mandate_id,
                        "display_name": mandate_names.get(mandate_id, mandate_id),
                        "affected_holdings": [h.model_dump() for h in matched],
                    }
                )
        if affected_mandates:
            results.append(
                {
                    "event": {
                        "source_id": ev.source_id,
                        "publisher": ev.publisher,
                        "title": ev.title,
                        "channel": ev.channel.value,
                        "url": ev.url,
                        "affected_tickers": ev.affected_tickers,
                        "advisor_talking_point": ev.advisor_talking_point,
                    },
                    "affected_mandates": affected_mandates,
                }
            )
    return results
