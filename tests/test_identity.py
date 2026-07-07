from types import SimpleNamespace
import asyncio
import pytest
from src.auth.exceptions import AuthenticationRequired
from src.identity.provider import DevIdentityProvider

class Request:
    def __init__(self, headers):
        self.headers = headers


def test_dev_identity_provider_uses_header_in_local():
    settings = SimpleNamespace(app_env="local", dev_auth_enabled=True, dev_user_id="fallback", dev_user_email="dev@example.com", dev_user_display_name="Dev User")
    user = asyncio.run(DevIdentityProvider(settings).get_current_user(Request({"x-dev-user": "header-user"})))
    assert user.user_id == "header-user"
    assert user.auth_source == "dev"


def test_dev_identity_provider_uses_env_default_in_local():
    settings = SimpleNamespace(app_env="local", dev_auth_enabled=True, dev_user_id="env-user", dev_user_email="dev@example.com", dev_user_display_name="Dev User")
    user = asyncio.run(DevIdentityProvider(settings).get_current_user(None))
    assert user.user_id == "env-user"


def test_x_dev_user_rejected_when_not_local():
    settings = SimpleNamespace(app_env="prod", dev_auth_enabled=True, dev_user_id="env-user", dev_user_email="dev@example.com", dev_user_display_name="Dev User")
    with pytest.raises(AuthenticationRequired):
        asyncio.run(DevIdentityProvider(settings).get_current_user(Request({"x-dev-user": "bad"})))
