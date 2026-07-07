"""Application service container for dependency injection."""
from src.audit.audit_logger import InMemoryAuditLogger
from src.auth.oauth_manager import OAuthManager
from src.auth.state_store import MemoryOAuthStateStore
from src.auth.token_store import MemoryTokenStore
from src.config import get_settings
from src.identity.context import ContextResolver
from src.identity.provider import DevIdentityProvider, FutureIdentityProvider

settings = get_settings()
token_store = MemoryTokenStore()
oauth_state_store = MemoryOAuthStateStore()
audit_logger = InMemoryAuditLogger()
identity_provider = DevIdentityProvider(settings) if settings.app_env == "local" else FutureIdentityProvider()
context_resolver = ContextResolver(identity_provider)
oauth_manager = OAuthManager(settings=settings, token_store=token_store, state_store=oauth_state_store, audit_logger=audit_logger)
