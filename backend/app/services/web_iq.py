"""Web IQ — live web grounding for the 'Market Context' section.

Used for market/macro context only — never client data. Registered as a Web
knowledge source on the Foundry IQ knowledge base.
"""

from __future__ import annotations

import logging

from app.infra.clients import get_search_index_client

logger = logging.getLogger(__name__)

SOURCE_NAME = "wealthgen-web-iq"


def register_source() -> str:
    """Register the Web knowledge source (GA generic Web / Web IQ MCP)."""
    from azure.search.documents.indexes.models import WebKnowledgeSource

    client = get_search_index_client()
    ks = WebKnowledgeSource(
        name=SOURCE_NAME,
        description="Live web grounding for market and macro context.",
    )
    client.create_or_update_knowledge_source(knowledge_source=ks)
    logger.info("Registered Web IQ source '%s'.", SOURCE_NAME)
    return SOURCE_NAME
