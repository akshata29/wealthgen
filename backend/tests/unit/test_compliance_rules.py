from app.agents import compliance_guard_agent
from app.models.commentary import (
    CommentaryDraft,
    CommentarySection,
    ComplianceStatus,
    SectionHeading,
    SourcedClaim,
)
from app.services.compliance import disclosures, rules


def _draft(text: str, heading: SectionHeading = SectionHeading.HOUSE_VIEW_OUTLOOK) -> CommentaryDraft:
    return CommentaryDraft(
        mandate_id="m1",
        period="Q2-2026",
        sections=[
            CommentarySection(
                heading=heading,
                claims=[SourcedClaim(text=text, source_id="s1")],
            )
        ],
        source_map={"s1": "source"},
    )


def test_forbidden_language_blocked() -> None:
    violations = rules.check_forbidden_language(_draft("This fund is guaranteed to outperform."))
    assert any(v.kind == "forbidden_language" for v in violations)


def test_gross_without_net_flagged() -> None:
    violations = rules.check_gross_net(_draft("Returned +5.0% gross this quarter."))
    assert any(v.kind == "gross_without_net" for v in violations)


def test_fair_and_balanced_requires_detractor() -> None:
    draft = _draft("Technology contributed strongly.", SectionHeading.PERFORMANCE_ATTRIBUTION)
    violations = rules.check_fair_and_balanced(draft)
    assert any(v.kind == "not_balanced" for v in violations)


def test_disclaimers_inserted_per_jurisdiction() -> None:
    uk_us = disclosures.select_disclaimers(["UK", "US"])
    assert any("not a reliable indicator" in d for d in uk_us)
    assert any("net of fees" in d for d in uk_us)


def test_guard_rejects_forbidden_language() -> None:
    result = compliance_guard_agent.enforce(
        _draft("Returns are guaranteed."), ["UK", "US"]
    )
    assert result.compliance_status == ComplianceStatus.REJECTED
    assert result.rejections


def test_guard_passes_clean_draft_and_inserts_disclaimers() -> None:
    result = compliance_guard_agent.enforce(
        _draft("The mandate returned +3.2% net of fees."), ["UK", "US"]
    )
    assert result.compliance_status in (ComplianceStatus.PASSED, ComplianceStatus.REWRITTEN)
    assert result.inserted_disclaimers
