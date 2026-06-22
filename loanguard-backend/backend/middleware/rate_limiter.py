"""
backend/middleware/rate_limiter.py — slowapi rate limiter setup.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit],
    storage_uri="memory://",
)
