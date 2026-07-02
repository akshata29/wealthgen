"""PortfolioAnalysisAgent — produces AnalysisFindings for the narrative.

Two grounding modes (see Settings.grounding_mode):
  * local      -> build findings directly from the synthetic dataset (reference_data).
                  Deterministic, reconciled numbers; no LLM/KB call, no fabrication.
  * foundry_iq -> narrate pre-computed attribution retrieved from the Foundry IQ
                  knowledge base (Fabric IQ sources). Requires the KB + RemoteTool
                  connection to be provisioned.
"""

from __future__ import annotations

import json
import logging

from app.agents.prompts import ANALYSIS_SYSTEM
from app.infra.settings import get_settings
from app.models.analysis import (
    AnalysisFindings,
    HoldingRef,
    PositioningChange,
    PositioningDirection,
    SegmentAttribution,
)
from app.services import foundry_iq, reference_data

logger = logging.getLogger(__name__)

AGENT_NAME = "PortfolioAnalysisAgent"


def analyze(mandate_id: str, period: str) -> AnalysisFindings:
    if get_settings().grounding_mode == "local":
        return _analyze_local(mandate_id, period)
    return _analyze_foundry_iq(mandate_id, period)


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


def _analyze_foundry_iq(mandate_id: str, period: str) -> AnalysisFindings:
    agent = foundry_iq.ensure_agent(AGENT_NAME, ANALYSIS_SYSTEM)
    prompt = (
        f"Summarise attribution for mandate '{mandate_id}', period '{period}'. "
        "Use the knowledge base (Fabric IQ) for holdings, weights, and Brinson-Fachler "
        "attribution. Return AnalysisFindings JSON only."
    )
    text, _ = foundry_iq.run_agent(agent, prompt)
    payload = _slice_json(text)
    return AnalysisFindings.model_validate(payload)


def _slice_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("PortfolioAnalysisAgent did not return JSON.")
    return json.loads(text[start : end + 1])
