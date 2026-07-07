"""ResearchAgent — third-party research/ratings via provider MCP servers.

Headless (OAuth refresh-token) path: providers (Morningstar, LSEG) are called
directly over their MCP endpoints using an access token minted from a stored
refresh token (one-time login via scripts/mcp_login.py). The Foundry LLM
orchestrates which MCP tools to call; execution happens in research_direct.

A provider is "configured" once its one-time login has been completed.
"""

from __future__ import annotations

import logging

from app.models.sources import Citation
from app.services import mcp_oauth, reference_data, research_direct

logger = logging.getLogger(__name__)

PROVIDERS = ["morningstar", "lseg", "moody"]


class ResearchNotConfiguredError(RuntimeError):
    """Raised when no research provider has completed its one-time OAuth login."""


def configured_providers() -> list[str]:
    """Providers whose one-time OAuth login has been completed."""
    return [p for p in PROVIDERS if mcp_oauth.has_login(p)]


def _require_login(provider: str) -> None:
    if not mcp_oauth.has_login(provider):
        raise ResearchNotConfiguredError(
            f"'{provider}' is not logged in. Run: python -m scripts.mcp_login {provider}"
        )


async def research(query: str, provider: str | None = None) -> tuple[str, list[Citation]]:
    """Free-form research answered from a provider's MCP tools."""
    available = configured_providers()
    if not available:
        raise ResearchNotConfiguredError(
            "No research provider logged in. Run: python -m scripts.mcp_login morningstar"
        )
    provider = provider or available[0]
    _require_login(provider)
    return await research_direct.run(provider, query)


async def portfolio_xray(mandate_id: str, period: str | None = None) -> tuple[str, list[Citation]]:
    """Run a Morningstar X-Ray-style analysis on the mandate's current holdings."""
    _require_login("morningstar")
    period = period or reference_data.latest_period()
    holdings = reference_data.get_holdings(mandate_id, period)
    if not holdings:
        raise ValueError(f"No holdings for {mandate_id} / {period}.")

    lines = [
        f"{h.instrument} | ticker {h.ticker} | ISIN {h.isin} | {h.asset_class} | "
        f"weight {h.weight * 100:.1f}%"
        for h in holdings
    ]
    prompt = (
        "Run a Morningstar X-Ray on the holdings below.\n"
        "Steps: (1) use the id-lookup tool to resolve each holding by ISIN or ticker; "
        "(2) if some cannot be resolved (e.g. cash, direct government/corporate bonds, or "
        "commodities like gold), EXCLUDE them, renormalise the remaining weights to sum to "
        "100%, and CONTINUE — do NOT abort or return an error; (3) run the portfolio X-Ray on "
        "the resolvable set and summarise asset allocation, sector exposure, geographic region, "
        "investment style, and risk/return; (4) flag concentration or style risks; (5) explicitly "
        "list any holdings you excluded and why. Attribute figures to Morningstar.\n\n"
        f"Mandate: {mandate_id} | Period: {period}\nHoldings:\n" + "\n".join(lines)
    )
    return await research_direct.run("morningstar", prompt)


async def lseg_market_context(mandate_id: str, period: str | None = None) -> tuple[str, list[Citation]]:
    """Assemble market context (indices, curve, FX, themes) via LSEG tools."""
    _require_login("lseg")
    period = period or reference_data.latest_period()
    mandate = reference_data.get_mandate(mandate_id)
    benchmark = mandate.benchmark_name if mandate else ""
    holdings = reference_data.get_holdings(mandate_id, period)
    sectors = ", ".join(sorted({h.sector for h in holdings})) or "multi-asset"

    prompt = (
        "Using the LSEG tools, give a concise market context for the reporting period "
        f"'{period}' relevant to a multi-asset mandate benchmarked to {benchmark}. Cover: major "
        "equity index total returns, government bond yield-curve moves (2y and 10y), key FX moves "
        "(GBP/USD, EUR/USD), and notable macro themes. Portfolio sectors in focus: "
        f"{sectors}. Attribute all figures to LSEG."
    )
    return await research_direct.run("lseg", prompt)


async def moody_credit_context(mandate_id: str, period: str | None = None) -> tuple[str, list[Citation]]:
    """Assemble credit-rating / credit-risk context via Moody's tools."""
    _require_login("moody")
    period = period or reference_data.latest_period()
    mandate = reference_data.get_mandate(mandate_id)
    benchmark = mandate.benchmark_name if mandate else ""
    holdings = reference_data.get_holdings(mandate_id, period)
    names = ", ".join(sorted({h.instrument for h in holdings})[:20]) or "the portfolio holdings"

    prompt = (
        "Using the Moody's tools, give a concise credit-risk context for the reporting period "
        f"'{period}' relevant to a mandate benchmarked to {benchmark}. Cover: issuer credit "
        "ratings and any recent rating actions or outlook changes, sector credit trends, and "
        "notable credit events relevant to these holdings: "
        f"{names}. Attribute all ratings and figures to Moody's."
    )
    return await research_direct.run("moody", prompt)

