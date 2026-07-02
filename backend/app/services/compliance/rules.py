"""Deterministic compliance rule engine (UK FCA + US SEC/FINRA).

Runs BEFORE any LLM pass. Blocks forbidden language, enforces fair-and-balanced
and gross/net pairing, and routes jurisdiction-specific disclosure requirements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.commentary import CommentaryDraft, SectionHeading

# Promissory / guarantee / prediction language forbidden in marketing comms.
FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bguarantee(d|s)?\b",
        r"\brisk[- ]free\b",
        r"\bwill\s+outperform\b",
        r"\bassured?\b",
        r"\bpromise(d|s)?\b",
        r"\bprotected\b",
        r"\bsecure\s+returns?\b",
        r"\bcertain\s+to\b",
        r"\bno\s+risk\b",
    )
]

# Words that indicate a gross performance figure requiring a net counterpart.
GROSS_MARKER = re.compile(r"\bgross\b", re.IGNORECASE)
NET_MARKER = re.compile(r"\bnet\b", re.IGNORECASE)


@dataclass
class Violation:
    section: str
    kind: str  # forbidden_language | not_balanced | gross_without_net
    detail: str
    suggested_rewrite: str | None = None


def route_jurisdiction(jurisdictions: list[str]) -> list[str]:
    return [j.upper() for j in jurisdictions if j.upper() in {"UK", "US"}]


def check_forbidden_language(draft: CommentaryDraft) -> list[Violation]:
    violations: list[Violation] = []
    for section in draft.sections:
        for claim in section.claims:
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(claim.text):
                    violations.append(
                        Violation(
                            section=section.heading.value,
                            kind="forbidden_language",
                            detail=f"Forbidden phrase matched '{pattern.pattern}': {claim.text!r}",
                        )
                    )
    return violations


def check_fair_and_balanced(draft: CommentaryDraft) -> list[Violation]:
    """Attribution section must include at least one detractor when contributors are present."""
    for section in draft.sections:
        if section.heading != SectionHeading.PERFORMANCE_ATTRIBUTION:
            continue
        text = " ".join(c.text.lower() for c in section.claims)
        has_positive = any(w in text for w in ("contribut", "gain", "added", "positive"))
        has_negative = any(w in text for w in ("detract", "loss", "cost", "negative", "trailed"))
        if has_positive and not has_negative:
            return [
                Violation(
                    section=section.heading.value,
                    kind="not_balanced",
                    detail="Contributors present with no detractors; add balancing detail.",
                )
            ]
    return []


def check_gross_net(draft: CommentaryDraft) -> list[Violation]:
    violations: list[Violation] = []
    for section in draft.sections:
        for claim in section.claims:
            if GROSS_MARKER.search(claim.text) and not NET_MARKER.search(claim.text):
                violations.append(
                    Violation(
                        section=section.heading.value,
                        kind="gross_without_net",
                        detail=f"Gross performance without net counterpart: {claim.text!r}",
                    )
                )
    return violations


def run_all(draft: CommentaryDraft) -> list[Violation]:
    return [
        *check_forbidden_language(draft),
        *check_fair_and_balanced(draft),
        *check_gross_net(draft),
    ]
