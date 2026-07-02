"""Fabric IQ — knowledge-source registration + query-time OBO auth helper.

Registration is done at provisioning time; retrieval flows through the Foundry IQ
knowledge base. Auth to Fabric is the END-USER OBO token at query time (NOT a
stored SPN) via the `x-ms-query-source-authorization` header.
"""

from __future__ import annotations

import logging

from app.infra.clients import get_search_index_client
from app.infra.settings import get_settings

logger = logging.getLogger(__name__)

# Work IQ / Fabric IQ retrieval can take 40-60s+.
MAX_RUNTIME_SECONDS = 120


def register_sources() -> list[str]:
    """Register Fabric Data Agent + Fabric Ontology knowledge sources."""
    from azure.search.documents.indexes.models import (
        FabricDataAgentKnowledgeSource,
        FabricDataAgentKnowledgeSourceParameters,
        FabricOntologyKnowledgeSource,
        FabricOntologyKnowledgeSourceParameters,
    )

    settings = get_settings()
    client = get_search_index_client()
    registered: list[str] = []

    if settings.fabric_workspace_id and settings.fabric_data_agent_id:
        ks = FabricDataAgentKnowledgeSource(
            name="wealthgen-fabric-data-agent",
            description="Validated holdings, weights, and Brinson attribution.",
            fabric_data_agent_parameters=FabricDataAgentKnowledgeSourceParameters(
                workspace_id=settings.fabric_workspace_id,
                data_agent_id=settings.fabric_data_agent_id,
            ),
        )
        client.create_or_update_knowledge_source(knowledge_source=ks)
        registered.append(ks.name)

    if settings.fabric_workspace_id and settings.fabric_ontology_id:
        ks = FabricOntologyKnowledgeSource(
            name="wealthgen-fabric-ontology",
            description="Mandate/portfolio/benchmark ontology over OneLake.",
            fabric_ontology_parameters=FabricOntologyKnowledgeSourceParameters(
                workspace_id=settings.fabric_workspace_id,
                ontology_id=settings.fabric_ontology_id,
            ),
        )
        client.create_or_update_knowledge_source(knowledge_source=ks)
        registered.append(ks.name)

    logger.info("Registered Fabric IQ sources: %s", registered)
    return registered


def obo_headers(end_user_token: str | None) -> dict[str, str]:
    """Query-time OBO header for Fabric IQ retrieval (scope search.azure.com)."""
    if not end_user_token:
        return {}
    return {"x-ms-query-source-authorization": end_user_token}
