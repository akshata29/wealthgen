"""Source facts and citations — the grounding backbone.

Every numeric or factual claim in generated commentary must reference a
`source_id` that resolves to a `SourceFact` here (see substantiation service).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SourceOrigin(str, Enum):
    CONTENT_UNDERSTANDING = "content_understanding"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    FABRIC_IQ = "fabric_iq"
    WORK_IQ = "work_iq"
    WEB_IQ = "web_iq"
    LSEG = "lseg"


class SourceFact(BaseModel):
    source_id: str = Field(..., description="Stable id, e.g. 'attr:tech:selection'")
    origin: SourceOrigin
    label: str = Field(..., description="Human-readable description of the datum")
    value: str | None = Field(None, description="Normalised value, e.g. '+28 bps'")
    unit: str | None = None
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Content Understanding field confidence"
    )
    region: str | None = Field(None, description="Page/bounding region for traceability")


class Citation(BaseModel):
    source_id: str
    display: str
    url: str | None = None


SourceMap = dict[str, SourceFact]
