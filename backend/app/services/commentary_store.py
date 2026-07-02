"""Cosmos DB persistence for commentary drafts, versions, and approval state.

Partition key: /mandate_id. Point reads by (id, mandate_id) — no cross-partition
queries in the hot path (see cosmosdb-best-practices).
"""

from __future__ import annotations

import logging
import uuid

from azure.cosmos import exceptions

from app.infra.clients import get_cosmos_client
from app.infra.settings import get_settings
from app.models.approvals import ApprovalState, ApprovalStatus
from app.models.commentary import CompliantCommentary

logger = logging.getLogger(__name__)


def _container():
    settings = get_settings()
    client = get_cosmos_client()
    db = client.get_database_client(settings.cosmos_database)
    return db.get_container_client(settings.cosmos_container)


def save_commentary(commentary: CompliantCommentary) -> CompliantCommentary:
    commentary.id = commentary.id or f"cmt-{uuid.uuid4()}"
    item = commentary.model_dump(mode="json")
    item["type"] = "commentary"
    item["approval"] = ApprovalState(commentary_id=commentary.id).model_dump(mode="json")
    _container().upsert_item(item)
    logger.info("Saved commentary %s (mandate %s).", commentary.id, commentary.mandate_id)
    return commentary


def get_commentary(commentary_id: str, mandate_id: str) -> dict | None:
    try:
        return _container().read_item(item=commentary_id, partition_key=mandate_id)
    except exceptions.CosmosResourceNotFoundError:
        return None


def list_commentary(mandate_id: str) -> list[dict]:
    """List commentary items for a mandate (single-partition query, newest first)."""
    items = list(
        _container().query_items(
            query="SELECT * FROM c WHERE c.type = 'commentary'",
            partition_key=mandate_id,
        )
    )
    items.sort(key=lambda x: x.get("_ts", 0), reverse=True)
    return items


def list_all_commentary() -> list[dict]:
    """List commentary across all mandates (cross-partition; newest first).

    Intended for a compliance review queue — not the hot path. Kept lean by the
    small demo dataset; add continuation/paging before production scale.
    """
    items = list(
        _container().query_items(
            query="SELECT * FROM c WHERE c.type = 'commentary'",
            enable_cross_partition_query=True,
        )
    )
    items.sort(key=lambda x: x.get("_ts", 0), reverse=True)
    return items


def update_sections(commentary_id: str, mandate_id: str, sections: list[dict]) -> dict | None:
    item = get_commentary(commentary_id, mandate_id)
    if item is None:
        return None
    item.setdefault("versions", []).append({"sections": item.get("sections", [])})
    item["sections"] = sections
    _container().upsert_item(item)
    return item


def update_approval(
    commentary_id: str, mandate_id: str, role: str
) -> ApprovalState | None:
    item = get_commentary(commentary_id, mandate_id)
    if item is None:
        return None
    approval = ApprovalState.model_validate(item.get("approval", {"commentary_id": commentary_id}))
    if role == "pm":
        approval.pm_status = ApprovalStatus.APPROVED
    elif role == "compliance":
        approval.compliance_status = ApprovalStatus.APPROVED
    item["approval"] = approval.model_dump(mode="json")
    _container().upsert_item(item)
    return approval


def mark_delivered(commentary_id: str, mandate_id: str) -> ApprovalState | None:
    item = get_commentary(commentary_id, mandate_id)
    if item is None:
        return None
    approval = ApprovalState.model_validate(item.get("approval", {"commentary_id": commentary_id}))
    approval.delivered = True
    item["approval"] = approval.model_dump(mode="json")
    _container().upsert_item(item)
    return approval
