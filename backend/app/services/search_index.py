"""Azure AI Search — PDF source index (hybrid + integrated vectorization).

Stores the SourceFacts extracted by Content Understanding so agents can ground
narrative claims in them. Underlies the Foundry IQ knowledge base.
"""

from __future__ import annotations

import logging

from app.infra.clients import get_search_client, get_search_index_client
from app.infra.settings import get_settings
from app.models.sources import SourceFact

logger = logging.getLogger(__name__)

VECTOR_DIMENSIONS = 1536


def ensure_pdf_index() -> None:
    """Create-or-update the PDF facts index (vector field + semantic config)."""
    from azure.search.documents.indexes.models import (
        HnswAlgorithmConfiguration,
        SearchableField,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        SemanticConfiguration,
        SemanticField,
        SemanticPrioritizedFields,
        SemanticSearch,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )

    settings = get_settings()
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="label", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="origin", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="mandate_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="value", type=SearchFieldDataType.String),
        SimpleField(name="confidence", type=SearchFieldDataType.Double, filterable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="wg-hnsw",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="wg-hnsw-algo")],
        profiles=[VectorSearchProfile(name="wg-hnsw", algorithm_configuration_name="wg-hnsw-algo")],
    )
    semantic = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="wg-semantic",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")],
                    title_field=SemanticField(field_name="label"),
                ),
            )
        ]
    )
    index = SearchIndex(
        name=settings.pdf_index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic,
    )
    get_search_index_client().create_or_update_index(index)
    logger.info("Ensured PDF source index '%s'.", settings.pdf_index_name)


def upsert_facts(mandate_id: str, facts: list[SourceFact]) -> int:
    """Upsert extracted facts as searchable documents."""
    client = get_search_client()
    docs = [
        {
            "id": _doc_id(mandate_id, fact.source_id),
            "label": fact.label,
            "content": f"{fact.label}: {fact.value or ''}",
            "origin": fact.origin.value,
            "mandate_id": mandate_id,
            "value": fact.value,
            "confidence": fact.confidence,
        }
        for fact in facts
    ]
    if not docs:
        return 0
    client.upload_documents(documents=docs)
    logger.info("Upserted %d fact docs for mandate %s.", len(docs), mandate_id)
    return len(docs)


def _doc_id(mandate_id: str, source_id: str) -> str:
    safe = source_id.replace(":", "_")
    return f"{mandate_id}__{safe}"
