"""Portfolio, client, performance, and event models for the advisory workspace.

These mirror the synthetic Fabric IQ tables (see scripts/synthetic/reference.py)
and back the /clients, /mandates, /performance, and /events endpoints. They carry
NO secrets and use demo-safe display names (never real PII).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"


class FinancialLiteracy(str, Enum):
    NOVICE = "novice"
    INFORMED = "informed"
    EXPERT = "expert"


class TonePreference(str, Enum):
    WARM = "warm"
    NEUTRAL = "neutral"
    FORMAL = "formal"


class Client(BaseModel):
    client_id: str
    display_name: str
    advisor_id: str
    jurisdiction: str
    risk_profile: RiskProfile
    financial_literacy: FinancialLiteracy
    tone_preference: TonePreference
    segment: str
    life_event: str | None = None
    esg_preference: bool = False


class Mandate(BaseModel):
    mandate_id: str
    display_name: str
    client_id: str
    strategy: str
    benchmark_id: str
    benchmark_name: str | None = None
    base_currency: str
    inception: str
    aum_musd: float


class ClientSummary(Client):
    """Client plus a lightweight roll-up of their mandates."""

    mandates: list[Mandate] = Field(default_factory=list)
    total_aum_musd: float = 0.0


class PerformanceSummary(BaseModel):
    mandate_id: str
    period: str
    total_return_net_pct: float
    benchmark_return_pct: float
    active_return_bps: float
    tracking_error_pct: float | None = None
    information_ratio: float | None = None
    ex_ante_vol_pct: float | None = None
    sharpe: float | None = None
    max_drawdown_pct: float | None = None


class Holding(BaseModel):
    mandate_id: str
    period: str
    ticker: str
    instrument: str
    isin: str
    asset_class: str
    sector: str
    region: str
    weight: float
    market_value_usd: float
    period_return_pct: float


class AttributionSegment(BaseModel):
    segment: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    allocation_bps: float
    selection_bps: float
    interaction_bps: float
    source_id: str

    @property
    def total_effect_bps(self) -> float:
        return self.allocation_bps + self.selection_bps + self.interaction_bps


class PositioningChange(BaseModel):
    mandate_id: str
    period: str
    description: str
    direction: str
    magnitude: str | None = None
    rationale: str | None = None
    source_id: str


class IndexReturn(BaseModel):
    index_name: str
    period_return_pct: float
    source_id: str


class SectorComparison(BaseModel):
    """Portfolio vs benchmark, per sector, with the Brinson total effect."""

    segment: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    total_effect_bps: float
    source_id: str


class PerformanceReport(BaseModel):
    """Composed report powering the templated performance widgets."""

    mandate: Mandate
    period: str
    summary: PerformanceSummary
    # Benchmark compare
    benchmark_name: str
    # Sector compare (top contributors + detractors)
    top_contributors: list[SectorComparison] = Field(default_factory=list)
    top_detractors: list[SectorComparison] = Field(default_factory=list)
    # Index / ETF compare
    index_returns: list[IndexReturn] = Field(default_factory=list)
    positioning_changes: list[PositioningChange] = Field(default_factory=list)


class VixEvent(BaseModel):
    period: str
    vix_close: float
    event_trigger: bool
    regime: str
    headline: str


class NextBestAction(BaseModel):
    """Compliant, suitability-aware suggestion (always human-gated before delivery)."""

    title: str
    rationale: str
    risk_warning: str
    trigger_type: str = Field(..., description="life_event | market_event")
    source: str
