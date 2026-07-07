"""Identity and request context models for MCP/client authentication."""
from datetime import datetime, timezone
import secrets
try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover
    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)
        def model_dump(self):
            return dict(self.__dict__)
    def Field(default=None, default_factory=None):
        return default_factory() if default_factory else default

class UserIdentity(BaseModel):
    """Authenticated MCP/client user identity resolved from request context."""
    user_id: str
    email: str | None = None
    display_name: str | None = None
    auth_source: str
    tenant_id: str | None = None
    roles: list[str] = Field(default_factory=list)

class RequestContext(BaseModel):
    """Per-request context passed to tools and service layers."""
    request_id: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    user: UserIdentity
    client_type: str | None = None
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
