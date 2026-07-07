from datetime import datetime, timedelta, timezone
import asyncio
from src.auth.models import OAuthState
from src.auth.state_store import MemoryOAuthStateStore


def test_oauth_state_is_bound_to_user_identity():
    async def scenario():
        store = MemoryOAuthStateStore()
        state = OAuthState(state="state-1", user_id="resolved-user", code_verifier="verifier", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))
        await store.save(state)
        popped = await store.pop("state-1")
        assert popped is not None
        assert popped.user_id == "resolved-user"
        assert popped.code_verifier == "verifier"
    asyncio.run(scenario())


def test_expired_oauth_state_is_not_returned():
    async def scenario():
        store = MemoryOAuthStateStore()
        state = OAuthState(state="state-2", user_id="resolved-user", code_verifier="verifier", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
        await store.save(state)
        assert await store.pop("state-2") is None
    asyncio.run(scenario())
