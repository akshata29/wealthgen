from app.models.approvals import AuditEventType, AuditRecord
from app.services.audit import mask_pii


def test_mask_pii_keeps_last_four() -> None:
    assert mask_pii("HFO-0421") == "****0421"
    assert mask_pii("12") == "12"


def test_audit_record_shape() -> None:
    record = AuditRecord(
        event_type=AuditEventType.GENERATED,
        advisor_id="adv-1",
        client_id="HFO-0421",
        session_id="sess-1",
        mandate_id="m1",
        action="commentary_generated",
        metadata={"period": "Q2-2026"},
    )
    data = record.model_dump(mode="json")
    assert data["type"] == "audit"
    assert data["event_type"] == "commentary_generated"
    assert data["mandate_id"] == "m1"
    assert "timestamp" in data
