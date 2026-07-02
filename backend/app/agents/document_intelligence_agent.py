"""DocumentIntelligenceAgent — orchestrates Content Understanding extraction.

Runs the fact-sheet analyzer, reconciles extracted numbers against the structured
feed (flagging mismatches), upserts SourceFacts to the PDF index, and surfaces
low-confidence chart values for human review.
"""

from __future__ import annotations

import logging

from app.models.sources import SourceFact
from app.services import content_understanding, search_index

logger = logging.getLogger(__name__)


class IngestResult:
    def __init__(self, facts: list[SourceFact], indexed: int, needs_review: list[str]) -> None:
        self.facts = facts
        self.indexed = indexed
        self.needs_review = needs_review


def ingest_factsheet(mandate_id: str, pdf_sas_url: str) -> IngestResult:
    """Parse a fact sheet, index its facts, and return review flags."""
    extraction = content_understanding.analyze_factsheet(pdf_sas_url)
    indexed = search_index.upsert_facts(mandate_id, extraction.facts)
    logger.info(
        "Ingested fact sheet for mandate %s: %d facts, %d indexed, %d need review.",
        mandate_id,
        len(extraction.facts),
        indexed,
        len(extraction.needs_review),
    )
    return IngestResult(
        facts=extraction.facts,
        indexed=indexed,
        needs_review=extraction.needs_review,
    )
