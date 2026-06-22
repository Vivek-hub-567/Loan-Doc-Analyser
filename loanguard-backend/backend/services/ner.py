"""
backend/services/ner.py — Named Entity Recognition service wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

from nlp.preprocessing import extract_entities

logger = logging.getLogger(__name__)


def run_ner(text: str) -> dict[str, Any]:
    """
    Wrap extract_entities() with error handling.

    Returns entity dict including per-type lists and summary.
    """
    try:
        return extract_entities(text)
    except Exception as e:
        logger.error("NER extraction failed: %s", e)
        return {
            "MONEY": [], "RATE": [], "FEE_AMOUNT": [], "LOAN_AMOUNT": [],
            "DURATION": [], "DATE": [], "ORG": [], "CLAUSE_TYPE": [], "REGULATION": [],
            "summary": {
                "total_entities": 0,
                "money_mentions": 0,
                "rate_mentions": 0,
                "fee_mentions": 0,
                "clause_types": [],
                "regulations": [],
            },
        }
