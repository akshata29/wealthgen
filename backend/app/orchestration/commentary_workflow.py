"""Commentary generation pipeline orchestration.

analysis (Fabric IQ) + market (Web IQ + LSEG) -> narrative (Work IQ voice)
-> substantiation gate -> compliance gate -> persisted CompliantCommentary.
"""

from __future__ import annotations

import asyncio
import logging
import time

from app.agents import (
    compliance_guard_agent,
    market_intelligence_agent,
    narrative_generator_agent,
    portfolio_analysis_agent,
    research_agent,
)
from app.infra.settings import get_settings
from app.models.commentary import Audience, CommentaryType, CompliantCommentary, NarrativeStyle
from app.models.context import AffectedHolding, ContextChannel, ContextSource
from app.models.sources import SourceFact, SourceOrigin
from app.services import reference_data, substantiation

logger = logging.getLogger(__name__)

# Short-lived cache for the (slow) Morningstar X-Ray, keyed by (mandate, period),
# so repeat generations of the same brief don't re-run the provider call.
_XRAY_CACHE: dict[tuple[str, str], tuple[float, ContextSource]] = {}
_XRAY_TTL = 900.0  # seconds


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
    commentary_type: CommentaryType = CommentaryType.QUARTERLY_REVIEW,
) -> CompliantCommentary:
    findings = portfolio_analysis_agent.analyze(mandate_id, period)

    # Market context (Web IQ) and the Morningstar X-Ray (MCP) are independent —
    # run them concurrently so the slow provider call overlaps the rest.
    market, research_source = await asyncio.gather(
        market_intelligence_agent.build_context(period, commentary_type.value),
        _fetch_research_xray(mandate_id, period),
    )
    if research_source is not None:
        market.context_sources.insert(0, research_source)

    # Cross-reference every context source's affected tickers against the client's
    # ACTUAL holdings so the narrative can name the specific affected positions and
    # weights (never generic). This is the "which holdings are affected" link.
    holdings = reference_data.get_holdings(mandate_id, period)
    _cross_reference_holdings(market.context_sources, holdings)

    source_facts = _collect_source_facts(findings, market)
    source_facts.extend(_affected_holding_facts(market.context_sources))
    draft = narrative_generator_agent.generate(
        mandate_id, period, audience, findings, market, source_facts,
        style=style, event_driven=event_driven, commentary_type=commentary_type,
    )
    # Carry the commentary type and the real-world context the brief drew on.
    draft.commentary_type = commentary_type
    draft.context_sources = market.context_sources

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
    # Real-world market context (portals, commentary, alerts) so Market Context and
    # House View sections can cite the same artefacts an advisor reads.
    for src in market.context_sources:
        origin = (
            SourceOrigin.MORNINGSTAR
            if src.channel == ContextChannel.RESEARCH
            else SourceOrigin.WEB_IQ
        )
        facts.append(
            SourceFact(
                source_id=src.source_id,
                origin=origin,
                label=f"{src.publisher} — {src.title}",
                value=src.summary,
            )
        )
    return facts


async def _fetch_research_xray(mandate_id: str, period: str) -> ContextSource | None:
    """Best-effort Morningstar X-Ray (via MCP) as a citeable context source.

    Runs headlessly using the stored OAuth refresh token. Returns None (never
    raises) when research grounding is disabled, the provider isn't logged in, or
    the call errors/times out — so generation is never blocked by the provider.
    """
    if not get_settings().include_research_grounding:
        return None

    cache_key = (mandate_id, period)
    cached = _XRAY_CACHE.get(cache_key)
    if cached is not None and time.time() - cached[0] < _XRAY_TTL:
        return cached[1]

    try:
        answer, _ = await asyncio.wait_for(
            research_agent.portfolio_xray(mandate_id, period), timeout=60
        )
    except research_agent.ResearchNotConfiguredError:
        logger.info("Morningstar not logged in; skipping X-Ray grounding.")
        return None
    except (TimeoutError, asyncio.TimeoutError):
        logger.warning("Morningstar X-Ray timed out; skipping.")
        return None
    except Exception as exc:  # noqa: BLE001 — provider optional; never block generation
        logger.warning("Morningstar X-Ray unavailable (%s); skipping.", exc)
        return None

    if not (answer and answer.strip()):
        return None
    source = ContextSource(
        source_id="ctx:morningstar:xray",
        channel=ContextChannel.RESEARCH,
        publisher="Morningstar",
        title="Independent portfolio X-Ray (via MCP)",
        summary=answer.strip()[:1200],
        periods=[period],
        themes=["independent-research", "allocation", "risk"],
        commentary_types=[],
        live=True,
    )
    _XRAY_CACHE[cache_key] = (time.time(), source)
    return source


def _cross_reference_holdings(
    sources: list[ContextSource], holdings: list
) -> None:
    """Attach the client's actual affected holdings to each context source.

    Matches each source's `affected_tickers` against the mandate's holdings so the
    brief can name specific positions and weights instead of generic commentary.
    """
    by_ticker = {h.ticker: h for h in holdings}
    for src in sources:
        matched: list[AffectedHolding] = []
        for ticker in src.affected_tickers:
            holding = by_ticker.get(ticker)
            if holding is not None:
                matched.append(
                    AffectedHolding(
                        ticker=holding.ticker,
                        instrument=holding.instrument,
                        weight=holding.weight,
                    )
                )
        src.affected_holdings = matched


def _affected_holding_facts(sources: list[ContextSource]) -> list[SourceFact]:
    """Citeable facts for each affected holding (weight), so claims tie to numbers."""
    facts: list[SourceFact] = []
    seen: set[str] = set()
    for src in sources:
        for holding in src.affected_holdings:
            source_id = f"hold:{holding.ticker.lower()}"
            if source_id in seen:
                continue
            seen.add(source_id)
            facts.append(
                SourceFact(
                    source_id=source_id,
                    origin=SourceOrigin.FABRIC_IQ,
                    label=f"{holding.instrument} ({holding.ticker}) portfolio weight",
                    value=f"{holding.weight * 100:.1f}%",
                )
            )
    return facts
