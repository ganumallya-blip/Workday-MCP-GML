"""Audit event model."""
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None
    event_type: str
    actor_type: str
    actor_id: str
    action: str
    target_user_id: str | None = None
    status: str
    metadata: dict[str, str | int | bool | None] = Field(default_factory=dict)
