"""Provision the WealthGen fund fact-sheet Content Understanding analyzer.

Creates (idempotent) a custom analyzer over `prebuilt-documentAnalyzer` that
extracts the structured fund metrics from a fact-sheet PDF as SourceFacts.

Run:
    cd backend
    python -m scripts.provision_cu_analyzer
    python -m scripts.provision_cu_analyzer --recreate
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.infra.clients import get_content_understanding_client
from app.infra.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Field label -> natural-language extraction hint.
FACT_FIELDS: dict[str, str] = {
    "total_return_net": "Total return net of fees, as a percentage (e.g. +1.05%).",
    "benchmark_return": "Benchmark return, as a percentage.",
    "active_return": "Active return / excess return over benchmark (e.g. +125 bps).",
    "tracking_error": "Tracking error, as a percentage.",
    "information_ratio": "Information ratio (a number).",
    "sharpe_ratio": "Sharpe ratio (a number).",
    "max_drawdown": "Maximum drawdown, as a percentage.",
    "ongoing_charges": "Ongoing charges figure / OCF, as a percentage.",
    "distribution_yield": "Distribution yield, as a percentage.",
    "duration": "Fixed income duration in years (e.g. 6.5y).",
}


def build_analyzer():
    from azure.ai.contentunderstanding.models import (
        ContentAnalyzer,
        ContentFieldDefinition,
        ContentFieldSchema,
        ContentFieldType,
        GenerationMethod,
    )

    fields = {
        name: ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.EXTRACT,
            description=hint,
        )
        for name, hint in FACT_FIELDS.items()
    }
    settings = get_settings()
    return ContentAnalyzer(
        base_analyzer_id="prebuilt-document",
        description="WealthGen fund fact-sheet metric extractor.",
        field_schema=ContentFieldSchema(fields=fields),
        models={"completion": settings.cu_completion_model},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recreate", action="store_true", help="Delete then recreate.")
    args = parser.parse_args()

    settings = get_settings()
    cu = get_content_understanding_client()
    analyzer_id = settings.cu_analyzer_id

    existing = {a.analyzer_id for a in cu.list_analyzers()}
    if analyzer_id in existing:
        if not args.recreate:
            logger.info("Analyzer '%s' already exists. Use --recreate to rebuild.", analyzer_id)
            return
        logger.info("Deleting existing analyzer '%s'...", analyzer_id)
        cu.delete_analyzer(analyzer_id)

    logger.info("Creating analyzer '%s'...", analyzer_id)
    poller = cu.begin_create_analyzer(analyzer_id=analyzer_id, resource=build_analyzer())
    result = poller.result()
    logger.info("Created analyzer '%s' (status: %s).", analyzer_id, getattr(result, "status", "?"))


if __name__ == "__main__":
    main()
