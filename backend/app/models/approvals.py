"""Approval state and immutable audit records for financial data mutations."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ApprovalState(BaseModel):
    commentary_id: str
    pm_status: ApprovalStatus = ApprovalStatus.PENDING
    compliance_status: ApprovalStatus = ApprovalStatus.PENDING
    delivered: bool = False

    @property
    def can_deliver(self) -> bool:
        return (
            self.pm_status == ApprovalStatus.APPROVED
            and self.compliance_status == ApprovalStatus.APPROVED
        )


class AuditEventType(str, Enum):
    GENERATED = "commentary_generated"
    EDITED = "commentary_edited"
    APPROVED = "commentary_approved"
    DELIVERED = "commentary_delivered"
    DELETED = "commentary_deleted"
    INGESTED = "documents_ingested"


class AuditRecord(BaseModel):
    id: str | None = None
    type: str = "audit"  # discriminator within the commentary container
    event_type: AuditEventType
    timestamp: str = Field(default_factory=_utc_now)
    advisor_id: str
    client_id: str
    session_id: str
    mandate_id: str
    action: str
    metadata: dict = Field(default_factory=dict)
    approval: dict | None = None
