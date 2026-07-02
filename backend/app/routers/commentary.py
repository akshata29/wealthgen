"""Commentary generation and retrieval endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.infra.settings import get_settings
from app.models.approvals import AuditEventType, AuditRecord
from app.models.commentary import (
    Audience,
    BriefTrigger,
    ComplianceStatus,
    CompliantCommentary,
    GenerateCommentaryRequest,
)
from app.orchestration.commentary_workflow import SubstantiationError, generate_commentary
from app.services import audit, commentary_store, content_safety

logger = logging.getLogger(__name__)
router = APIRouter()


class CommentarySummary(BaseModel):
    """Lightweight history row for a mandate's generated commentaries."""

    id: str
    mandate_id: str
    period: str
    audience: Audience
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
async def generate(request: GenerateCommentaryRequest) -> CompliantCommentary:
    settings = get_settings()
    try:
        commentary = await generate_commentary(
            mandate_id=request.mandate_id,
            period=request.period,
            audience=request.audience,
            jurisdictions=settings.jurisdictions,
            style=request.style,
            event_driven=request.trigger == BriefTrigger.EVENT,
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
                "trigger": request.trigger.value,
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
