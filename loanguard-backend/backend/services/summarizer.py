"""
backend/services/summarizer.py — Extractive summarization service wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

from nlp.preprocessing import summarize

logger = logging.getLogger(__name__)


def run_summarization(text: str, top_n: int = 3) -> dict[str, Any]:
    """
    Wrap summarize() with error handling.

    Args:
        text  : full document text
        top_n : number of key sentences to extract

    Returns:
        dict with text, key_sentences, sentence_count, compression_ratio, method
    """
    try:
        return summarize(text, top_n=top_n)
    except Exception as e:
        logger.error("Summarization failed: %s", e)
        return {
            "text": "",
            "key_sentences": [],
            "sentence_count": 0,
            "compression_ratio": 0.0,
            "method": "tfidf",
        }
