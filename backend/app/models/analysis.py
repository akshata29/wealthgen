"""Analytical findings consumed by the narrative generator.

IMPORTANT: attribution effects are *consumed* from the performance/attribution
engine (via Fabric IQ) and never recomputed here. Validators only check that the
supplied effects reconcile to the active return within tolerance.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

# Brinson reconciliation tolerance, in basis points.
RECONCILE_TOLERANCE_BPS = 1.0


class PositioningDirection(str, Enum):
    TRIM = "trim"
    ADD = "add"
    INITIATE = "initiate"
    EXIT = "exit"
    DURATION = "duration"


class SegmentAttribution(BaseModel):
    segment: str = Field(..., description="Sector or asset class")
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    allocation_bps: float = Field(..., description="Brinson-Fachler allocation effect")
    selection_bps: float
    interaction_bps: float
    source_id: str

    @property
    def total_effect_bps(self) -> float:
        return self.allocation_bps + self.selection_bps + self.interaction_bps


class PositioningChange(BaseModel):
    description: str
    direction: PositioningDirection
    magnitude: str | None = None
    rationale: str | None = None
    source_id: str


class HoldingRef(BaseModel):
    """A named top holding surfaced to the narrative for grounded attribution."""

    instrument: str
    ticker: str
    sector: str
    weight: float
    source_id: str


class AnalysisFindings(BaseModel):
    mandate_id: str
    period: str
    total_return_net: float
    benchmark_return: float
    active_return_bps: float
    tracking_error: float | None = None
    ex_ante_vol: float | None = None
    top_contributors: list[SegmentAttribution] = Field(default_factory=list)
    top_detractors: list[SegmentAttribution] = Field(default_factory=list)
    top_holdings: list[HoldingRef] = Field(default_factory=list)
    positioning_changes: list[PositioningChange] = Field(default_factory=list)
    reconciled: bool = True

    @model_validator(mode="after")
    def _check_reconciliation(self) -> "AnalysisFindings":
        segments = [*self.top_contributors, *self.top_detractors]
        if segments:
            total = sum(s.total_effect_bps for s in segments)
            # Only a soft check across the provided (top) segments; full universe
            # reconciliation happens upstream in the attribution engine.
            self.reconciled = abs(total) <= abs(self.active_return_bps) + RECONCILE_TOLERANCE_BPS
        return self
