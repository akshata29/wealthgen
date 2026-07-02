import pytest
from pydantic import ValidationError

from app.models.commentary import CommentaryDraft


def test_valid_contract_parses() -> None:
    payload = {
        "mandate_id": "m1",
        "period": "Q2-2026",
        "audience": "client",
        "sections": [
            {
                "heading": "Executive Summary",
                "claims": [{"text": "Returned", "value": "+3.2%", "source_id": "s1"}],
            }
        ],
        "source_map": {"s1": "IBOR net return"},
    }
    draft = CommentaryDraft.model_validate(payload)
    assert draft.sections[0].claims[0].source_id == "s1"


def test_claim_missing_source_id_rejected() -> None:
    payload = {
        "mandate_id": "m1",
        "period": "Q2-2026",
        "sections": [{"heading": "Executive Summary", "claims": [{"text": "Returned"}]}],
    }
    with pytest.raises(ValidationError):
        CommentaryDraft.model_validate(payload)


def test_invalid_section_heading_rejected() -> None:
    payload = {
        "mandate_id": "m1",
        "period": "Q2-2026",
        "sections": [{"heading": "Not A Section", "claims": []}],
    }
    with pytest.raises(ValidationError):
        CommentaryDraft.model_validate(payload)
