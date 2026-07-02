"""ComplianceGuardAgent — deterministic gate first, then disclosure insertion.

1. Run the deterministic rule engine (forbidden language, fair-&-balanced, gross/net).
2. If forbidden language is present, reject with structured reasons for the PM.
3. Insert jurisdiction-routed approved disclaimers (never free-written).

An optional LLM tone pass can be layered on later; the deterministic gate is the
compliance-by-construction backbone and runs with no model dependency.
"""

from __future__ import annotations

import logging

from app.models.commentary import (
    CommentaryDraft,
    ComplianceStatus,
    CompliantCommentary,
)
from app.services.compliance import disclosures, rules

logger = logging.getLogger(__name__)


def enforce(draft: CommentaryDraft, jurisdictions: list[str]) -> CompliantCommentary:
    active = rules.route_jurisdiction(jurisdictions)
    violations = rules.run_all(draft)

    forbidden = [v for v in violations if v.kind == "forbidden_language"]
    other = [v for v in violations if v.kind != "forbidden_language"]

    selected = disclosures.select_disclaimers(active)

    if forbidden:
        logger.warning("Compliance rejected draft: %d forbidden-language violations.", len(forbidden))
        return CompliantCommentary(
            **draft.model_dump(),
            compliance_status=ComplianceStatus.REJECTED,
            inserted_disclaimers=selected,
            rejections=[v.detail for v in (*forbidden, *other)],
        )

    status = ComplianceStatus.REWRITTEN if other else ComplianceStatus.PASSED
    merged = list(dict.fromkeys([*draft.disclaimers, *selected]))
    payload = draft.model_dump()
    payload["disclaimers"] = merged
    return CompliantCommentary(
        **payload,
        compliance_status=status,
        inserted_disclaimers=selected,
        rejections=[v.detail for v in other],
    )
