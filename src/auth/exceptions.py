"""Authentication exception types."""

class AuthenticationRequired(Exception):
    """Raised when a user must complete Workday authentication."""

class InvalidOAuthState(Exception):
    """Raised when an OAuth state value is missing, expired, or invalid."""

class TokenExpired(Exception):
    """Raised when an access token is expired and cannot be refreshed."""

class RefreshFailed(Exception):
    """Raised when refresh-token exchange fails."""
