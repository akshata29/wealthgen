"""Lazy Azure client factories.

Credential selection:
  - service principal (AZURE_TENANT_ID/CLIENT_ID/CLIENT_SECRET) -> ClientSecretCredential
  - local   -> AzureCliCredential (az login)
  - prod    -> DefaultAzureCredential (managed identity)

Clients are created on demand and cached. No mocks, no fallbacks — a missing
endpoint raises when the client is first requested.
"""

from __future__ import annotations

from functools import lru_cache

from azure.identity import (
    AzureCliCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
)

from app.infra.settings import get_settings


@lru_cache
def get_credential():
    settings = get_settings()
    if settings.has_service_principal:
        return ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )
    if settings.is_local:
        return AzureCliCredential()
    return DefaultAzureCredential()


@lru_cache
def get_project_client():
    """Azure AI Foundry project client (new-GA azure-ai-projects 2.x)."""
    from azure.ai.projects import AIProjectClient

    settings = get_settings()
    return AIProjectClient(endpoint=settings.foundry_endpoint, credential=get_credential())


@lru_cache
def get_content_understanding_client():
    from azure.ai.contentunderstanding import ContentUnderstandingClient

    settings = get_settings()
    return ContentUnderstandingClient(
        endpoint=settings.cu_endpoint, credential=get_credential()
    )


@lru_cache
def get_document_intelligence_client():
    from azure.ai.documentintelligence import DocumentIntelligenceClient

    settings = get_settings()
    if not settings.di_endpoint:
        raise RuntimeError("DI_ENDPOINT is not configured; required for layout markdown.")
    return DocumentIntelligenceClient(
        endpoint=settings.di_endpoint, credential=get_credential()
    )


@lru_cache
def get_embeddings_client():
    """Azure OpenAI client for the embedding deployment (AAD token auth)."""
    from azure.identity import get_bearer_token_provider
    from openai import AzureOpenAI

    settings = get_settings()
    if not settings.azure_openai_endpoint:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT is not configured; required for embeddings."
        )
    token_provider = get_bearer_token_provider(
        get_credential(), "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=settings.embedding_api_version,
    )


def _search_credential():
    """Prefer the admin key when configured (provisioning path), else AAD."""
    settings = get_settings()
    if settings.search_admin_key:
        from azure.core.credentials import AzureKeyCredential

        return AzureKeyCredential(settings.search_admin_key)
    return get_credential()


@lru_cache
def get_search_index_client():
    from azure.search.documents.indexes import SearchIndexClient

    settings = get_settings()
    return SearchIndexClient(
        endpoint=settings.search_endpoint, credential=_search_credential()
    )


@lru_cache
def get_search_client():
    from azure.search.documents import SearchClient

    settings = get_settings()
    return SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.pdf_index_name,
        credential=_search_credential(),
    )


@lru_cache
def get_kb_retrieval_client():
    """Foundry IQ knowledge base retrieval client (direct, filterable retrieval)."""
    from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient

    settings = get_settings()
    return KnowledgeBaseRetrievalClient(
        endpoint=settings.search_endpoint,
        credential=_search_credential(),
        knowledge_base_name=settings.kb_name,
    )


@lru_cache
def get_cosmos_client():
    from azure.cosmos import CosmosClient

    settings = get_settings()
    return CosmosClient(url=settings.cosmos_endpoint, credential=get_credential())


@lru_cache
def get_content_safety_client():
    from azure.ai.contentsafety import ContentSafetyClient

    settings = get_settings()
    return ContentSafetyClient(
        endpoint=settings.content_safety_endpoint, credential=get_credential()
    )
