"""Live document ingestion — the single path used by the API and batch scripts.

For a PDF (bytes) this:
  1. Document Intelligence `prebuilt-layout` -> Markdown,
  2. section-aware chunking,
  3. embed + upsert chunks into the search index (doc_type="chunk"), and
  4. Content Understanding -> structured SourceFacts -> index (doc_type="fact").

Chunks ground narrative; facts ground numeric substantiation. Both live in the
same `wealthgenpdf` index. Real services only — no synthetic fallback.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.models.sources import SourceFact
from app.services import content_understanding, search_index
from app.services.chunking import chunk_markdown
from app.services.document_layout import extract_markdown_from_bytes

logger = logging.getLogger(__name__)


def _period_from_source(source_name: str) -> str | None:
    """`ashcombe-ldi-core_Q1-2026.pdf` -> `Q1-2026` (the trailing _<period> token)."""
    stem = Path(source_name).stem
    return stem.rsplit("_", 1)[1] if "_" in stem else None


class IngestResult:
    def __init__(
        self,
        markdown: str,
        chunks_indexed: int,
        facts: list[SourceFact],
        facts_indexed: int,
        needs_review: list[str],
    ) -> None:
        self.markdown = markdown
        self.chunks_indexed = chunks_indexed
        self.facts = facts
        self.facts_indexed = facts_indexed
        self.needs_review = needs_review


def ingest_document(
    mandate_id: str, source_name: str, data: bytes, *, with_cu: bool = True
) -> IngestResult:
    """Run the full live ingestion pipeline for one PDF's bytes."""
    period = _period_from_source(source_name)

    # 1-3: Document Intelligence markdown -> chunks -> index
    markdown = extract_markdown_from_bytes(data)
    chunks = chunk_markdown(markdown)
    chunks_indexed = search_index.upsert_chunks(mandate_id, source_name, chunks, period=period)

    # 4: Content Understanding structured facts (best effort — never drop chunks).
    facts: list[SourceFact] = []
    facts_indexed = 0
    needs_review: list[str] = []
    if with_cu:
        try:
            extraction = content_understanding.analyze_factsheet_bytes(data)
            stem = Path(source_name).stem
            for fact in extraction.facts:
                # Disambiguate per source (period) so quarters don't overwrite.
                fact.source_id = f"cu:{stem}:{fact.label}"
            facts = extraction.facts
            facts_indexed = search_index.upsert_facts(mandate_id, facts, period=period)
            needs_review = extraction.needs_review
        except Exception as exc:  # noqa: BLE001 — CU optional; chunks already indexed.
            logger.warning("Content Understanding failed for %s: %s", source_name, exc)

    logger.info(
        "Ingested %s for %s: %d chunks, %d facts (%d need review).",
        source_name,
        mandate_id,
        chunks_indexed,
        facts_indexed,
        len(needs_review),
    )
    return IngestResult(
        markdown=markdown,
        chunks_indexed=chunks_indexed,
        facts=facts,
        facts_indexed=facts_indexed,
        needs_review=needs_review,
    )
