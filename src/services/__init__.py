"""Application service container for dependency injection."""
from src.audit.audit_logger import InMemoryAuditLogger
from src.auth.oauth_manager import OAuthManager
from src.auth.token_store import MemoryTokenStore
from src.config import get_settings

settings = get_settings()
token_store = MemoryTokenStore()
audit_logger = InMemoryAuditLogger()
oauth_manager = OAuthManager(settings=settings, token_store=token_store, audit_logger=audit_logger)
