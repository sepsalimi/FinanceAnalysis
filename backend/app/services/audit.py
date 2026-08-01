"""Audit event helpers."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def record_audit(
    db: Session,
    *,
    household_id: UUID | None,
    user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    previous_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    request_id: str | None = None,
    job_id: UUID | None = None,
) -> AuditEvent:
    event = AuditEvent(
        household_id=household_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_value=previous_value,
        new_value=new_value,
        request_id=request_id,
        job_id=job_id,
    )
    db.add(event)
    return event
