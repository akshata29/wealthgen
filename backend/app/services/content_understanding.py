"""Azure AI Content Understanding — primary PDF path.

A custom analyzer extracts, from a fund fact sheet / manager commentary PDF:
  - the attribution table (Table field),
  - chart / figure values (Generate/Classify),
  - fund metrics (Extract),
each with a confidence score and source region. Fields below `CONFIDENCE_THRESHOLD`
are flagged for human review (never silently used).
"""

from __future__ import annotations

import logging

from app.infra.clients import get_content_understanding_client
from app.infra.settings import get_settings
from app.models.sources import SourceFact, SourceOrigin

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7


class FactSheetExtraction:
    def __init__(self, facts: list[SourceFact], needs_review: list[str]) -> None:
        self.facts = facts
        self.needs_review = needs_review


def analyze_factsheet(pdf_sas_url: str) -> FactSheetExtraction:
    """Run the custom fact-sheet analyzer on a URL source and map fields to SourceFacts."""
    from azure.ai.contentunderstanding.models import AnalysisInput

    settings = get_settings()
    client = get_content_understanding_client()
    poller = client.begin_analyze(
        analyzer_id=settings.cu_analyzer_id,
        inputs=[AnalysisInput(url=pdf_sas_url)],
    )
    result = poller.result()
    return _map_result(result)


def analyze_factsheet_bytes(data: bytes) -> FactSheetExtraction:
    """Run the custom fact-sheet analyzer on raw PDF bytes (no blob/SAS needed)."""
    settings = get_settings()
    client = get_content_understanding_client()
    poller = client.begin_analyze_binary(settings.cu_analyzer_id, data)
    result = poller.result()
    return _map_result(result)


def _map_result(result) -> FactSheetExtraction:
    facts: list[SourceFact] = []
    needs_review: list[str] = []

    # New CU SDK returns `contents: [{ fields: {...} }]`; older shape exposed `fields`.
    contents = getattr(result, "contents", None)
    field_maps = (
        [getattr(c, "fields", {}) or {} for c in contents]
        if contents
        else [getattr(result, "fields", {}) or {}]
    )

    for fields in field_maps:
        for name, field in fields.items():
            value = _field_value(field)
            if value is None:
                continue
            confidence = getattr(field, "confidence", None)
            region = _field_region(field)
            source_id = f"cu:{name}"
            facts.append(
                SourceFact(
                    source_id=source_id,
                    origin=SourceOrigin.CONTENT_UNDERSTANDING,
                    label=name,
                    value=str(value),
                    confidence=confidence,
                    region=region,
                )
            )
            if confidence is not None and confidence < CONFIDENCE_THRESHOLD:
                needs_review.append(source_id)

    logger.info(
        "Content Understanding extracted %d fields (%d need review).",
        len(facts),
        len(needs_review),
    )
    return FactSheetExtraction(facts=facts, needs_review=needs_review)


def _field_value(field) -> object | None:
    for attr in ("value_string", "value_number", "value_integer", "value", "content"):
        v = getattr(field, attr, None)
        if v is not None:
            return v
    return None


def _field_region(field) -> str | None:
    source = getattr(field, "source", None)
    if source is None:
        return None
    return str(source)
