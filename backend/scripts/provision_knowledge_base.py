"""One-shot provisioning for the Foundry IQ knowledge base and its knowledge sources.

Run ONCE per environment (idempotent create-or-update). Steps:
  1. Ensure the PDF source search index exists (vector + semantic + integrated vectorization).
  2. Register knowledge sources: PDF index, Work IQ, Fabric Data Agent, Fabric Ontology, Web.
  3. Build the Foundry IQ knowledge base aggregating the sources.
  4. Create the RemoteTool project connection (ARM) so agents can call the KB via MCP.
  5. Grant the project managed identity 'Search Index Data Reader' on the search service.

Prerequisites (out of band):
  - Work IQ: 'EnableFoundryIQWithWorkIQ' feature flag + M365 Copilot licences (same tenant).
  - Fabric IQ: Fabric workspace + Data Agent / Ontology in the same Entra tenant.
  - Reference data: if DATA_SOURCE_MODE=fabric, load the advisory tables into the Fabric
    Warehouse first via 'python -m scripts.load_fabric_tables' (see scripts/fabric/README.md).

Usage:
    python -m backend.scripts.provision_knowledge_base
"""

from __future__ import annotations

import logging

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    FabricDataAgentKnowledgeSource,
    FabricDataAgentKnowledgeSourceParameters,
    FabricOntologyKnowledgeSource,
    FabricOntologyKnowledgeSourceParameters,
    WorkIQKnowledgeSource,
)

from app.infra.clients import get_credential
from app.infra.settings import get_settings
from app.services.search_index import ensure_pdf_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _index_client() -> SearchIndexClient:
    settings = get_settings()
    return SearchIndexClient(endpoint=settings.search_endpoint, credential=get_credential())


def register_knowledge_sources() -> list[str]:
    """Register Work IQ + Fabric IQ knowledge sources. Returns registered source names."""
    settings = get_settings()
    client = _index_client()
    registered: list[str] = []

    # Work IQ — house view, style guide, approved-language/disclosure library (M365).
    work_iq = WorkIQKnowledgeSource(
        name="wealthgen-work-iq",
        description="House view, brand voice style guide, and approved-language disclosure library.",
    )
    client.create_or_update_knowledge_source(knowledge_source=work_iq)
    registered.append(work_iq.name)

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

    return registered


def main() -> None:
    settings = get_settings()
    logger.info("Ensuring PDF source index '%s'...", settings.pdf_index_name)
    ensure_pdf_index()

    logger.info("Registering Work IQ / Fabric IQ knowledge sources...")
    sources = register_knowledge_sources()
    logger.info("Registered knowledge sources: %s", sources)

    logger.info(
        "NEXT (manual/ARM): build knowledge base '%s' over sources, create RemoteTool "
        "connection '%s' (authType=ProjectManagedIdentity, audience=https://search.azure.com/), "
        "and grant the project MI 'Search Index Data Reader'.",
        settings.kb_name,
        settings.kb_connection_name,
    )


if __name__ == "__main__":
    main()
