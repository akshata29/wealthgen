"""Web IQ — live web grounding for the 'Market Context' section.

Used for market/macro context only — never client data. Two roles:

1. Registered as a Web knowledge source on the Foundry IQ knowledge base.
2. Direct REST calls to the Microsoft Web IQ v3 search API (POST /v3/search/web
   with an `x-apikey` header) to fetch live market themes for a reporting period.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from urllib.parse import urlparse

import httpx

from app.infra.clients import get_search_index_client
from app.infra.settings import get_settings
from app.models.context import ContextChannel, ContextSource

logger = logging.getLogger(__name__)

SOURCE_NAME = "wealthgen-web-iq"

# Documented Web IQ v3 REST search endpoint.
_DEFAULT_SEARCH_URL = "https://api.microsoft.ai/v3/search/web"

# Retry only transient SERVER errors. We deliberately do NOT retry 429: the key's
# throttle window is long (retryAfter ~60s), so retrying just burns quota — we
# fail fast and let callers fall back to cached/curated context.
_RETRY_STATUS = {500, 502, 503, 504}
_MAX_ATTEMPTS = 3
_BASE_BACKOFF = 1.0  # seconds; exponential with jitter, capped

# Short-lived response cache so a single generate + the live scan + repeat
# generations don't each hit the (rate-limited) API. Keyed by request body.
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 600.0  # seconds

# Known publisher domains -> display names.
_PUBLISHERS = {
    "blackrock.com": "BlackRock",
    "ishares.com": "iShares by BlackRock",
    "jpmorgan.com": "J.P. Morgan Asset Management",
    "fidelity.com": "Fidelity",
    "fidelity.ca": "Fidelity",
    "pimco.com": "PIMCO",
    "ssga.com": "State Street Global Advisors",
    "vanguard.com": "Vanguard",
    "schwab.com": "Charles Schwab",
    "morningstar.com": "Morningstar",
}


class WebIqConfigError(RuntimeError):
    """Raised when the Web IQ API key is not configured."""


def _search_url() -> str:
    """Normalise the configured Web IQ URL to the REST v3 search endpoint.

    Accepts either the MCP path (`.../v3/mcp`) or a base and returns the
    documented `.../v3/search/web` endpoint.
    """
    url = (get_settings().webiq_mcp_url or "").strip().rstrip("/")
    if not url:
        return _DEFAULT_SEARCH_URL
    if url.endswith("/search/web"):
        return url
    if url.endswith("/mcp"):
        return url[: -len("/mcp")] + "/search/web"
    return url + "/search/web"


async def _post_with_retry(body: dict, headers: dict) -> httpx.Response:
    """POST to Web IQ, retrying only transient 5xx (not 429 — see _RETRY_STATUS)."""
    url = _search_url()
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code not in _RETRY_STATUS:
                resp.raise_for_status()  # 429 raises here -> caller falls back
                return resp
            last_exc = httpx.HTTPStatusError(
                f"Web IQ {resp.status_code}", request=resp.request, response=resp
            )
            if attempt == _MAX_ATTEMPTS:
                break
            delay = min(_BASE_BACKOFF * (2 ** (attempt - 1)), 6.0) + random.uniform(0, 0.3)
            logger.warning(
                "Web IQ %s (attempt %d/%d); retrying in %.1fs.",
                resp.status_code, attempt, _MAX_ATTEMPTS, delay,
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc


async def search(
    query: str, *, max_results: int = 5, content_format: str = "passage", max_length: int = 600
) -> list[dict]:
    """Run a Web IQ web search (with retry). Returns the raw `webResults` list.

    Raises WebIqConfigError if no API key is set; propagates HTTP errors after
    retries are exhausted for the caller to handle/fall back.
    """
    settings = get_settings()
    if not settings.webiq_mcp_key:
        raise WebIqConfigError("WEBIQ_MCP_KEY is not configured; set it in .env.")

    body = {
        "query": query[:1000],
        "maxResults": max_results,
        "contentFormat": content_format,
        "maxLength": max_length,
    }
    cache_key = json.dumps(body, sort_keys=True)
    cached = _CACHE.get(cache_key)
    if cached is not None and time.time() - cached[0] < _CACHE_TTL:
        logger.debug("Web IQ cache hit for query %r", query[:60])
        return cached[1]

    headers = {"x-apikey": settings.webiq_mcp_key, "content-type": "application/json"}
    resp = await _post_with_retry(body, headers)
    results = resp.json().get("webResults", []) or []
    _CACHE[cache_key] = (time.time(), results)
    return results


def _publisher_for(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    for domain, name in _PUBLISHERS.items():
        if host == domain or host.endswith("." + domain):
            return name
    root = host.split(".")[-2] if host.count(".") >= 1 else host
    return root.capitalize() or "Web"


def _channel_for(url: str) -> ContextChannel:
    u = url.lower()
    if any(k in u for k in ("/events", "webcast", "webinar", "conference-call")):
        return ContextChannel.WEBCAST
    if any(k in u for k in ("fact-sheet", "/funds", "/products", "/etf")):
        return ContextChannel.FUND_WEBPAGE
    if any(k in u for k in ("cio", "portfolio-manager", "manager-commentary", "perspective")):
        return ContextChannel.PORTFOLIO_MANAGER
    if "advisor" in u or "/adv/" in u:
        return ContextChannel.ADVISOR_PORTAL
    return ContextChannel.MARKET_COMMENTARY


async def get_context_sources(
    period: str,
    themes: list[str] | None = None,
    commentary_type: str = "quarterly_review",
    event_topic: str | None = None,
    limit: int = 4,
) -> list[ContextSource]:
    """Fetch LIVE market-context sources from the web via Web IQ.

    Builds a query from the period/themes (or an explicit event topic) and maps
    each web result to a citeable `ContextSource` (channel inferred from the URL,
    publisher from the domain). Returns [] on rate-limit/config/error so callers
    can fall back to the curated library.
    """
    theme_str = " ".join((themes or [])[:4])
    if event_topic:
        query = (
            f"{event_topic} market impact and portfolio implications — advisor commentary {period}"
        )
    else:
        query = (
            f"asset manager market commentary and outlook for financial advisors {period} "
            f"{theme_str}"
        ).strip()

    try:
        results = await search(query, max_results=limit + 2, content_format="passage", max_length=500)
    except (WebIqConfigError, httpx.HTTPError) as exc:
        logger.warning("Web IQ context fetch unavailable (%s); using curated library.", exc)
        return []
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        logger.warning("Web IQ context fetch error (%s); using curated library.", exc)
        return []

    sources: list[ContextSource] = []
    for i, item in enumerate(results[:limit]):
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        content = (item.get("content") or "").strip()
        if not (url and title):
            continue
        sources.append(
            ContextSource(
                source_id=f"ctx:live:{period.lower()}:{i}",
                channel=_channel_for(url),
                publisher=_publisher_for(url),
                title=title,
                summary=content[:500] or title,
                url=url,
                published=item.get("lastUpdatedAt") or item.get("crawledAt"),
                periods=[period],
                themes=themes or [],
                commentary_types=[commentary_type],
                live=True,
            )
        )
    return sources


async def get_market_themes(period: str, limit: int = 5) -> list[str]:
    """Fetch live, web-grounded market themes for the reporting period.

    Returns a list of concise theme strings sourced from Web IQ result titles.
    Returns an empty list (rather than raising) if Web IQ is unavailable so the
    caller can fall back to reference-data themes.
    """
    query = (
        f"global markets outlook {period}: dominant themes across equities, rates, "
        "credit, and commodities"
    )
    try:
        results = await search(query, max_results=limit, content_format="passage")
    except (WebIqConfigError, httpx.HTTPError) as exc:
        logger.warning("Web IQ themes unavailable (%s); no live themes.", exc)
        return []
    except Exception as exc:  # noqa: BLE001 — network/parse; degrade gracefully
        logger.warning("Web IQ search error (%s); no live themes.", exc)
        return []

    themes: list[str] = []
    for item in results:
        title = (item.get("title") or "").strip()
        if title:
            themes.append(title)
    return themes[:limit]


def register_source() -> str:
    """Register the Web knowledge source (GA generic Web / Web IQ MCP)."""
    from azure.search.documents.indexes.models import WebKnowledgeSource

    client = get_search_index_client()
    ks = WebKnowledgeSource(
        name=SOURCE_NAME,
        description="Live web grounding for market and macro context.",
    )
    client.create_or_update_knowledge_source(knowledge_source=ks)
    logger.info("Registered Web IQ source '%s'.", SOURCE_NAME)
    return SOURCE_NAME
