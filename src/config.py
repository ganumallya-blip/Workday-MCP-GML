"""Application configuration loaded exclusively from environment variables."""
from functools import lru_cache
import os
try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - supports minimal CI/test containers
    def Field(default=None, alias=None):
        return default
    class BaseSettings:
        def __init__(self, **kwargs):
            aliases = getattr(self, "_ALIASES", {})
            for name, alias in aliases.items():
                default = getattr(self.__class__, name)
                raw = kwargs.get(name, os.getenv(alias, default))
                if isinstance(default, bool):
                    raw = str(raw).lower() in {"1", "true", "yes", "on"}
                elif isinstance(default, int):
                    raw = int(raw)
                elif isinstance(default, float):
                    raw = float(raw)
                setattr(self, name, raw)
    def SettingsConfigDict(**kwargs):
        return kwargs

class Settings(BaseSettings):
    """Runtime settings. Values come from environment variables or .env locally."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    _ALIASES = {
        "app_env": "APP_ENV", "log_level": "LOG_LEVEL", "request_timeout": "REQUEST_TIMEOUT",
        "dev_auth_enabled": "DEV_AUTH_ENABLED", "dev_user_id": "DEV_USER_ID", "dev_user_email": "DEV_USER_EMAIL", "dev_user_display_name": "DEV_USER_DISPLAY_NAME",
        "workday_tenant_name": "WORKDAY_TENANT_NAME", "workday_base_url": "WORKDAY_BASE_URL", "workday_authorize_url": "WORKDAY_AUTHORIZE_URL", "workday_token_url": "WORKDAY_TOKEN_URL", "workday_client_id": "WORKDAY_CLIENT_ID", "workday_client_secret": "WORKDAY_CLIENT_SECRET", "workday_redirect_uri": "WORKDAY_REDIRECT_URI", "workday_scope": "WORKDAY_SCOPE",
        "token_encryption_key": "TOKEN_ENCRYPTION_KEY", "admin_auth_enabled": "ADMIN_AUTH_ENABLED", "admin_username": "ADMIN_USERNAME", "admin_password": "ADMIN_PASSWORD", "admin_password_hash": "ADMIN_PASSWORD_HASH", "admin_session_secret": "ADMIN_SESSION_SECRET", "admin_session_ttl_minutes": "ADMIN_SESSION_TTL_MINUTES",
    }

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    request_timeout: float = Field(default=30.0, alias="REQUEST_TIMEOUT")
    dev_auth_enabled: bool = Field(default=True, alias="DEV_AUTH_ENABLED")
    dev_user_id: str = Field(default="local-dev-user", alias="DEV_USER_ID")
    dev_user_email: str = Field(default="local-dev-user@example.com", alias="DEV_USER_EMAIL")
    dev_user_display_name: str = Field(default="Local Dev User", alias="DEV_USER_DISPLAY_NAME")

    workday_tenant_name: str = Field(default="", alias="WORKDAY_TENANT_NAME")
    workday_base_url: str = Field(default="", alias="WORKDAY_BASE_URL")
    workday_authorize_url: str = Field(default="", alias="WORKDAY_AUTHORIZE_URL")
    workday_token_url: str = Field(default="", alias="WORKDAY_TOKEN_URL")
    workday_client_id: str = Field(default="", alias="WORKDAY_CLIENT_ID")
    workday_client_secret: str = Field(default="", alias="WORKDAY_CLIENT_SECRET")
    workday_redirect_uri: str = Field(default="", alias="WORKDAY_REDIRECT_URI")
    workday_scope: str = Field(default="", alias="WORKDAY_SCOPE")

    token_encryption_key: str = Field(default="", alias="TOKEN_ENCRYPTION_KEY")

    admin_auth_enabled: bool = Field(default=True, alias="ADMIN_AUTH_ENABLED")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")
    admin_password_hash: str = Field(default="", alias="ADMIN_PASSWORD_HASH")
    admin_session_secret: str = Field(default="", alias="ADMIN_SESSION_SECRET")
    admin_session_ttl_minutes: int = Field(default=60, alias="ADMIN_SESSION_TTL_MINUTES")

    def config_status(self) -> dict[str, bool]:
        """Return non-secret configuration presence flags only."""
        return {
            "tenant_name_present": bool(self.workday_tenant_name),
            "authorize_url_configured": bool(self.workday_authorize_url),
            "token_url_configured": bool(self.workday_token_url),
            "redirect_uri_configured": bool(self.workday_redirect_uri),
            "client_id_configured": bool(self.workday_client_id),
            "client_secret_configured": bool(self.workday_client_secret),
            "scope_configured": bool(self.workday_scope),
            "base_url_configured": bool(self.workday_base_url),
            "token_encryption_key_configured": bool(self.token_encryption_key),
            "admin_session_secret_configured": bool(self.admin_session_secret),
            "dev_auth_enabled": bool(self.dev_auth_enabled),
        }

@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
