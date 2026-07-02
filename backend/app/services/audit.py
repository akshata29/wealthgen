"""Immutable audit trail + PII masking for financial data mutations."""

from __future__ import annotations

import logging
import re
import uuid

from app.infra.clients import get_cosmos_client
from app.infra.settings import get_settings
from app.models.approvals import AuditRecord

logger = logging.getLogger(__name__)

_ACCOUNT_RE = re.compile(r"(?<=\w)\w(?=\w{0,3}\d)")


def mask_pii(value: str) -> str:
    """Mask an account/client identifier, keeping only the last four characters."""
    if not value:
        return value
    tail = value[-4:]
    return f"{'*' * max(0, len(value) - 4)}{tail}"


def _container():
    settings = get_settings()
    client = get_cosmos_client()
    db = client.get_database_client(settings.cosmos_database)
    return db.get_container_client(settings.cosmos_container)


def write_audit(record: AuditRecord) -> AuditRecord:
    """Persist an immutable audit record. Client id is masked before storage."""
    record.id = record.id or f"audit-{uuid.uuid4()}"
    record.client_id = mask_pii(record.client_id)
    item = record.model_dump(mode="json")
    item["mandate_id"] = record.mandate_id  # partition key
    _container().upsert_item(item)
    logger.info("Audit: %s mandate=%s action=%s", record.event_type, record.mandate_id, record.action)
    return record
