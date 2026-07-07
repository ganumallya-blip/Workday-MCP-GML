"""Replaceable token store abstraction and in-memory implementation."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import copy
from .models import TokenMetadata, TokenSession

class TokenStore(ABC):
    @abstractmethod
    async def save(self, session: TokenSession) -> None: ...
    @abstractmethod
    async def get(self, user_id: str) -> TokenSession | None: ...
    @abstractmethod
    async def delete(self, user_id: str) -> None: ...
    @abstractmethod
    async def list_metadata(self) -> list[TokenMetadata]: ...
    @abstractmethod
    async def metadata(self, user_id: str) -> TokenMetadata: ...

class MemoryTokenStore(TokenStore):
    """Process-local token store for Phase 1 development and tests."""
    def __init__(self) -> None:
        self._sessions: dict[str, TokenSession] = {}

    async def save(self, session: TokenSession) -> None:
        now = datetime.now(timezone.utc)
        if session.user_id in self._sessions:
            session.created_at = self._sessions[session.user_id].created_at
        session.updated_at = now
        self._sessions[session.user_id] = copy.deepcopy(session)

    async def get(self, user_id: str) -> TokenSession | None:
        session = self._sessions.get(user_id)
        if not session:
            return None
        session = copy.deepcopy(session)
        session.last_used_at = datetime.now(timezone.utc)
        self._sessions[user_id].last_used_at = session.last_used_at
        return session

    async def delete(self, user_id: str) -> None:
        self._sessions.pop(user_id, None)

    async def list_metadata(self) -> list[TokenMetadata]:
        return [self._to_metadata(s) for s in self._sessions.values()]

    async def metadata(self, user_id: str) -> TokenMetadata:
        session = self._sessions.get(user_id)
        if session is None:
            return TokenMetadata(user_id=user_id, authenticated=False, token_status="missing")
        return self._to_metadata(session)

    def _to_metadata(self, session: TokenSession) -> TokenMetadata:
        status = "expired" if session.is_expired else "valid"
        return TokenMetadata(
            user_id=session.user_id,
            authenticated=not session.is_expired,
            expires_at=session.expires_at,
            scopes=session.scopes,
            token_status=status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_used_at=session.last_used_at,
        )
