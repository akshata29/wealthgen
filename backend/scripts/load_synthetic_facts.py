"""Load generated fact-sheet SourceFacts into the Foundry IQ PDF search index.

This is the offline/demo path that bypasses PDF upload + Content Understanding:
it reads the `facts.jsonl` produced by `scripts.synthetic.generate` and upserts
the facts directly via the same `search_index.upsert_facts` used by ingest.

Requires real Azure AI Search configuration in the environment (see settings).

Run:
    cd backend
    python -m scripts.synthetic.generate            # produce data/synthetic/**
    python -m scripts.load_synthetic_facts          # index it
    python -m scripts.load_synthetic_facts --facts C:/tmp/wg/foundry_iq/facts.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

# Ensure the backend package root is importable when this file is run directly
# (e.g. `py .\load_synthetic_facts.py`) and not only as `python -m scripts.load_synthetic_facts`.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.models.sources import SourceFact
from app.services.search_index import ensure_pdf_index, upsert_facts

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def load(facts_path: Path) -> int:
    """Upsert all facts grouped by mandate. Returns total docs indexed."""
    if not facts_path.exists():
        raise FileNotFoundError(
            f"{facts_path} not found. Run 'python -m scripts.synthetic.generate' first."
        )

    by_mandate: dict[str, list[SourceFact]] = defaultdict(list)
    with facts_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            mandate_id = raw.pop("mandate_id", None)
            raw.pop("period", None)  # not a SourceFact field
            if not mandate_id:
                logger.warning("Skipping fact without mandate_id: %s", raw.get("source_id"))
                continue
            by_mandate[mandate_id].append(SourceFact.model_validate(raw))

    logger.info("Ensuring PDF source index exists...")
    ensure_pdf_index()

    total = 0
    for mandate_id, facts in sorted(by_mandate.items()):
        indexed = upsert_facts(mandate_id, facts)
        logger.info("  %-34s %d facts", mandate_id, indexed)
        total += indexed
    return total


def main() -> None:
    default = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "foundry_iq" / "facts.jsonl"
    parser = argparse.ArgumentParser(description="Index synthetic fact-sheet facts.")
    parser.add_argument("--facts", default=str(default), help="Path to facts.jsonl.")
    args = parser.parse_args()

    total = load(Path(args.facts))
    logger.info("Indexed %d fact documents into the Foundry IQ PDF index.", total)


if __name__ == "__main__":
    main()
