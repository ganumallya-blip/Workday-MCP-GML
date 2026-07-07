"""MCP authentication tool implementation."""
from src.auth.exceptions import AuthenticationRequired
from src.services import oauth_manager

async def authenticate_workday(user_id: str) -> dict[str, str]:
    """Return Workday auth status or a per-user authorization URL."""
    try:
        await oauth_manager.get_valid_access_token(user_id)
        return {"status": "authenticated", "message": "Already authenticated."}
    except AuthenticationRequired:
        auth_url = await oauth_manager.generate_authorization_url(user_id)
        return {"status": "authentication_required", "authorization_url": auth_url.authorization_url, "message": "Please sign in to Workday."}
