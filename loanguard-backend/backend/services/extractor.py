"""
backend/services/extractor.py — Keyword extraction service wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_keyword_extraction(text: str, extractor: Any) -> dict[str, Any]:
    """
    Wrap the KeywordExtractor.extract() call.

    Args:
        text      : preprocessed document text
        extractor : KeywordExtractor instance (loaded at startup)

    Returns:
        dict with matches, category_breakdown, risk_score, risk_level, top_flags
    """
    try:
        return extractor.extract(text)
    except Exception as e:
        logger.error("Keyword extraction failed: %s", e)
        return {
            "matches": [],
            "category_breakdown": [],
            "risk_score": 0.0,
            "risk_level": "LOW",
            "top_flags": [],
        }
