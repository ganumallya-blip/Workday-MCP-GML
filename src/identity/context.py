"""Request context resolver."""
from typing import Any
import secrets
from src.identity.models import RequestContext
from src.identity.provider import IdentityProvider

class ContextResolver:
    """Build RequestContext objects from a trusted IdentityProvider."""
    def __init__(self, identity_provider: IdentityProvider) -> None:
        self.identity_provider = identity_provider

    async def resolve(self, request: Any | None = None) -> RequestContext:
        user = await self.identity_provider.get_current_user(request)
        headers = getattr(request, "headers", {}) if request is not None else {}
        has_get = hasattr(headers, "get")
        return RequestContext(
            request_id=headers.get("x-request-id", secrets.token_urlsafe(16)) if has_get else secrets.token_urlsafe(16),
            user=user,
            client_type=headers.get("x-client-type") if has_get else None,
            correlation_id=headers.get("x-correlation-id") if has_get else None,
        )
