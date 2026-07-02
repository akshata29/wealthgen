"""Work IQ — knowledge-source registration for house content.

Grounds the house view, brand-voice style guide, and approved-language /
disclosure library from Microsoft 365. Auth is the end-user OBO token at query
time (see `fabric_iq.obo_headers`). Prereqs: M365 Copilot licence +
`EnableFoundryIQWithWorkIQ` feature flag, same Entra tenant.
"""

from __future__ import annotations

import logging

from app.infra.clients import get_search_index_client

logger = logging.getLogger(__name__)

SOURCE_NAME = "wealthgen-work-iq"


def register_source() -> str:
    """Register the Work IQ knowledge source (kind: workIQ)."""
    from azure.search.documents.indexes.models import WorkIQKnowledgeSource

    client = get_search_index_client()
    ks = WorkIQKnowledgeSource(
        name=SOURCE_NAME,
        description="House view, brand-voice style guide, approved-language disclosure library.",
    )
    client.create_or_update_knowledge_source(knowledge_source=ks)
    logger.info("Registered Work IQ source '%s'.", SOURCE_NAME)
    return SOURCE_NAME
