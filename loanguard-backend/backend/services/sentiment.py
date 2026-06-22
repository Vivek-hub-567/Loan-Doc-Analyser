"""
backend/services/sentiment.py — Sentiment analysis service wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

from nlp.preprocessing import analyze_sentiment

logger = logging.getLogger(__name__)


def run_sentiment_analysis(text: str) -> dict[str, Any]:
    """
    Wrap analyze_sentiment() with error handling.

    Returns VADER + aggressive/friendly scoring dict.
    """
    try:
        return analyze_sentiment(text)
    except Exception as e:
        logger.error("Sentiment analysis failed: %s", e)
        return {
            "label": "NEUTRAL",
            "compound_score": 0.0,
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0,
            "aggressive_score": 0.0,
            "aggressive_hits": [],
            "friendly_score": 0.0,
            "friendly_hits": [],
            "worst_clauses": [],
        }
