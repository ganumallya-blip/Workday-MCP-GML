"""MCP authentication tool implementation."""
from src.auth.exceptions import AuthenticationRequired
from src.identity.models import RequestContext
from src.services import context_resolver, oauth_manager

async def authenticate_workday(context: RequestContext | None = None) -> dict[str, str]:
    """Return Workday auth status or a per-user authorization URL for the current user."""
    resolved_context = context or await context_resolver.resolve(None)
    try:
        await oauth_manager.get_valid_access_token(resolved_context.user)
        return {"status": "authenticated", "message": "Already authenticated."}
    except AuthenticationRequired:
        auth_url = await oauth_manager.generate_authorization_url(resolved_context)
        return {"status": "authentication_required", "authorization_url": auth_url.authorization_url, "message": "Please sign in to Workday."}
