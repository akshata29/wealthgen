"""PDF ingest — upload -> content safety -> blob -> Content Understanding -> index."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.agents import document_intelligence_agent
from app.models.approvals import AuditEventType, AuditRecord
from app.services import audit, content_safety
from app.services.blob import upload_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest(
    mandate_id: str = Form(...),
    advisor_id: str = Form(...),
    client_id: str = Form(...),
    session_id: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    all_facts = 0
    all_chunks = 0
    needs_review: list[str] = []
    for upload in files:
        data = await upload.read()
        # Content Safety on the extracted-first-page text is done inside the agent;
        # here we guard the filename/simple metadata boundary.
        try:
            content_safety.check_text(upload.filename or "")
        except content_safety.ContentSafetyError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CONTENT_SAFETY", "message": str(exc)},
            ) from exc

        filename = upload.filename or "factsheet.pdf"
        # Persist the source PDF for audit/storage; ingestion runs on the bytes.
        upload_pdf(mandate_id, filename, data)
        result = document_intelligence_agent.ingest_factsheet(mandate_id, filename, data)
        all_chunks += result.chunks_indexed
        all_facts += result.facts_indexed
        needs_review.extend(result.needs_review)

    audit.write_audit(
        AuditRecord(
            event_type=AuditEventType.INGESTED,
            advisor_id=advisor_id,
            client_id=client_id,
            session_id=session_id,
            mandate_id=mandate_id,
            action="documents_ingested",
            metadata={
                "facts_indexed": all_facts,
                "chunks_indexed": all_chunks,
                "files": len(files),
            },
        )
    )
    return {
        "mandate_id": mandate_id,
        "facts_indexed": all_facts,
        "chunks_indexed": all_chunks,
        "needs_review": needs_review,
    }
