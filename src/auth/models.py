"""Pydantic models for OAuth and token sessions."""
from datetime import datetime, timezone
from enum import Enum
try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback for minimal test environments
    class BaseModel:
        def __init__(self, **data):
            for name, value in self.__class__.__dict__.items():
                if name.startswith("_") or callable(value) or isinstance(value, property):
                    continue
                if name not in data:
                    setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

    class _FieldInfo:
        def __init__(self, default=None, default_factory=None):
            self.default = default_factory() if default_factory else default

    def Field(default=None, default_factory=None):
        return default_factory() if default_factory else default

class AuthStatus(str, Enum):
    authenticated = "authenticated"
    authentication_required = "authentication_required"
    expired = "expired"
    refresh_failed = "refresh_failed"

class TokenSession(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime
    scopes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= datetime.now(timezone.utc)

class AuthUrlResponse(BaseModel):
    authorization_url: str
    state: str
    expires_at: datetime

class OAuthState(BaseModel):
    state: str
    user_id: str
    code_verifier: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

class TokenMetadata(BaseModel):
    user_id: str
    authenticated: bool
    expires_at: datetime | None = None
    scopes: list[str] = Field(default_factory=list)
    token_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_used_at: datetime | None = None
