"""Azure Blob Storage helper — stores uploaded PDFs and returns a readable URL.

Content Understanding consumes a URL source; with managed identity + a
private container the blob URL is resolved via the credential. Returns the blob
URL for the uploaded fact sheet.
"""

from __future__ import annotations

import logging
import uuid

from app.infra.clients import get_credential
from app.infra.settings import get_settings

logger = logging.getLogger(__name__)


class BlobConfigError(RuntimeError):
    """Raised when blob storage is not configured."""


def upload_pdf(mandate_id: str, filename: str, data: bytes) -> str:
    from azure.storage.blob import BlobServiceClient

    settings = get_settings()
    if not settings.blob_account_url:
        raise BlobConfigError("BLOB_ACCOUNT_URL is not configured; set it in .env.")

    service = BlobServiceClient(account_url=settings.blob_account_url, credential=get_credential())
    container = service.get_container_client(settings.blob_container)
    blob_name = f"{mandate_id}/{uuid.uuid4()}-{filename}"
    container.upload_blob(name=blob_name, data=data, overwrite=True)
    url = f"{settings.blob_account_url.rstrip('/')}/{settings.blob_container}/{blob_name}"
    logger.info("Uploaded fact sheet to %s", url)
    return url
