"""Market context facts for the 'Market Context' commentary section.

Sourced from Web IQ (themes) and LSEG (index returns, FX). Contains NO client
data — market/macro grounding only.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.context import ContextSource


class IndexReturn(BaseModel):
    name: str = Field(..., description="e.g. 'Developed market equities'")
    period_return: float = Field(..., description="Period return as a percentage")
    source_id: str


class FxMove(BaseModel):
    pair: str = Field(..., description="e.g. 'GBP/USD'")
    change_pct: float
    source_id: str


class MarketContextFacts(BaseModel):
    period: str
    themes: list[str] = Field(default_factory=list)
    index_returns: list[IndexReturn] = Field(default_factory=list)
    fx_moves: list[FxMove] = Field(default_factory=list)
    context_sources: list[ContextSource] = Field(
        default_factory=list, description="Real-world market context (portals, commentary, alerts)"
    )
