"""Ingest the real fund fact sheets (from the manifest) into the search index.

For each fund in ``data/real_funds/manifest.json`` this runs the same live
pipeline as the synthetic ingest (Document Intelligence -> chunks -> Search, plus
best-effort Content Understanding facts), associating the fund's fact sheet with
every mandate that holds it and tagging the configured period so retrieval stays
period-scoped.

Requires Azure creds in ``backend/.env`` (Document Intelligence + Search, and
optionally Content Understanding). Download the PDFs first:

    cd backend
    python -m scripts.download_real_factsheets
    python -m scripts.ingest_real_factsheets
    python -m scripts.ingest_real_factsheets --no-cu           # DI/chunks only
    python -m scripts.ingest_real_factsheets --ticker IVV      # single fund
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services import ingestion, search_index

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

_REAL_ROOT = _BACKEND_ROOT / "data" / "real_funds"
_MANIFEST = _REAL_ROOT / "manifest.json"
_PDF_DIR = _REAL_ROOT / "pdfs"
_MD_OUT_DIR = _REAL_ROOT / "markdown"


def _source_name(ticker: str, mandate_id: str, period: str) -> str:
    """`IVV`, `halvorsen-global-growth`, `Q1-2026` -> ingestible file name.

    The trailing `_<period>` token lets the shared pipeline derive the period.
    """
    return f"{ticker}-{mandate_id}_{period}.pdf"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-cu", action="store_true", help="Skip Content Understanding facts.")
    parser.add_argument("--ticker", type=str, default=None, help="Only this fund ticker.")
    args = parser.parse_args()

    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    default_period = manifest.get("default_period", "Q1-2026")
    funds = manifest.get("funds", [])
    if args.ticker:
        funds = [f for f in funds if f["ticker"].upper() == args.ticker.upper()]
    if not funds:
        raise SystemExit(f"No matching funds in {_MANIFEST}.")

    logger.info("Ensuring search index (with chunk fields)...")
    search_index.ensure_pdf_index()
    _MD_OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_chunks = total_facts = ingested = 0
    for fund in funds:
        pdf_path = _PDF_DIR / fund["pdf"]
        if not pdf_path.exists():
            logger.error("%s missing — run scripts.download_real_factsheets first.", pdf_path)
            continue
        data = pdf_path.read_bytes()
        period = fund.get("period", default_period)
        for mandate_id in fund.get("mandates", []):
            source_name = _source_name(fund["ticker"], mandate_id, period)
            result = ingestion.ingest_document(mandate_id, source_name, data, with_cu=not args.no_cu)
            (_MD_OUT_DIR / f"{Path(source_name).stem}.md").write_text(
                result.markdown, encoding="utf-8"
            )
            logger.info(
                "%s -> %s: %d chunks, %d facts",
                fund["ticker"], mandate_id, result.chunks_indexed, result.facts_indexed,
            )
            total_chunks += result.chunks_indexed
            total_facts += result.facts_indexed
            ingested += 1

    logger.info(
        "Done: %d fund/mandate ingests -> %d chunks, %d facts indexed.",
        ingested, total_chunks, total_facts,
    )


if __name__ == "__main__":
    main()
