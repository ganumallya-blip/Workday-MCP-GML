"""PKCE helper functions for OAuth2 Authorization Code flow."""
import base64
import hashlib
import secrets


def generate_code_verifier() -> str:
    """Generate a high-entropy PKCE code verifier."""
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(code_verifier: str) -> str:
    """Generate an S256 PKCE code challenge for the supplied verifier."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
