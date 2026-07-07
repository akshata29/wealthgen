"""Batch-ingest the synthetic PDF factsheets through the REAL Azure services.

For each PDF this:
  1. Document Intelligence `prebuilt-layout` -> Markdown (persisted for inspection),
  2. chunks the Markdown (section-aware, size-capped, page-tracked),
  3. embeds + upserts the chunks into the search index (doc_type="chunk"), and
  4. (best effort) Content Understanding -> SourceFacts -> index (doc_type="fact").

Chunks complement the fact docs in the same `wealthgenpdf` index: chunks ground
narrative, facts ground numeric substantiation.

Run:
    cd backend
    python -m scripts.synthetic.render_factsheets_pdf     # produce PDFs first
    python -m scripts.ingest_pdfs                          # ingest all
    python -m scripts.ingest_pdfs --limit 1               # validate on one
    python -m scripts.ingest_pdfs --no-cu                 # DI/chunks only
    python -m scripts.ingest_pdfs --mandate ashcombe-ldi-core
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure the backend package root is importable when run directly.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services import ingestion, search_index

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

PDF_DIR = _BACKEND_ROOT / "data" / "synthetic" / "foundry_iq" / "factsheets" / "pdf"
MD_OUT_DIR = _BACKEND_ROOT / "data" / "synthetic" / "foundry_iq" / "factsheets" / "markdown"


def _mandate_id(pdf_path: Path) -> str:
    """`ashcombe-ldi-core_Q1-2026.pdf` -> `ashcombe-ldi-core`."""
    stem = pdf_path.stem
    return stem.rsplit("_", 1)[0] if "_" in stem else stem


def ingest_pdf(pdf_path: Path, *, with_cu: bool) -> tuple[int, int]:
    """Ingest one PDF via the shared pipeline. Returns (chunks_indexed, facts_indexed)."""
    mandate_id = _mandate_id(pdf_path)
    data = pdf_path.read_bytes()
    result = ingestion.ingest_document(mandate_id, pdf_path.name, data, with_cu=with_cu)

    # Persist the DI markdown for inspection (batch-only convenience).
    MD_OUT_DIR.mkdir(parents=True, exist_ok=True)
    (MD_OUT_DIR / f"{pdf_path.stem}.md").write_text(result.markdown, encoding="utf-8")

    logger.info(
        "%s -> %d chunks, %d facts", pdf_path.name, result.chunks_indexed, result.facts_indexed
    )
    return result.chunks_indexed, result.facts_indexed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Only ingest the first N PDFs.")
    parser.add_argument("--mandate", type=str, default=None, help="Only this mandate id.")
    parser.add_argument("--no-cu", action="store_true", help="Skip Content Understanding facts.")
    args = parser.parse_args()

    logger.info("Ensuring search index (with chunk fields)...")
    search_index.ensure_pdf_index()

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if args.mandate:
        pdfs = [p for p in pdfs if _mandate_id(p) == args.mandate]
    if args.limit:
        pdfs = pdfs[: args.limit]
    if not pdfs:
        raise FileNotFoundError(
            f"No PDFs found in {PDF_DIR}. Run 'python -m scripts.synthetic.render_factsheets_pdf'."
        )

    total_chunks = total_facts = 0
    for pdf_path in pdfs:
        c, f = ingest_pdf(pdf_path, with_cu=not args.no_cu)
        total_chunks += c
        total_facts += f

    logger.info(
        "Done: %d PDFs -> %d chunks, %d facts indexed.", len(pdfs), total_chunks, total_facts
    )


if __name__ == "__main__":
    main()
