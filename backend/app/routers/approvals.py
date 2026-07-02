"""HITL approval endpoints — PM review, PM/Compliance approval, delivery gate."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.models.approvals import AuditEventType, AuditRecord
from app.models.commentary import ApproveCommentaryRequest, ReviewCommentaryRequest
from app.services import audit, commentary_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/commentary/{commentary_id}/review")
async def review(commentary_id: str, mandate_id: str, request: ReviewCommentaryRequest) -> dict:
    if request.sections is not None:
        updated = commentary_store.update_sections(
            commentary_id, mandate_id, [s.model_dump(mode="json") for s in request.sections]
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.EDITED,
            advisor_id=request.advisor_id,
            client_id=mandate_id,
            session_id=commentary_id,
            mandate_id=mandate_id,
            action="commentary_edited",
            metadata={"pm_status": request.pm_status},
        )
    )
    return {"commentary_id": commentary_id, "status": "reviewed"}


@router.post("/commentary/{commentary_id}/approve")
async def approve(commentary_id: str, mandate_id: str, request: ApproveCommentaryRequest) -> dict:
    if request.role not in {"pm", "compliance"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BAD_ROLE", "message": "role must be 'pm' or 'compliance'"},
        )
    approval = commentary_store.update_approval(commentary_id, mandate_id, request.role)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.APPROVED,
            advisor_id=request.approver_id,
            client_id=mandate_id,
            session_id=commentary_id,
            mandate_id=mandate_id,
            action=f"approved_by_{request.role}",
            approval=approval.model_dump(mode="json"),
        )
    )
    return {"commentary_id": commentary_id, "approval": approval.model_dump(mode="json")}


@router.post("/commentary/{commentary_id}/deliver")
async def deliver(commentary_id: str, mandate_id: str) -> dict:
    item = commentary_store.get_commentary(commentary_id, mandate_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    from app.models.approvals import ApprovalState

    approval = ApprovalState.model_validate(item.get("approval", {"commentary_id": commentary_id}))
    if not approval.can_deliver:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "NOT_APPROVED",
                "message": "PM and Compliance must both approve before delivery.",
            },
        )
    commentary_store.mark_delivered(commentary_id, mandate_id)
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.DELIVERED,
            advisor_id="system",
            client_id=mandate_id,
            session_id=commentary_id,
            mandate_id=mandate_id,
            action="commentary_delivered",
        )
    )
    return {"commentary_id": commentary_id, "status": "delivered"}
