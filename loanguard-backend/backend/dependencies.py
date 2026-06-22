"""
backend/dependencies.py — Shared FastAPI dependency injection providers.

All ML/NLP resources are loaded once at startup (via lifespan) and
stored in app.state. These DI functions retrieve them per-request
without reloading.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request


def get_extractor(request: Request) -> Any:
    """Return the shared KeywordExtractor instance."""
    return request.app.state.extractor


def get_model(request: Request) -> tuple[Any, Any]:
    """Return (pipeline, mlb) tuple from app state."""
    return request.app.state.pipeline, request.app.state.mlb


def get_rag_explainer(request: Request) -> Any | None:
    """Return the RAGExplainer instance (may be None if knowledge base is empty)."""
    return getattr(request.app.state, "rag_explainer", None)


def get_database_service(request: Request) -> Any:
    """Return the DatabaseService instance."""
    return request.app.state.db
