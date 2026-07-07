"""Identity provider abstractions for MCP/client authentication (Layer 1)."""
from abc import ABC, abstractmethod
from typing import Any
from src.auth.exceptions import AuthenticationRequired
from src.config import Settings
from src.identity.models import UserIdentity

class IdentityProvider(ABC):
    """Resolve the authenticated MCP/client user from a trusted request context."""
    @abstractmethod
    async def get_current_user(self, request: Any | None = None) -> UserIdentity: ...

class DevIdentityProvider(IdentityProvider):
    """Local-only identity provider using X-Dev-User or DEV_USER_ID."""
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get_current_user(self, request: Any | None = None) -> UserIdentity:
        header_user = self._header(request, "x-dev-user")
        if self.settings.app_env != "local":
            if header_user:
                raise AuthenticationRequired("X-Dev-User is only allowed when APP_ENV=local.")
            raise AuthenticationRequired("Production identity provider is not configured.")
        if not self.settings.dev_auth_enabled:
            raise AuthenticationRequired("Development identity is disabled.")
        user_id = header_user or self.settings.dev_user_id
        if not user_id:
            raise AuthenticationRequired("DEV_USER_ID is required for local development identity.")
        return UserIdentity(user_id=user_id, email=self.settings.dev_user_email, display_name=self.settings.dev_user_display_name, auth_source="dev")

    def _header(self, request: Any | None, name: str) -> str | None:
        if request is None or not hasattr(request, "headers"):
            return None
        return request.headers.get(name) or request.headers.get(name.title()) or None

class FutureIdentityProvider(IdentityProvider):
    """Placeholder for production identity validation."""
    async def get_current_user(self, request: Any | None = None) -> UserIdentity:
        # TODO: Validate Entra ID JWTs for Microsoft 365 Copilot and enterprise clients.
        # TODO: Validate Copilot Studio authentication context and claims.
        # TODO: Add generic OAuth/JWT validation for ChatGPT, Claude, web, and mobile clients.
        raise AuthenticationRequired("Production identity provider is not implemented yet.")
