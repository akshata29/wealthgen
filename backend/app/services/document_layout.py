"""Azure AI Document Intelligence — layout extraction to Markdown.

Runs the `prebuilt-layout` model with Markdown output so fund fact sheets /
manager commentary PDFs become clean, structured Markdown (tables preserved,
page markers retained) suitable for semantic chunking and RAG grounding.
"""

from __future__ import annotations

import logging

from app.infra.clients import get_document_intelligence_client

logger = logging.getLogger(__name__)


def extract_markdown_from_url(pdf_url: str) -> str:
    """Analyze a PDF at a (SAS/blob) URL and return its Markdown content."""
    from azure.ai.documentintelligence.models import (
        AnalyzeDocumentRequest,
        DocumentContentFormat,
    )

    client = get_document_intelligence_client()
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        AnalyzeDocumentRequest(url_source=pdf_url),
        output_content_format=DocumentContentFormat.MARKDOWN,
    )
    result = poller.result()
    markdown = result.content or ""
    logger.info("Document Intelligence produced %d markdown chars.", len(markdown))
    return markdown


def extract_markdown_from_bytes(data: bytes) -> str:
    """Analyze in-memory PDF bytes and return its Markdown content."""
    from azure.ai.documentintelligence.models import DocumentContentFormat

    client = get_document_intelligence_client()
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=data,
        content_type="application/octet-stream",
        output_content_format=DocumentContentFormat.MARKDOWN,
    )
    result = poller.result()
    markdown = result.content or ""
    logger.info("Document Intelligence produced %d markdown chars.", len(markdown))
    return markdown
