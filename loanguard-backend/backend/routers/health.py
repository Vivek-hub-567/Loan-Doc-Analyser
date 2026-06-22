"""
backend/routers/health.py — GET /api/v1/health
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request

from backend.schemas.response import HealthResponse
from backend.config import get_settings

router = APIRouter()
settings = get_settings()

_START_TIME = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns service health status including model and dependency availability.",
)
async def health_check(request: Request) -> HealthResponse:
    state = request.app.state

    model_loaded = (
        getattr(state, "pipeline", None) is not None
        and getattr(state, "mlb", None) is not None
    )

    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader_available = True
    except ImportError:
        vader_available = False

    try:
        import nltk
        nltk.data.find("tokenizers/punkt")
        nltk_data_ready = True
    except LookupError:
        nltk_data_ready = False
    except ImportError:
        nltk_data_ready = False

    uptime = round(time.monotonic() - _START_TIME, 2)

    status = "healthy"
    if not model_loaded or not vader_available:
        status = "degraded"

    return HealthResponse(
        status=status,  # type: ignore[arg-type]
        model_loaded=model_loaded,
        vader_available=vader_available,
        nltk_data_ready=nltk_data_ready,
        uptime_seconds=uptime,
        version=settings.app_version,
    )
