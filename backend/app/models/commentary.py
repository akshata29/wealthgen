"""Commentary domain + request/response models.

The commentary contract enforces "every number ties to a source": each
`SourcedClaim` carries a `source_id` that must resolve in `source_map`, else the
substantiation gate rejects the draft.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Audience(str, Enum):
    CLIENT = "client"
    INSTITUTIONAL = "institutional"
    IC = "ic"


class SectionHeading(str, Enum):
    EXECUTIVE_SUMMARY = "Executive Summary"
    MARKET_CONTEXT = "Market Context"
    PERFORMANCE_ATTRIBUTION = "Performance Attribution"
    POSITIONING_CHANGES = "Positioning Changes"
    HOUSE_VIEW_OUTLOOK = "House View & Outlook"
    RISK_COMPLIANCE = "Risk & Compliance Note"
    NEXT_STEPS = "Next Steps"


class ComplianceStatus(str, Enum):
    PASSED = "passed"
    REWRITTEN = "rewritten"
    REJECTED = "rejected"


class Tone(str, Enum):
    WARM = "warm"
    NEUTRAL = "neutral"
    FORMAL = "formal"


class Literacy(str, Enum):
    NOVICE = "novice"
    INFORMED = "informed"
    EXPERT = "expert"


class BriefTrigger(str, Enum):
    SCHEDULED = "scheduled"
    AD_HOC = "ad_hoc"
    EVENT = "event"


class NarrativeStyle(BaseModel):
    """The tone/ease dials read by the narrative generator (see tone_playbook)."""

    tone: Tone = Tone.NEUTRAL
    literacy: Literacy = Literacy.INFORMED
    non_financial_language: bool = False


class SourcedClaim(BaseModel):
    text: str
    value: str | None = Field(None, description="e.g. '+3.2%', '+35 bps'")
    source_id: str = Field(..., description="Must resolve in CommentaryDraft.source_map")
    confidence: float | None = Field(None, ge=0.0, le=1.0)


class CommentarySection(BaseModel):
    heading: SectionHeading
    claims: list[SourcedClaim] = Field(default_factory=list)


class CommentaryDraft(BaseModel):
    mandate_id: str
    period: str = Field(..., description="e.g. 'Q2-2026'")
    audience: Audience = Audience.CLIENT
    sections: list[CommentarySection] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    source_map: dict[str, str] = Field(
        default_factory=dict, description="source_id -> human-readable citation"
    )


class CompliantCommentary(CommentaryDraft):
    id: str | None = None
    compliance_status: ComplianceStatus = ComplianceStatus.PASSED
    inserted_disclaimers: list[str] = Field(default_factory=list)
    rejections: list[str] = Field(default_factory=list)


class GenerateCommentaryRequest(BaseModel):
    mandate_id: str
    period: str
    audience: Audience = Audience.CLIENT
    style: NarrativeStyle | None = Field(
        None, description="Tone / ease dials; defaults to audience-appropriate values"
    )
    trigger: BriefTrigger = Field(
        BriefTrigger.SCHEDULED, description="What prompted the brief (scheduled | ad_hoc | event)"
    )
    event_period: str | None = Field(
        None, description="For event-driven briefs, the period of the triggering market event"
    )
    end_user_token: str | None = Field(
        None, description="OBO token for Work IQ / Fabric IQ query-time auth"
    )


class ReviewCommentaryRequest(BaseModel):
    sections: list[CommentarySection] | None = None
    pm_status: str | None = Field(None, description="approved | changes_requested")
    advisor_id: str


class ApproveCommentaryRequest(BaseModel):
    role: str = Field(..., description="pm | compliance")
    approver_id: str
