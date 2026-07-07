"""OAuth state store abstraction for PKCE authorization attempts."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import copy
from src.auth.models import OAuthState

class OAuthStateStore(ABC):
    @abstractmethod
    async def save(self, state: OAuthState) -> None: ...
    @abstractmethod
    async def pop(self, state: str) -> OAuthState | None: ...

class MemoryOAuthStateStore(OAuthStateStore):
    """In-memory expiring OAuth state store for Phase 1."""
    def __init__(self) -> None:
        self._states: dict[str, OAuthState] = {}

    async def save(self, state: OAuthState) -> None:
        self._states[state.state] = copy.deepcopy(state)

    async def pop(self, state: str) -> OAuthState | None:
        oauth_state = self._states.pop(state, None)
        if oauth_state is None:
            return None
        if oauth_state.expires_at <= datetime.now(timezone.utc):
            return None
        return oauth_state
