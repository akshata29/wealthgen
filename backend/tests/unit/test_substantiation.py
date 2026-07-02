from app.models.commentary import (
    CommentaryDraft,
    CommentarySection,
    SectionHeading,
    SourcedClaim,
)
from app.services import substantiation


def _draft(source_map: dict[str, str], source_id: str) -> CommentaryDraft:
    return CommentaryDraft(
        mandate_id="m1",
        period="Q2-2026",
        sections=[
            CommentarySection(
                heading=SectionHeading.PERFORMANCE_ATTRIBUTION,
                claims=[SourcedClaim(text="Allocation added", value="+35 bps", source_id=source_id)],
            )
        ],
        source_map=source_map,
    )


def test_resolved_source_passes() -> None:
    draft = _draft({"attr:alloc": "Allocation +35 bps"}, "attr:alloc")
    assert substantiation.substantiate(draft) == []


def test_unresolved_source_is_flagged() -> None:
    draft = _draft({"attr:alloc": "Allocation +35 bps"}, "attr:missing")
    assert substantiation.substantiate(draft) == ["attr:missing"]
