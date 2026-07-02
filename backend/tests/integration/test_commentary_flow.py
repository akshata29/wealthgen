"""Approval gate flow — delivery is blocked until PM + Compliance both approve."""

from app.models.approvals import ApprovalState, ApprovalStatus


def test_delivery_blocked_until_both_approve() -> None:
    state = ApprovalState(commentary_id="c1")
    assert not state.can_deliver

    state.pm_status = ApprovalStatus.APPROVED
    assert not state.can_deliver

    state.compliance_status = ApprovalStatus.APPROVED
    assert state.can_deliver
