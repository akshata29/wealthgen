"""Approval gate flow — delivery is blocked until PM + Compliance both approve."""

import pytest
from pydantic import ValidationError

from app.infra.settings import Settings
from app.models.approvals import ApprovalState, ApprovalStatus


# Minimal set of otherwise-required Azure settings so only the fabric guard fails.
_REQUIRED = dict(
    foundry_endpoint="https://x.services.ai.azure.com/api/projects/p",
    search_endpoint="https://x.search.windows.net",
    kb_connection_name="kb-remote-tool",
    cu_endpoint="https://x.services.ai.azure.com/",
    cosmos_endpoint="https://x.documents.azure.com:443/",
    content_safety_endpoint="https://x.cognitiveservices.azure.com/",
)


def test_fabric_mode_requires_sql_endpoint_and_database() -> None:
    with pytest.raises(ValidationError, match="FABRIC_SQL_ENDPOINT"):
        Settings(_env_file=None, data_source_mode="fabric", **_REQUIRED)


def test_fabric_mode_valid_when_configured() -> None:
    settings = Settings(
        _env_file=None,
        data_source_mode="fabric",
        fabric_sql_endpoint="wh.datawarehouse.fabric.microsoft.com",
        fabric_database="wealthgen-wh",
        **_REQUIRED,
    )
    assert settings.data_source_mode == "fabric"


def test_delivery_blocked_until_both_approve() -> None:
    state = ApprovalState(commentary_id="c1")
    assert not state.can_deliver

    state.pm_status = ApprovalStatus.APPROVED
    assert not state.can_deliver

    state.compliance_status = ApprovalStatus.APPROVED
    assert state.can_deliver
