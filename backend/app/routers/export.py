"""Export endpoints — download an approved brief as PDF / Word, or as an email."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.models.approvals import AuditEventType, AuditRecord
from app.models.commentary import CompliantCommentary
from app.services import audit, commentary_store, export

logger = logging.getLogger(__name__)
router = APIRouter()


def _load(commentary_id: str, mandate_id: str) -> CompliantCommentary:
    item = commentary_store.get_commentary(commentary_id, mandate_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"Commentary {commentary_id} not found"},
        )
    return CompliantCommentary.model_validate(item)


def _audit_export(commentary: CompliantCommentary, fmt: str) -> None:
    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.DELIVERED,
            advisor_id="system",
            client_id=commentary.mandate_id,
            session_id=commentary.id or "",
            mandate_id=commentary.mandate_id,
            action=f"commentary_exported_{fmt}",
            metadata={"format": fmt, "period": commentary.period},
        )
    )


@router.get("/commentary/{commentary_id}/export/pdf")
async def export_pdf(commentary_id: str, mandate_id: str) -> Response:
    commentary = _load(commentary_id, mandate_id)
    try:
        data = export.to_pdf(commentary)
    except export.ExportUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail={"code": "EXPORT_UNAVAILABLE", "message": str(exc)}) from exc
    _audit_export(commentary, "pdf")
    filename = f"{commentary.mandate_id}_{commentary.period}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/commentary/{commentary_id}/export/docx")
async def export_docx(commentary_id: str, mandate_id: str) -> Response:
    commentary = _load(commentary_id, mandate_id)
    try:
        data = export.to_docx(commentary)
    except export.ExportUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail={"code": "EXPORT_UNAVAILABLE", "message": str(exc)}) from exc
    _audit_export(commentary, "docx")
    filename = f"{commentary.mandate_id}_{commentary.period}.docx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/commentary/{commentary_id}/export/email")
async def export_email(commentary_id: str, mandate_id: str, to: str = Query(...)) -> Response:
    commentary = _load(commentary_id, mandate_id)
    data = export.to_eml(commentary, to_address=to)
    _audit_export(commentary, "email")
    filename = f"{commentary.mandate_id}_{commentary.period}.eml"
    return Response(
        content=data,
        media_type="message/rfc822",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
