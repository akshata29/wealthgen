"""Commentary generation pipeline orchestration.

analysis (Fabric IQ) + market (Web IQ + LSEG) -> narrative (Work IQ voice)
-> substantiation gate -> compliance gate -> persisted CompliantCommentary.
"""

from __future__ import annotations

import logging

from app.agents import (
    compliance_guard_agent,
    market_intelligence_agent,
    narrative_generator_agent,
    portfolio_analysis_agent,
)
from app.models.commentary import Audience, CompliantCommentary, NarrativeStyle
from app.models.sources import SourceFact, SourceOrigin
from app.services import substantiation

logger = logging.getLogger(__name__)


class SubstantiationError(ValueError):
    """Raised when generated claims reference unresolved sources."""

    def __init__(self, unresolved: list[str]) -> None:
        self.unresolved = unresolved
        super().__init__(f"Unresolved source ids: {unresolved}")


async def generate_commentary(
    mandate_id: str,
    period: str,
    audience: Audience,
    jurisdictions: list[str],
    style: NarrativeStyle | None = None,
    event_driven: bool = False,
) -> CompliantCommentary:
    findings = portfolio_analysis_agent.analyze(mandate_id, period)
    market = await market_intelligence_agent.build_context(period)

    source_facts = _collect_source_facts(findings, market)
    draft = narrative_generator_agent.generate(
        mandate_id, period, audience, findings, market, source_facts,
        style=style, event_driven=event_driven,
    )

    unresolved = substantiation.substantiate(draft)
    if unresolved:
        raise SubstantiationError(unresolved)

    return compliance_guard_agent.enforce(draft, jurisdictions)


def _collect_source_facts(findings, market) -> list[SourceFact]:
    """Assemble the source facts underpinning the narrative for the source map."""
    facts: list[SourceFact] = [
        SourceFact(
            source_id="perf:total_return",
            origin=SourceOrigin.FABRIC_IQ,
            label="Total return (net)",
            value=f"{findings.total_return_net:+.2f}%",
        ),
        SourceFact(
            source_id="perf:benchmark_return",
            origin=SourceOrigin.FABRIC_IQ,
            label="Benchmark return",
            value=f"{findings.benchmark_return:+.2f}%",
        ),
        SourceFact(
            source_id="perf:active_return",
            origin=SourceOrigin.FABRIC_IQ,
            label="Active return",
            value=f"{findings.active_return_bps:+.0f} bps",
        ),
    ]
    for seg in [*findings.top_contributors, *findings.top_detractors]:
        facts.append(
            SourceFact(
                source_id=seg.source_id,
                origin=SourceOrigin.FABRIC_IQ,
                label=f"{seg.segment} attribution",
                value=f"alloc {seg.allocation_bps:+.0f} / sel {seg.selection_bps:+.0f} bps",
            )
        )
    for change in findings.positioning_changes:
        facts.append(
            SourceFact(
                source_id=change.source_id,
                origin=SourceOrigin.FABRIC_IQ,
                label="Positioning change",
                value=change.description,
            )
        )
    for h in getattr(findings, "top_holdings", []):
        facts.append(
            SourceFact(
                source_id=h.source_id,
                origin=SourceOrigin.FABRIC_IQ,
                label=f"Top holding {h.instrument} ({h.ticker})",
                value=f"{h.weight * 100:.1f}%",
            )
        )
    for idx in market.index_returns:
        facts.append(
            SourceFact(
                source_id=idx.source_id,
                origin=SourceOrigin.LSEG,
                label=idx.name,
                value=f"{idx.period_return:+.1f}%",
            )
        )
    for fx in market.fx_moves:
        facts.append(
            SourceFact(
                source_id=fx.source_id,
                origin=SourceOrigin.LSEG,
                label=fx.pair,
                value=f"{fx.change_pct:+.1f}%",
            )
        )
    # House (Work IQ) sources so qualitative sections can be cited.
    facts.extend(
        [
            SourceFact(source_id="house:view", origin=SourceOrigin.WORK_IQ, label="House view & outlook"),
            SourceFact(source_id="house:risk", origin=SourceOrigin.WORK_IQ, label="Risk & compliance guidance"),
            SourceFact(source_id="house:next", origin=SourceOrigin.WORK_IQ, label="Next steps guidance"),
        ]
    )
    return facts
