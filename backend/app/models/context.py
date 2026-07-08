"""Real-world market context sources.

Large asset managers publish ad-hoc market-event updates alongside formal fund
facts and regulatory disclosures. These arrive through advisor portals, fund
webpages, market-commentary sections, webcasts, email alerts, and wholesaler
communications. `ContextSource` models one such artefact so the narrative can
cite the same channels an advisor reads in real life.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ContextChannel(str, Enum):
    ADVISOR_PORTAL = "advisor_portal"
    FUND_WEBPAGE = "fund_webpage"
    MARKET_COMMENTARY = "market_commentary"
    PORTFOLIO_MANAGER = "portfolio_manager"
    RESEARCH = "research"
    WEBCAST = "webcast"
    EMAIL_ALERT = "email_alert"
    WHOLESALER = "wholesaler"


class AffectedHolding(BaseModel):
    """A portfolio holding the event/context source directly affects."""

    ticker: str
    instrument: str
    weight: float = Field(..., description="Portfolio weight as a fraction (0-1)")


class ContextSource(BaseModel):
    """A citeable piece of real-world market context (curated or live-fetched)."""

    source_id: str = Field(..., description="Stable id, e.g. 'ctx:blackrock:weekly-2026q1'")
    channel: ContextChannel
    publisher: str = Field(..., description="e.g. 'BlackRock', 'J.P. Morgan Asset Management'")
    title: str
    summary: str = Field(..., description="Curated excerpt the narrative may cite")
    url: str | None = None
    published: str | None = Field(None, description="ISO date, e.g. '2026-01-15'")
    periods: list[str] = Field(
        default_factory=list, description="Reporting periods this applies to, e.g. ['Q1-2026']"
    )
    themes: list[str] = Field(
        default_factory=list, description="Theme tags, e.g. ['rates', 'volatility']"
    )
    commentary_types: list[str] = Field(
        default_factory=list,
        description="Commentary types this suits, e.g. ['event_driven', 'quarterly_review']",
    )
    live: bool = Field(False, description="True if fetched live rather than from the seeded library")

    # Optional event-bulletin structure (used for market-event updates), mirroring
    # how asset managers publish: what happened, why it matters, which holdings are
    # affected, and a compliant advisor talking point.
    key_points: list[str] = Field(
        default_factory=list, description="Bulleted 'what happened / why it matters' points"
    )
    affected_tickers: list[str] = Field(
        default_factory=list, description="Fund/holding tickers the event most affects"
    )
    advisor_talking_point: str | None = Field(
        None, description="Compliant, non-advice talking point for client conversations"
    )
    affected_holdings: list[AffectedHolding] = Field(
        default_factory=list,
        description="Cross-referenced actual portfolio holdings the source affects (set at generation)",
    )
