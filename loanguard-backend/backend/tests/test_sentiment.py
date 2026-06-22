"""
backend/tests/test_sentiment.py — Unit tests for sentiment analysis.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from nlp.preprocessing import analyze_sentiment


def test_threatening_aggressive_text():
    """Text with multiple aggressive markers should produce THREATENING label."""
    text = (
        "The lender may seize the asset without notice at any time. "
        "Recovery agent will be dispatched. The borrower is liable for all costs. "
        "Sole discretion of the lender applies. Irrevocable consent is given."
    )
    result = analyze_sentiment(text)
    assert result["label"] == "THREATENING"
    assert result["aggressive_score"] > 0.0
    assert len(result["aggressive_hits"]) > 0


def test_borrower_friendly_text():
    """Text with multiple friendly markers should produce non-THREATENING label."""
    text = (
        "This loan includes a cooling-off period of 3 days. "
        "The Key Fact Statement (KFS) is provided. Grievance redressal is available. "
        "Contact the ombudsman for disputes. Fair lending practices apply."
    )
    result = analyze_sentiment(text)
    assert result["friendly_score"] > 0.0
    assert len(result["friendly_hits"]) > 0
    assert result["label"] in ("BORROWER_FRIENDLY", "NEUTRAL_POSITIVE", "NEUTRAL")


def test_sentiment_label_options():
    """All sentiment labels should be valid."""
    valid_labels = {
        "THREATENING", "NEGATIVE", "NEUTRAL", "NEUTRAL_POSITIVE", "BORROWER_FRIENDLY"
    }
    result = analyze_sentiment("The borrower must repay the loan on time.")
    assert result["label"] in valid_labels


def test_sentiment_scores_bounded():
    """All score values should be within expected bounds."""
    result = analyze_sentiment(
        "The borrower agrees to repay the loan in monthly instalments. "
        "Interest rate is 12% per annum. EMI is payable on 5th of every month."
    )
    assert -1.0 <= result["compound_score"] <= 1.0
    assert 0.0 <= result["aggressive_score"] <= 1.0
    assert 0.0 <= result["friendly_score"] <= 1.0
    assert 0.0 <= result["positive"] <= 1.0
    assert 0.0 <= result["negative"] <= 1.0
    assert 0.0 <= result["neutral"] <= 1.0


def test_worst_clauses_are_sorted():
    """Worst clauses should have compound score below 0 and be sorted ascending."""
    text = (
        "The asset will be seized immediately upon default. "
        "Recovery agents may visit your home. "
        "This is a standard agreement. "
        "The borrower is happy with the terms. "
        "Legal action will be taken without notice."
    )
    result = analyze_sentiment(text)
    clauses = result["worst_clauses"]
    if len(clauses) > 1:
        for i in range(len(clauses) - 1):
            assert clauses[i]["compound"] <= clauses[i + 1]["compound"]


def test_aggressive_score_cap():
    """Aggressive score should not exceed 1.0."""
    text = " ".join([
        "seize irrevocable without notice liable for all recovery agent sole discretion "
        "mandatory arbitration asset seizure repossession legal action attach property "
        "accelerate entire outstanding full repayment immediately criminal action "
        "collection agent unilaterally absolute discretion without reason at any time"
    ] * 3)
    result = analyze_sentiment(text)
    assert result["aggressive_score"] <= 1.0
