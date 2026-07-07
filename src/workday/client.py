"""Workday API client scaffold for future business tools."""
from urllib.parse import urljoin
import httpx
from src.auth.oauth_manager import OAuthManager
from src.config import Settings
from src.workday.exceptions import WorkdayAPIError

class WorkdayClient:
    """Minimal authenticated Workday client using per-user bearer tokens."""
    def __init__(self, settings: Settings, oauth_manager: OAuthManager) -> None:
        self.settings = settings
        self.oauth_manager = oauth_manager

    async def _get(self, user_id: str, path: str, params: dict | None = None) -> dict:
        """Perform an authenticated GET against Workday."""
        return await self._request("GET", user_id, path, params=params)

    async def _post(self, user_id: str, path: str, payload: dict | None = None) -> dict:
        """Perform an authenticated POST against Workday."""
        return await self._request("POST", user_id, path, json=payload)

    async def _request(self, method: str, user_id: str, path: str, **kwargs) -> dict:
        token = await self.oauth_manager.get_valid_access_token(user_id)
        url = urljoin(self.settings.workday_base_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
                response = await client.request(method, url, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise WorkdayAPIError("Workday request timed out.") from exc
        except httpx.HTTPError as exc:
            raise WorkdayAPIError("Workday request failed.") from exc
        if response.status_code < 200 or response.status_code >= 300:
            raise WorkdayAPIError("Workday returned a non-success response.", status_code=response.status_code)
        if not response.content:
            return {}
        return response.json()

    # TODO: Add concrete Workday REST/SOAP business endpoint methods in Phase 2.
