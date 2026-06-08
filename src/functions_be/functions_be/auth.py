"""Local-token auth (be_011, per d_be_013 → loopback + generated token).

A token is generated once and stored chmod 600; the GUI (same machine) reads it and
sends it as a bearer token. Loopback-only binding is the transport boundary.
"""

from __future__ import annotations

import hmac
import os
import secrets
from pathlib import Path


def token_file() -> Path:
    override = os.environ.get("FUNCTIONS_TOKEN_FILE")
    return Path(override) if override else Path.home() / ".functions" / "token"


def ensure_token(path: str | Path | None = None) -> str:
    p = Path(path) if path else token_file()
    if p.exists():
        return p.read_text().strip()
    p.parent.mkdir(parents=True, exist_ok=True)
    tok = secrets.token_urlsafe(32)
    p.write_text(tok)
    p.chmod(0o600)
    return tok


def verify(provided: str | None, token: str) -> bool:
    return bool(provided) and hmac.compare_digest(provided, token)
