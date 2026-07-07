"""Logging setup helpers."""
import logging
import sys

SENSITIVE_FIELDS = {"access_token", "refresh_token", "client_secret", "code", "code_verifier", "password"}


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        stream=sys.stdout,
    )
