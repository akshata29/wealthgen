"""Provision the Foundry IQ knowledge base and its knowledge sources.

Idempotent create-or-update. Steps:
  1. Ensure the PDF source search index exists (vector + semantic + vectorizer).
  2. Register knowledge sources:
       - the PDF index (always),
       - Work IQ (best effort — needs the feature flag + M365 licences),
       - Fabric Data Agent / Ontology (only if FABRIC_* is configured).
  3. Build the Foundry IQ knowledge base aggregating the registered sources.

Still MANUAL / ARM afterwards (see the printed NEXT steps):
  4. Create the RemoteTool project connection `KB_CONNECTION_NAME`
     (authType=ProjectManagedIdentity, audience=https://search.azure.com/).
  5. Grant the Foundry project managed identity 'Search Index Data Reader' on the
     search service so the agent can call the KB via MCP.

Usage:
    cd backend
    python -m scripts.provision_knowledge_base
    python -m scripts.provision_knowledge_base --pdf-only   # skip Work IQ / Fabric
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizerParameters,
    FabricDataAgentKnowledgeSource,
    FabricDataAgentKnowledgeSourceParameters,
    FabricOntologyKnowledgeSource,
    FabricOntologyKnowledgeSourceParameters,
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeSourceReference,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
    WorkIQKnowledgeSource,
)

from app.infra.clients import get_search_index_client
from app.infra.settings import get_settings
from app.services.search_index import ensure_pdf_index

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def register_pdf_source(base_filter: str | None = None) -> str:
    """Register the PDF chunks+facts index as a Search Index knowledge source.

    `mandate_id` and `period` are returned as source data fields so retrieval
    results are traceable and can be scoped by mandate/quarter. Pass `base_filter`
    (e.g. "mandate_id eq 'ashcombe-ldi-core' and period eq 'Q1-2026'") to hard-scope
    the whole source; per-query scoping is done via runtime filter overrides.
    """
    settings = get_settings()
    client = get_search_index_client()
    source = SearchIndexKnowledgeSource(
        name=settings.kb_pdf_source_name,
        description="WealthGen fund fact-sheet markdown chunks + extracted metrics.",
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=settings.pdf_index_name,
            semantic_configuration_name="wg-semantic",
            # Focus retrieval on the text fields (not ids/values).
            search_fields=[
                SearchIndexFieldReference(name="content"),
                SearchIndexFieldReference(name="label"),
                SearchIndexFieldReference(name="section"),
            ],
            # Return provenance/scoping fields with each result.
            source_data_fields=[
                SearchIndexFieldReference(name="mandate_id"),
                SearchIndexFieldReference(name="period"),
                SearchIndexFieldReference(name="doc_type"),
                SearchIndexFieldReference(name="section"),
                SearchIndexFieldReference(name="page"),
                SearchIndexFieldReference(name="source_file"),
            ],
            base_filter=base_filter,
        ),
    )
    client.create_or_update_knowledge_source(knowledge_source=source)
    logger.info("Registered PDF knowledge source '%s'.", source.name)
    return source.name


def register_optional_sources() -> list[str]:
    """Register Work IQ + Fabric IQ sources when available. Returns registered names."""
    settings = get_settings()
    client = get_search_index_client()
    registered: list[str] = []

    # Work IQ — house view, style guide, approved-language/disclosure library (M365).
    try:
        work_iq = WorkIQKnowledgeSource(
            name="wealthgen-work-iq",
            description="House view, brand voice style guide, and approved-language disclosure library.",
        )
        client.create_or_update_knowledge_source(knowledge_source=work_iq)
        registered.append(work_iq.name)
        logger.info("Registered Work IQ knowledge source.")
    except Exception as exc:  # noqa: BLE001 — needs feature flag + M365 licences.
        logger.warning("Work IQ source skipped: %s", exc)

    # Fabric Data Agent — validated holdings, weights, attribution.
    if settings.fabric_workspace_id and settings.fabric_data_agent_id:
        fabric_agent = FabricDataAgentKnowledgeSource(
            name="wealthgen-fabric-data-agent",
            description="Validated portfolio holdings, weights, and Brinson attribution.",
            fabric_data_agent_parameters=FabricDataAgentKnowledgeSourceParameters(
                workspace_id=settings.fabric_workspace_id,
                data_agent_id=settings.fabric_data_agent_id,
            ),
        )
        client.create_or_update_knowledge_source(knowledge_source=fabric_agent)
        registered.append(fabric_agent.name)
        logger.info("Registered Fabric Data Agent knowledge source.")

    # Fabric Ontology — business entities/relationships over OneLake.
    if settings.fabric_workspace_id and settings.fabric_ontology_id:
        fabric_ontology = FabricOntologyKnowledgeSource(
            name="wealthgen-fabric-ontology",
            description="Mandate/portfolio/benchmark ontology linked to OneLake.",
            fabric_ontology_parameters=FabricOntologyKnowledgeSourceParameters(
                workspace_id=settings.fabric_workspace_id,
                ontology_id=settings.fabric_ontology_id,
            ),
        )
        client.create_or_update_knowledge_source(knowledge_source=fabric_ontology)
        registered.append(fabric_ontology.name)
        logger.info("Registered Fabric Ontology knowledge source.")

    return registered


def build_knowledge_base(source_names: list[str]) -> None:
    """Create-or-update the KB aggregating the registered knowledge sources."""
    settings = get_settings()
    if not settings.azure_openai_endpoint:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT is required to build the knowledge base.")
    client = get_search_index_client()
    kb = KnowledgeBase(
        name=settings.kb_name,
        description="WealthGen grounding hub (PDF facts/chunks + Work IQ + Fabric IQ).",
        knowledge_sources=[KnowledgeSourceReference(name=n) for n in source_names],
        models=[
            KnowledgeBaseAzureOpenAIModel(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=settings.azure_openai_endpoint,
                    deployment_name=settings.kb_completion_deployment,
                    model_name=settings.kb_completion_model,
                )
            )
        ],
        output_mode="answerSynthesis",
    )
    client.create_or_update_knowledge_base(knowledge_base=kb)
    logger.info("Built knowledge base '%s' over %d source(s).", settings.kb_name, len(source_names))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-only", action="store_true", help="Skip Work IQ / Fabric sources.")
    args = parser.parse_args()

    settings = get_settings()
    logger.info("Ensuring PDF source index '%s'...", settings.pdf_index_name)
    ensure_pdf_index()

    sources = [register_pdf_source()]
    if not args.pdf_only:
        sources.extend(register_optional_sources())
    logger.info("Registered knowledge sources: %s", sources)

    build_knowledge_base(sources)

    logger.info(
        "\nNEXT (manual/ARM):\n"
        "  4. Create the RemoteTool project connection '%s' in the Foundry project\n"
        "     (authType=ProjectManagedIdentity, audience=https://search.azure.com/).\n"
        "  5. Grant the Foundry project managed identity 'Search Index Data Reader'\n"
        "     on search service '%s'.",
        settings.kb_connection_name,
        settings.search_endpoint,
    )


if __name__ == "__main__":
    main()
