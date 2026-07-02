"""Azure AI Content Safety checks for user-provided text and generated commentary."""

from __future__ import annotations

import logging

from app.infra.clients import get_content_safety_client

logger = logging.getLogger(__name__)

# Severity threshold (0-7 scale); >= this value blocks.
BLOCK_SEVERITY = 4


class ContentSafetyError(ValueError):
    """Raised when text violates content safety policy."""


def check_text(text: str) -> None:
    """Raise ContentSafetyError if the text breaches policy; otherwise return None."""
    from azure.ai.contentsafety.models import AnalyzeTextOptions

    if not text.strip():
        return
    client = get_content_safety_client()
    response = client.analyze_text(AnalyzeTextOptions(text=text))
    for item in response.categories_analysis:
        severity = item.severity or 0
        if severity >= BLOCK_SEVERITY:
            raise ContentSafetyError(
                f"Content safety violation: {item.category} severity {severity}"
            )
