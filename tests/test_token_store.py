from datetime import datetime, timedelta, timezone
import asyncio
from src.auth.models import TokenSession
from src.auth.token_store import MemoryTokenStore


def test_memory_token_store_save_get_delete():
    async def scenario():
        store = MemoryTokenStore()
        session = TokenSession(user_id="u1", email="u1@example.com", access_token="access", refresh_token="refresh", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5), scopes=["openid"])
        await store.save(session)
        saved = await store.get("u1")
        assert saved is not None
        assert saved.user_id == "u1"
        assert saved.access_token == "access"
        assert saved.last_used_at is not None
        await store.delete("u1")
        assert await store.get("u1") is None
    asyncio.run(scenario())


def test_expired_token_metadata_behavior():
    async def scenario():
        store = MemoryTokenStore()
        session = TokenSession(user_id="u2", email="u2@example.com", access_token="access", refresh_token="refresh", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1), scopes=["openid"])
        await store.save(session)
        metadata = await store.metadata("u2")
        assert metadata.authenticated is False
        assert metadata.token_status == "expired"
        assert metadata.scopes == ["openid"]
    asyncio.run(scenario())


def test_token_metadata_exposes_only_safe_fields():
    async def scenario():
        store = MemoryTokenStore()
        session = TokenSession(user_id="u3", email="u3@example.com", access_token="secret-access", refresh_token="secret-refresh", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5), scopes=["openid"])
        await store.save(session)
        metadata = (await store.list_metadata())[0]
        data = metadata.model_dump() if hasattr(metadata, "model_dump") else metadata.__dict__
        assert data["email"] == "u3@example.com"
        assert "access_token" not in data
        assert "refresh_token" not in data
        assert "authorization_code" not in data
        assert "client_secret" not in data
    asyncio.run(scenario())


def test_revoke_session_removes_token_by_user_metadata():
    async def scenario():
        store = MemoryTokenStore()
        session = TokenSession(user_id="u4", email="u4@example.com", access_token="secret-access", refresh_token="secret-refresh", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5), scopes=["openid"])
        await store.save(session)
        metadata = (await store.list_metadata())[0]
        await store.delete(metadata.user_id)
        assert await store.get("u4") is None
    asyncio.run(scenario())
