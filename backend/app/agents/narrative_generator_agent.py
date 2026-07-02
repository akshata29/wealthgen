"""NarrativeGeneratorAgent — drafts the 7-section commentary as a grounded JSON contract.

Grounded on Work IQ (house voice). Emits CommentaryDraft JSON where every numeric
claim carries a source_id present in the source map. Downstream substantiation and
compliance gates enforce correctness.
"""

from __future__ import annotations

import json
import logging

from app.agents.prompts import build_narrative_instructions
from app.infra.settings import get_settings
from app.models.analysis import AnalysisFindings
from app.models.commentary import Audience, CommentaryDraft, NarrativeStyle, SectionHeading
from app.models.market import MarketContextFacts
from app.models.sources import SourceFact
from app.services import foundry_iq

logger = logging.getLogger(__name__)

AGENT_NAME = "NarrativeGeneratorAgent"


def _alnum(text: str) -> str:
    """Lowercase alphanumeric-only form, with 'and' dropped, for heading matching."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum()).replace("and", "")


def generate(
    mandate_id: str,
    period: str,
    audience: Audience,
    findings: AnalysisFindings,
    market: MarketContextFacts,
    source_facts: list[SourceFact],
    style: NarrativeStyle | None = None,
    event_driven: bool = False,
) -> CommentaryDraft:
    source_map = {f.source_id: f.label + (f": {f.value}" if f.value else "") for f in source_facts}
    style = style or NarrativeStyle()
    instructions = build_narrative_instructions(
        audience=audience.value,
        tone=style.tone.value,
        literacy=style.literacy.value,
        non_financial_language=style.non_financial_language,
        event_driven=event_driven,
    )
    # In local grounding mode the narrative is written purely from the supplied
    # (already-grounded) facts, so the KB retrieval tool is omitted.
    tools = [] if get_settings().grounding_mode == "local" else None
    agent = foundry_iq.ensure_agent(AGENT_NAME, instructions, tools=tools)

    prompt = json.dumps(
        {
            "mandate_id": mandate_id,
            "period": period,
            "audience": audience.value,
            "analysis": findings.model_dump(mode="json"),
            "market": market.model_dump(mode="json"),
            "source_map": source_map,
            "allowed_source_ids": list(source_map.keys()),
            "rules": [
                "Every claim's source_id MUST be EXACTLY one of allowed_source_ids.",
                "Never invent a source_id and never use 'analysis' or 'market' as a source_id.",
                "Where it aids the reader, name specific top holdings (source ids hold:*) in the "
                "Executive Summary or Performance Attribution.",
                "For qualitative sections (House View & Outlook, Risk & Compliance Note, "
                "Next Steps) cite the house:* source ids.",
            ],
        }
    )
    text, _ = foundry_iq.run_agent(agent, prompt)
    payload = _slice_json(text)
    payload = _normalize_payload(payload)
    payload.setdefault("mandate_id", mandate_id)
    payload.setdefault("period", period)
    payload.setdefault("audience", audience.value)
    payload.setdefault("source_map", source_map)
    _repair_source_ids(payload, source_facts, source_map)
    return CommentaryDraft.model_validate(payload)


def _repair_source_ids(
    payload: dict, source_facts: list[SourceFact], source_map: dict[str, str]
) -> None:
    """Keep the 'no fabricated numbers' guarantee robust for the demo.

    For any claim whose source_id is not in the source_map, try to remap it to a
    fact with a matching value; otherwise drop the claim. This prevents spurious
    422s from the model mislabelling an otherwise-grounded number.
    """
    by_value: dict[str, str] = {}
    for f in source_facts:
        if f.value:
            by_value.setdefault(_norm_value(f.value), f.source_id)

    for section in payload.get("sections", []):
        kept: list[dict] = []
        for claim in section.get("claims", []):
            sid = claim.get("source_id", "")
            if sid in source_map:
                kept.append(claim)
                continue
            value = claim.get("value")
            remapped = by_value.get(_norm_value(value)) if value else None
            if remapped:
                claim["source_id"] = remapped
                kept.append(claim)
            # else: drop the uncited claim
        section["claims"] = kept


def _norm_value(value) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isdigit() or ch in ".-")


def _slice_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("NarrativeGeneratorAgent did not return JSON.")
    return json.loads(text[start : end + 1])


# Canonical SectionHeading values keyed by their alphanumeric-only form so we can
# match model variants like "ExecutiveSummary", "House View and Outlook", etc.
_HEADING_LOOKUP = {_alnum(heading.value): heading.value for heading in SectionHeading}


def _normalize_payload(payload: dict) -> dict:
    """Coerce the model's flexible JSON into the strict CommentaryDraft schema.

    Handles common LLM deviations:
      * a top-level {"CommentaryDraft": {...}} wrapper;
      * heading-named keys (ExecutiveSummary: [...]) instead of a sections array;
      * numeric `value` fields where the schema expects strings.
    """
    # Unwrap a single-key wrapper such as {"CommentaryDraft": {...}}.
    if "sections" not in payload and len(payload) == 1:
        (only_value,) = payload.values()
        if isinstance(only_value, dict):
            payload = only_value

    if isinstance(payload.get("sections"), list):
        payload["sections"] = [_normalize_section(s) for s in payload["sections"]]
        return payload

    # Convert heading-named keys into a sections array.
    sections: list[dict] = []
    for key, value in payload.items():
        heading = _HEADING_LOOKUP.get(_alnum(key))
        if heading and isinstance(value, list):
            sections.append({"heading": heading, "claims": [_normalize_claim(c) for c in value]})
    if sections:
        payload = {"sections": sections}
    return payload


def _normalize_section(section: dict) -> dict:
    heading = section.get("heading")
    canonical = _HEADING_LOOKUP.get(_alnum(str(heading)), heading)
    claims = section.get("claims", [])
    return {"heading": canonical, "claims": [_normalize_claim(c) for c in claims]}


def _normalize_claim(claim: dict) -> dict:
    value = claim.get("value")
    return {
        "text": str(claim.get("text", "")),
        "value": None if value is None else str(value),
        "source_id": str(claim.get("source_id", "")),
        "confidence": claim.get("confidence"),
    }
