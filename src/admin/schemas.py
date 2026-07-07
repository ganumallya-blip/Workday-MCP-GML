"""Admin API request/response schemas and exceptions."""
from pydantic import BaseModel

class AdminAuthenticationFailed(Exception):
    """Raised when admin credentials or session token are invalid."""

class AdminAuthorizationFailed(Exception):
    """Raised when an authenticated admin is not authorized."""

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int

class AdminHealthResponse(BaseModel):
    status: str
    admin_auth_enabled: bool
