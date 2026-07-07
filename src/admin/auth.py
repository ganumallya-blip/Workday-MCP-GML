"""Local admin authentication for Phase 1 operations console."""
from datetime import datetime, timedelta, timezone
import secrets
from fastapi import Depends, Header, HTTPException
from passlib.context import CryptContext
from src.admin.schemas import AdminAuthenticationFailed
from src.audit.models import AuditEvent
from src.config import Settings
from src.services import audit_logger, settings
from src.utils.security import constant_time_equals

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_sessions: dict[str, tuple[str, datetime]] = {}

class AdminAuthService:
    """Session-token based local admin auth. TODO: replace with Entra ID/enterprise SSO."""
    def __init__(self, app_settings: Settings) -> None:
        self.settings = app_settings

    async def login(self, username: str, password: str) -> tuple[str, int]:
        if not self._verify(username, password):
            await audit_logger.log(AuditEvent(event_type="admin", actor_type="admin", actor_id=username, action="admin_login", status="failure"))
            raise AdminAuthenticationFailed("Invalid admin credentials.")
        token = secrets.token_urlsafe(48)
        ttl = self.settings.admin_session_ttl_minutes * 60
        _sessions[token] = (username, datetime.now(timezone.utc) + timedelta(seconds=ttl))
        await audit_logger.log(AuditEvent(event_type="admin", actor_type="admin", actor_id=username, action="admin_login", status="success"))
        return token, ttl

    def validate(self, token: str) -> str:
        if not self.settings.admin_auth_enabled:
            return "admin-auth-disabled"
        session = _sessions.get(token)
        if session is None or session[1] <= datetime.now(timezone.utc):
            _sessions.pop(token, None)
            raise AdminAuthenticationFailed("Invalid or expired admin session.")
        return session[0]

    def _verify(self, username: str, password: str) -> bool:
        if not constant_time_equals(username, self.settings.admin_username):
            return False
        if self.settings.admin_password_hash:
            return pwd_context.verify(password, self.settings.admin_password_hash)
        if self.settings.admin_password and self.settings.app_env == "local":
            return constant_time_equals(password, self.settings.admin_password)
        return False

admin_auth_service = AdminAuthService(settings)

async def require_admin(authorization: str | None = Header(default=None)) -> str:
    if not settings.admin_auth_enabled:
        return "admin-auth-disabled"
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Admin authentication required.")
    try:
        return admin_auth_service.validate(authorization.split(" ", 1)[1])
    except AdminAuthenticationFailed as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
