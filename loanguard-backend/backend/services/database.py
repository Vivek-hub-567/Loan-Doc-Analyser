"""
backend/services/database.py — Supabase database client stub.

Connect later by filling SUPABASE_URL and SUPABASE_KEY in .env
and replacing stub methods with actual supabase-py calls.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# In-memory store for batch job results (used until Supabase is connected)
_batch_store: dict[str, Any] = {}
_history_store: dict[str, Any] = {}


class DatabaseService:
    """Stub database service. Replace methods with Supabase calls when ready."""

    def __init__(self) -> None:
        self._connected = False
        logger.info("DatabaseService initialized (stub mode — Supabase not connected).")

    # ------------------------------------------------------------------
    async def save_analysis(self, doc_id: str, result: dict) -> None:
        """Persist analysis result."""
        _history_store[doc_id] = result
        logger.debug("Saved analysis result for doc_id=%s (in-memory)", doc_id)

    async def get_analysis(self, doc_id: str) -> dict | None:
        """Retrieve analysis result by doc_id."""
        return _history_store.get(doc_id)

    async def delete_analysis(self, doc_id: str) -> bool:
        """Delete analysis result. Returns True if deleted."""
        if doc_id in _history_store:
            del _history_store[doc_id]
            return True
        return False

    # ------------------------------------------------------------------
    async def save_batch(self, batch_id: str, data: dict) -> None:
        _batch_store[batch_id] = data

    async def get_batch(self, batch_id: str) -> dict | None:
        return _batch_store.get(batch_id)

    async def update_batch_result(self, batch_id: str, result: dict) -> None:
        if batch_id in _batch_store:
            _batch_store[batch_id].update(result)


# Singleton
_db_service: DatabaseService | None = None


def get_database() -> DatabaseService:
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
