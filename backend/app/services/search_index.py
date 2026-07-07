"""Azure AI Search — PDF source index (hybrid + integrated vectorization).

Stores the SourceFacts extracted by Content Understanding so agents can ground
narrative claims in them. Underlies the Foundry IQ knowledge base.
"""

from __future__ import annotations

import logging
import re

from app.infra.clients import (
    get_embeddings_client,
    get_search_client,
    get_search_index_client,
)
from app.infra.settings import get_settings
from app.models.sources import SourceFact

logger = logging.getLogger(__name__)

VECTOR_DIMENSIONS = 1536


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed texts with the Azure OpenAI embedding deployment."""
    settings = get_settings()
    response = get_embeddings_client().embeddings.create(
        model=settings.embedding_deployment,
        input=texts,
    )
    return [item.embedding for item in response.data]


def ensure_pdf_index() -> None:
    """Create-or-update the PDF facts index (vector field + semantic config)."""
    from azure.search.documents.indexes.models import (
        AzureOpenAIVectorizer,
        AzureOpenAIVectorizerParameters,
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
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="label", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="origin", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="mandate_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="period", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="value", type=SearchFieldDataType.String),
        SimpleField(name="confidence", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="section", type=SearchFieldDataType.String),
        SimpleField(name="page", type=SearchFieldDataType.Int32, filterable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="wg-hnsw",
        ),
    ]
    vectorizers = None
    profile_kwargs = {}
    if settings.azure_openai_endpoint:
        vectorizers = [
            AzureOpenAIVectorizer(
                vectorizer_name="wg-aoai",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=settings.azure_openai_endpoint,
                    deployment_name=settings.embedding_deployment,
                    model_name=settings.embedding_model,
                ),
            )
        ]
        profile_kwargs["vectorizer_name"] = "wg-aoai"
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="wg-hnsw-algo")],
        profiles=[
            VectorSearchProfile(
                name="wg-hnsw",
                algorithm_configuration_name="wg-hnsw-algo",
                **profile_kwargs,
            )
        ],
        vectorizers=vectorizers,
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


def upsert_facts(mandate_id: str, facts: list[SourceFact], period: str | None = None) -> int:
    """Upsert extracted facts as searchable documents (with content embeddings)."""
    client = get_search_client()
    docs = [
        {
            "id": _doc_id(mandate_id, fact.source_id),
            "doc_type": "fact",
            "label": fact.label,
            "content": f"{fact.label}: {fact.value or ''}",
            "origin": fact.origin.value,
            "mandate_id": mandate_id,
            "period": period,
            "value": fact.value,
            "confidence": fact.confidence,
        }
        for fact in facts
    ]
    if not docs:
        return 0
    for doc, vector in zip(docs, _embed([d["content"] for d in docs])):
        doc["content_vector"] = vector
    client.upload_documents(documents=docs)
    logger.info("Upserted %d fact docs for mandate %s.", len(docs), mandate_id)
    return len(docs)


def upsert_chunks(
    mandate_id: str, source_file: str, chunks: list, period: str | None = None
) -> int:
    """Upsert markdown chunks (from DI layout) as searchable, vectorised documents.

    `chunks` is a list of `app.services.chunking.Chunk`.
    """
    client = get_search_client()
    docs = [
        {
            "id": _doc_id(mandate_id, f"chunk:{source_file}:{chunk.ordinal}"),
            "doc_type": "chunk",
            "label": chunk.section,
            "content": chunk.content,
            "origin": "document_intelligence",
            "mandate_id": mandate_id,
            "period": period,
            "source_file": source_file,
            "section": chunk.section,
            "page": chunk.page,
        }
        for chunk in chunks
    ]
    if not docs:
        return 0
    for doc, vector in zip(docs, _embed([d["content"] for d in docs])):
        doc["content_vector"] = vector
    client.upload_documents(documents=docs)
    logger.info("Upserted %d chunk docs for mandate %s (%s).", len(docs), mandate_id, source_file)
    return len(docs)


def _doc_id(mandate_id: str, source_id: str) -> str:
    raw = f"{mandate_id}__{source_id}"
    # Search keys allow only letters, digits, underscore, dash, equals.
    return re.sub(r"[^A-Za-z0-9_\-=]", "_", raw)
