"""Market context sources — the real-world artefacts an advisor reads.

Blends LIVE web-grounded context (via Web IQ) with a curated library of ad-hoc
market-event updates (advisor portals, fund webpages, market commentary, PM
notes, webcasts, email alerts, wholesaler notes). Live sources are dynamic; the
curated library carries the structured event bulletins (key points, affected
tickers, advisor talking points) and is the fallback when Web IQ is rate-limited.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.models.context import ContextSource
from app.services import web_iq

logger = logging.getLogger(__name__)

# backend/app/services/market_context_sources.py -> parents[2] == backend/
_LIBRARY_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "context" / "market_context_library.json"
)

# How many sources to surface on a brief, at most.
MAX_SOURCES = 4


@lru_cache(maxsize=1)
def _load_library() -> list[ContextSource]:
    if not _LIBRARY_PATH.exists():
        logger.warning("Context library not found at %s; no context sources.", _LIBRARY_PATH)
        return []
    with _LIBRARY_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return [ContextSource.model_validate(item) for item in payload.get("sources", [])]


def _select_curated(
    period: str, commentary_type: str, themes: list[str] | None, limit: int
) -> list[ContextSource]:
    """Pick the most relevant curated context sources (deterministic)."""
    theme_set = {t.lower() for t in (themes or [])}
    scored: list[tuple[int, ContextSource]] = []
    for src in _load_library():
        score = 0
        if period in src.periods:
            score += 4
        if commentary_type in src.commentary_types:
            score += 2
        score += len(theme_set & {t.lower() for t in src.themes})
        if score > 0:
            scored.append((score, src))

    scored.sort(key=lambda pair: (-pair[0], pair[1].published or "", pair[1].source_id))
    return [src for _, src in scored[:limit]]


async def select_sources(
    period: str,
    commentary_type: str,
    themes: list[str] | None = None,
    limit: int = MAX_SOURCES,
    event_topic: str | None = None,
) -> list[ContextSource]:
    """Select context sources for a brief: live Web IQ blended with curated.

    Live web results are dynamic and current; curated entries carry the
    structured event bulletins. For event-driven briefs the curated bulletins
    lead (they hold the key points / affected tickers / talking point); otherwise
    live web sources lead. Falls back entirely to curated if Web IQ is
    unavailable (e.g. rate-limited).
    """
    curated = _select_curated(period, commentary_type, themes, limit)
    live = await web_iq.get_context_sources(
        period, themes=themes, commentary_type=commentary_type, event_topic=event_topic, limit=limit
    )

    ordered = (curated + live) if commentary_type == "event_driven" else (live + curated)
    merged: list[ContextSource] = []
    seen: set[str] = set()
    for src in ordered:
        key = (src.url or src.source_id).lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(src)
        if len(merged) >= limit:
            break
    return merged


def fetch_live(url: str) -> ContextSource | None:
    """Deprecated single-URL hook — superseded by web_iq.get_context_sources."""
    logger.info("fetch_live is superseded by web_iq.get_context_sources; skipping %s", url)
    return None
