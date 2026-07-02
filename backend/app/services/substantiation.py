"""Substantiation gate — the "no fabricated numbers" enforcement.

Every SourcedClaim must reference a source_id present in the draft's source_map.
Any unresolved claim id is returned; the router rejects the draft (HTTP 422) when
the list is non-empty.
"""

from __future__ import annotations

from app.models.commentary import CommentaryDraft


def substantiate(draft: CommentaryDraft) -> list[str]:
    """Return the ids of claims whose source_id does not resolve in source_map."""
    unresolved: list[str] = []
    for section in draft.sections:
        for claim in section.claims:
            if claim.source_id not in draft.source_map:
                unresolved.append(claim.source_id)
    return unresolved
