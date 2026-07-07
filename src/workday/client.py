"""Workday API client scaffold for future business tools."""
from urllib.parse import urljoin
import httpx
from src.auth.exceptions import AuthenticationRequired
from src.auth.oauth_manager import OAuthManager
from src.config import Settings
from src.identity.models import RequestContext
from src.workday.exceptions import WorkdayAPIError

class WorkdayClient:
    """Minimal authenticated Workday client using per-user bearer tokens."""
    def __init__(self, settings: Settings, oauth_manager: OAuthManager) -> None:
        self.settings = settings
        self.oauth_manager = oauth_manager

    async def get(self, context: RequestContext, path: str, params: dict | None = None) -> dict:
        """Perform an authenticated GET against Workday for the current user."""
        return await self._request("GET", context, path, params=params)

    async def post(self, context: RequestContext, path: str, payload: dict | None = None) -> dict:
        """Perform an authenticated POST against Workday for the current user."""
        return await self._request("POST", context, path, json=payload)

    async def _request(self, method: str, context: RequestContext, path: str, **kwargs) -> dict:
        token = await self.oauth_manager.get_valid_access_token(context.user)
        response = await self._send(method, token, path, **kwargs)
        if response.status_code == 401:
            try:
                refreshed = await self.oauth_manager.refresh_access_token(context.user)
            except Exception as exc:
                raise AuthenticationRequired("Workday authentication required.") from exc
            response = await self._send(method, refreshed.access_token, path, **kwargs)
        if response.status_code < 200 or response.status_code >= 300:
            raise WorkdayAPIError("Workday returned a non-success response.", status_code=response.status_code)
        if not response.content:
            return {}
        return response.json()

    async def _send(self, method: str, token: str, path: str, **kwargs) -> httpx.Response:
        url = urljoin(self.settings.workday_base_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
                return await client.request(method, url, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise WorkdayAPIError("Workday request timed out.") from exc
        except httpx.HTTPError as exc:
            raise WorkdayAPIError("Workday request failed.") from exc

    # TODO: Add concrete Workday REST/SOAP business endpoint methods in Phase 2.
