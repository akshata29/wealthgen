"""Commentary generation and retrieval endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel

from app.infra import auth
from app.infra.settings import get_settings
from app.models.approvals import AuditEventType, AuditRecord
from app.models.commentary import (
    Audience,
    BriefTrigger,
    CommentaryDraft,
    CommentaryType,
    ComplianceStatus,
    CompliantCommentary,
    GenerateCommentaryRequest,
)
from app.agents import compliance_guard_agent
from app.orchestration.commentary_workflow import SubstantiationError, generate_commentary
from app.services import audit, commentary_store, content_safety, substantiation

logger = logging.getLogger(__name__)
router = APIRouter()


class CommentarySummary(BaseModel):
    """Lightweight history row for a mandate's generated commentaries."""

    id: str
    mandate_id: str
    period: str
    audience: Audience
    commentary_type: CommentaryType = CommentaryType.QUARTERLY_REVIEW
    compliance_status: ComplianceStatus
    pm_status: str = "pending"
    compliance_approval: str = "pending"
    delivered: bool = False
    updated_ts: int | None = None


@router.post(
    "/commentary/generate",
    response_model=CompliantCommentary,
    status_code=status.HTTP_201_CREATED,
)
async def generate(
    request: GenerateCommentaryRequest,
    x_user_search_token: str | None = Header(default=None),
) -> CompliantCommentary:
    # Carry the signed-in advisor's delegated Search token for OBO grounding
    # (Fabric Data Agent knowledge source requires a user token, not the app SP).
    auth.set_user_search_token(x_user_search_token)
    settings = get_settings()
    try:
        commentary = await generate_commentary(
            mandate_id=request.mandate_id,
            period=request.period,
            audience=request.audience,
            jurisdictions=settings.jurisdictions,
            style=request.style,
            event_driven=request.resolved_trigger == BriefTrigger.EVENT,
            commentary_type=request.commentary_type,
        )
    except SubstantiationError as exc:
        # No fabricated numbers: any unresolved source_id blocks delivery.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUBSTANTIATED", "unresolved": exc.unresolved},
        ) from exc

    # Safety scan on the rendered narrative before persistence.
    rendered = " ".join(
        c.text for s in commentary.sections for c in s.claims
    )
    try:
        content_safety.check_text(rendered)
    except content_safety.ContentSafetyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONTENT_SAFETY", "message": str(exc)},
        ) from exc

    saved = commentary_store.save_commentary(commentary)
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.GENERATED,
            advisor_id="system",
            client_id=request.mandate_id,
            session_id=saved.id or "",
            mandate_id=request.mandate_id,
            action="commentary_generated",
            metadata={
                "period": request.period,
                "audience": request.audience.value,
                "trigger": request.resolved_trigger.value,
                "commentary_type": request.commentary_type.value,
                "compliance_status": saved.compliance_status.value,
            },
        )
    )
    return saved


@router.get("/commentary", response_model=list[CommentarySummary])
async def list_history(mandate_id: str = Query(...)) -> list[CommentarySummary]:
    """History of generated commentaries for a mandate, newest first."""
    items = commentary_store.list_commentary(mandate_id)
    return [_summarize(item) for item in items]


@router.get("/commentary/all", response_model=list[CommentarySummary])
async def list_all() -> list[CommentarySummary]:
    """Cross-mandate review queue of all generated commentaries, newest first."""
    items = commentary_store.list_all_commentary()
    return [_summarize(item) for item in items]


def _summarize(item: dict) -> CommentarySummary:
    approval = item.get("approval", {}) or {}
    return CommentarySummary(
        id=item.get("id", ""),
        mandate_id=item.get("mandate_id", ""),
        period=item.get("period", ""),
        audience=item.get("audience", "client"),
        commentary_type=item.get("commentary_type", "quarterly_review"),
        compliance_status=item.get("compliance_status", "passed"),
        pm_status=approval.get("pm_status", "pending"),
        compliance_approval=approval.get("compliance_status", "pending"),
        delivered=approval.get("delivered", False),
        updated_ts=item.get("_ts"),
    )


@router.get("/commentary/{commentary_id}", response_model=CompliantCommentary)
async def get(commentary_id: str, mandate_id: str) -> CompliantCommentary:
    item = commentary_store.get_commentary(commentary_id, mandate_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"Commentary {commentary_id} not found"},
        )
    return CompliantCommentary.model_validate(item)


@router.delete("/commentary/{commentary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(commentary_id: str, mandate_id: str = Query(...)) -> None:
    deleted = commentary_store.delete_commentary(commentary_id, mandate_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"Commentary {commentary_id} not found"},
        )
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.DELETED,
            advisor_id="system",
            client_id=mandate_id,
            session_id=commentary_id,
            mandate_id=mandate_id,
            action="commentary_deleted",
            metadata={},
        )
    )


@router.post("/commentary/{commentary_id}/recompliance", response_model=CompliantCommentary)
async def rerun_compliance(commentary_id: str, mandate_id: str = Query(...)) -> CompliantCommentary:
    """Re-run the compliance gate on a (possibly edited) commentary.

    Lets a PM/advisor edit the draft then re-check compliance. Resets the approval
    state (content changed) and returns the updated status (passed / rewritten /
    rejected) with any remaining violations.
    """
    item = commentary_store.get_commentary(commentary_id, mandate_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"Commentary {commentary_id} not found"},
        )

    draft = CommentaryDraft.model_validate(item)
    settings = get_settings()

    # Edited claims must still cite valid sources.
    unresolved = substantiation.substantiate(draft)
    if unresolved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUBSTANTIATED", "unresolved": unresolved},
        )

    compliant = compliance_guard_agent.enforce(draft, settings.jurisdictions)
    compliant.id = commentary_id

    rendered = " ".join(c.text for s in compliant.sections for c in s.claims)
    try:
        content_safety.check_text(rendered)
    except content_safety.ContentSafetyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONTENT_SAFETY", "message": str(exc)},
        ) from exc

    # Persist the re-checked commentary; save_commentary resets approval to pending
    # (edits invalidate any prior sign-off).
    saved = commentary_store.save_commentary(compliant)
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.EDITED,
            advisor_id="system",
            client_id=mandate_id,
            session_id=commentary_id,
            mandate_id=mandate_id,
            action="compliance_rechecked",
            metadata={"compliance_status": saved.compliance_status.value},
        )
    )
    return saved
