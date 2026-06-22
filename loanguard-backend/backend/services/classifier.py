"""
backend/services/classifier.py — Classifier service wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

import ml.classifier as clf_module

logger = logging.getLogger(__name__)


def run_classifier_document(
    text: str,
    pipeline: Any,
    mlb: Any,
    window: int = 3,
) -> list[dict[str, Any]]:
    """
    Run sliding-window multi-label classification over document.

    Args:
        text    : full document text
        pipeline: loaded sklearn pipeline
        mlb     : MultiLabelBinarizer
        window  : sentences per chunk

    Returns:
        list of {chunk, predictions, top_label}
    """
    try:
        return clf_module.predict_document(text, pipeline, mlb, window=window)
    except Exception as e:
        logger.error("Classifier document prediction failed: %s", e)
        return []


def run_classifier_sentence(
    text: str,
    pipeline: Any,
    mlb: Any,
) -> dict[str, float]:
    """Run single-sentence classification."""
    try:
        return clf_module.predict_sentence(text, pipeline, mlb)
    except Exception as e:
        logger.error("Classifier sentence prediction failed: %s", e)
        return {}
