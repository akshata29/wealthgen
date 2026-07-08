"""PortfolioAnalysisAgent — produces AnalysisFindings for the narrative.

Two grounding modes (see Settings.grounding_mode):
  * local      -> build findings directly from the synthetic dataset (reference_data).
                  Deterministic, reconciled numbers; no LLM/KB call, no fabrication.
  * foundry_iq -> narrate pre-computed attribution retrieved from the Foundry IQ
                  knowledge base (Fabric IQ sources). Requires the KB + RemoteTool
                  connection to be provisioned.
"""

from __future__ import annotations

import logging

from app.models.analysis import (
    AnalysisFindings,
    HoldingRef,
    PositioningChange,
    PositioningDirection,
    SegmentAttribution,
)
from app.services import reference_data

logger = logging.getLogger(__name__)

AGENT_NAME = "PortfolioAnalysisAgent"


def analyze(mandate_id: str, period: str) -> AnalysisFindings:
    # Structured findings always come from the authoritative reference_data
    # (Fabric in DATA_SOURCE_MODE=fabric): the figures must be exact for the
    # substantiation gate. KB/agent grounding is applied during narrative
    # generation (and Morningstar X-Ray as a source), so we skip a slow, fragile
    # LLM extraction here whose output we would only discard.
    return _analyze_local(mandate_id, period)


def _analyze_local(mandate_id: str, period: str) -> AnalysisFindings:
    perf = reference_data.get_performance(mandate_id, period)
    if perf is None:
        raise ValueError(f"No performance data for {mandate_id} / {period}.")

    segments = reference_data.get_attribution(mandate_id, period)
    ranked = sorted(segments, key=lambda s: s.total_effect_bps, reverse=True)
    contributors = [_to_segment(s) for s in ranked[:3] if s.total_effect_bps > 0]
    detractors = [_to_segment(s) for s in reversed(ranked[-3:]) if s.total_effect_bps < 0]

    positioning = [
        PositioningChange(
            description=p.description,
            direction=_direction(p.direction),
            magnitude=p.magnitude,
            rationale=p.rationale,
            source_id=p.source_id,
        )
        for p in reference_data.get_positioning(mandate_id, period)
    ]

    holdings = reference_data.get_holdings(mandate_id, period)
    top_holdings = [
        HoldingRef(
            instrument=h.instrument,
            ticker=h.ticker,
            sector=h.sector,
            weight=h.weight,
            source_id=f"hold:{h.ticker.lower()}",
        )
        for h in sorted(holdings, key=lambda x: x.weight, reverse=True)[:5]
    ]

    return AnalysisFindings(
        mandate_id=mandate_id,
        period=period,
        total_return_net=perf.total_return_net_pct,
        benchmark_return=perf.benchmark_return_pct,
        active_return_bps=perf.active_return_bps,
        tracking_error=perf.tracking_error_pct,
        ex_ante_vol=perf.ex_ante_vol_pct,
        top_contributors=contributors,
        top_detractors=detractors,
        top_holdings=top_holdings,
        positioning_changes=positioning,
    )


def _to_segment(s) -> SegmentAttribution:
    return SegmentAttribution(
        segment=s.segment,
        portfolio_weight=s.portfolio_weight,
        benchmark_weight=s.benchmark_weight,
        portfolio_return=s.portfolio_return,
        benchmark_return=s.benchmark_return,
        allocation_bps=s.allocation_bps,
        selection_bps=s.selection_bps,
        interaction_bps=s.interaction_bps,
        source_id=s.source_id,
    )


def _direction(value: str) -> PositioningDirection:
    try:
        return PositioningDirection(value)
    except ValueError:
        return PositioningDirection.ADD
