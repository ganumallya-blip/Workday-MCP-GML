"""OAuth2 Authorization Code + PKCE orchestration."""
from datetime import datetime, timedelta, timezone
import secrets
from urllib.parse import urlencode
import httpx
from src.audit.audit_logger import AuditLogger
from src.audit.models import AuditEvent
from src.auth.exceptions import AuthenticationRequired, InvalidOAuthState, RefreshFailed
from src.auth.models import AuthUrlResponse, OAuthState, TokenSession
from src.auth.pkce import generate_code_challenge, generate_code_verifier
from src.auth.state_store import OAuthStateStore
from src.auth.token_store import TokenStore
from src.config import Settings
from src.identity.models import RequestContext, UserIdentity

class OAuthManager:
    """Manages per-employee Workday OAuth sessions without impersonation support."""
    def __init__(self, settings: Settings, token_store: TokenStore, state_store: OAuthStateStore, audit_logger: AuditLogger) -> None:
        self.settings = settings
        self.token_store = token_store
        self.state_store = state_store
        self.audit_logger = audit_logger

    async def generate_authorization_url(self, context: RequestContext) -> AuthUrlResponse:
        """Create a Workday authorization URL bound to the resolved current user."""
        verifier = generate_code_verifier()
        state_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self.state_store.save(OAuthState(state=state_value, user_id=context.user.user_id, code_verifier=verifier, expires_at=expires_at))
        params = {
            "response_type": "code", "client_id": self.settings.workday_client_id,
            "redirect_uri": self.settings.workday_redirect_uri, "scope": self.settings.workday_scope,
            "state": state_value, "code_challenge": generate_code_challenge(verifier), "code_challenge_method": "S256",
        }
        url = f"{self.settings.workday_authorize_url}?{urlencode(params)}"
        await self.audit_logger.log(AuditEvent(request_id=context.request_id, event_type="oauth", actor_type="user", actor_id=context.user.user_id, action="auth_url_generated", target_user_id=context.user.user_id, status="success"))
        return AuthUrlResponse(authorization_url=url, state=state_value, expires_at=expires_at)

    async def exchange_authorization_code(self, code: str, state: str) -> TokenSession:
        """Validate OAuth state and exchange an authorization code for a token session."""
        oauth_state = await self.state_store.pop(state)
        if oauth_state is None:
            await self.audit_logger.log(AuditEvent(event_type="oauth", actor_type="unknown", actor_id="unknown", action="oauth_callback_failure", status="failure", metadata={"reason": "invalid_state"}))
            raise InvalidOAuthState("Invalid or expired OAuth state.")
        data = {
            "grant_type": "authorization_code", "client_id": self.settings.workday_client_id,
            "client_secret": self.settings.workday_client_secret, "redirect_uri": self.settings.workday_redirect_uri,
            "code": code, "code_verifier": oauth_state.code_verifier,
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
                response = await client.post(self.settings.workday_token_url, data=data)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            await self.audit_logger.log(AuditEvent(event_type="oauth", actor_type="user", actor_id=oauth_state.user_id, action="oauth_callback_failure", target_user_id=oauth_state.user_id, status="failure"))
            raise AuthenticationRequired("Unable to complete Workday authentication.") from exc
        session = self._session_from_payload(oauth_state.user_id, payload)
        await self.token_store.save(session)
        await self.audit_logger.log(AuditEvent(event_type="oauth", actor_type="user", actor_id=oauth_state.user_id, action="oauth_callback_success", target_user_id=oauth_state.user_id, status="success"))
        return session

    async def refresh_access_token(self, user: UserIdentity) -> TokenSession:
        """Refresh a Workday access token for the resolved current user."""
        session = await self.token_store.get(user.user_id)
        if not session or not session.refresh_token:
            raise AuthenticationRequired("Workday authentication required.")
        data = {"grant_type": "refresh_token", "client_id": self.settings.workday_client_id, "client_secret": self.settings.workday_client_secret, "refresh_token": session.refresh_token}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
                response = await client.post(self.settings.workday_token_url, data=data)
                response.raise_for_status()
                payload = response.json()
            refreshed = self._session_from_payload(user.user_id, payload, email=user.email, fallback_refresh_token=session.refresh_token)
            await self.token_store.save(refreshed)
            await self.audit_logger.log(AuditEvent(event_type="oauth", actor_type="user", actor_id=user.user_id, action="token_refreshed", target_user_id=user.user_id, status="success"))
            return refreshed
        except Exception as exc:
            await self.audit_logger.log(AuditEvent(event_type="oauth", actor_type="user", actor_id=user.user_id, action="token_refresh_failed", target_user_id=user.user_id, status="failure"))
            raise RefreshFailed("Token refresh failed.") from exc

    async def get_valid_access_token(self, user: UserIdentity) -> str:
        """Return a valid Workday access token for the resolved current user."""
        session = await self.token_store.get(user.user_id)
        if not session:
            raise AuthenticationRequired("Workday authentication required.")
        if not session.is_expired:
            return session.access_token
        try:
            return (await self.refresh_access_token(user)).access_token
        except RefreshFailed as exc:
            raise AuthenticationRequired("Workday authentication required.") from exc

    async def revoke_token(self, user: UserIdentity) -> None:
        await self.logout(user)

    async def revoke_user_id(self, user_id: str, actor_id: str = "admin") -> None:
        """Admin-only revocation by safe session metadata key; does not impersonate."""
        await self.token_store.delete(user_id)
        await self.audit_logger.log(AuditEvent(event_type="session", actor_type="admin", actor_id=actor_id, action="session_revoked", target_user_id=user_id, status="success"))

    async def logout(self, user: UserIdentity) -> None:
        await self.token_store.delete(user.user_id)
        await self.audit_logger.log(AuditEvent(event_type="session", actor_type="user", actor_id=user.user_id, action="session_revoked", target_user_id=user.user_id, status="success"))

    def _session_from_payload(self, user_id: str, payload: dict, email: str | None = None, fallback_refresh_token: str | None = None) -> TokenSession:
        expires_in = int(payload.get("expires_in", 3600))
        scopes = str(payload.get("scope", self.settings.workday_scope)).split()
        return TokenSession(user_id=user_id, email=email, access_token=payload["access_token"], refresh_token=payload.get("refresh_token") or fallback_refresh_token, expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in), scopes=scopes)
