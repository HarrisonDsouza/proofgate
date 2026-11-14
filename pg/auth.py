"""Shared auth helpers (kept out of main.py so routers such as pg/voice.py can use them without a circular import)."""
from __future__ import annotations

import secrets

from fastapi import Header, HTTPException

from pg.config import settings


def same(given: str | None, expected: str) -> bool:
    """Constant-time comparison; an unset expected key never matches."""
    return bool(expected) and secrets.compare_digest((given or "").encode(), expected.encode())


def console_only(x_console_key: str | None = Header(None)):
    """Operator console key for sessions and the control plane. Without it: 401, nothing is read or written."""
    if not same(x_console_key, settings.console_key):
        raise HTTPException(401, "console key required")
