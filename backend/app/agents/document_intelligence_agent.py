"""DocumentIntelligenceAgent — orchestrates the live PDF ingestion pipeline.

Runs Document Intelligence layout -> Markdown -> chunks and Content Understanding
-> SourceFacts, indexing both into the search index. Surfaces low-confidence
fields for human review.
"""

from __future__ import annotations

import logging

from app.services import ingestion
from app.services.ingestion import IngestResult

logger = logging.getLogger(__name__)


def ingest_factsheet(mandate_id: str, source_name: str, data: bytes) -> IngestResult:
    """Ingest a fact sheet's bytes: markdown+chunks (DI) and facts (CU)."""
    return ingestion.ingest_document(mandate_id, source_name, data)
