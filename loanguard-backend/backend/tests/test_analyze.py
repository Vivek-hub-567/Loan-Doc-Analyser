"""
backend/tests/test_analyze.py — Integration tests for the /analyze endpoint.
"""

from __future__ import annotations

import pytest


def test_analyze_text_success(test_client, sample_text):
    """Full analysis of a valid loan agreement should return 200 with expected fields."""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": sample_text},
    )
    assert response.status_code == 200
    data = response.json()

    # Core fields
    assert "doc_id" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= data["risk_score"] <= 100.0
    assert isinstance(data["should_sign"], bool)
    assert data["word_count"] > 50

    # Sentiment
    assert data["sentiment"] is not None
    assert data["sentiment"]["label"] in (
        "THREATENING", "NEGATIVE", "NEUTRAL", "NEUTRAL_POSITIVE", "BORROWER_FRIENDLY"
    )

    # Entities
    assert data["entities"] is not None
    assert "summary" in data["entities"]

    # Category breakdown
    assert isinstance(data["category_breakdown"], list)

    # Summary
    assert data["summary"] is not None
    assert data["summary"]["method"] in ("textrank", "tfidf")

    # TF-IDF terms
    assert data["tfidf_terms"] is not None
    assert len(data["tfidf_terms"]) > 0

    # X-Request-ID header
    assert "x-request-id" in response.headers


def test_analyze_short_text_returns_400(test_client):
    """Text with fewer than 50 words should return 400."""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": "This is too short."},
    )
    assert response.status_code == 400
    detail = response.json().get("detail", {})
    assert detail.get("status") == 400
    assert "50 words" in detail.get("detail", "")


def test_analyze_empty_text_returns_400(test_client):
    """Empty text should return 400."""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": "   "},
    )
    assert response.status_code in (400, 422)


def test_analyze_high_risk_predatory_loan(test_client, sample_text):
    """Predatory loan agreement should score HIGH or CRITICAL and should_sign=False."""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": sample_text},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    assert data["should_sign"] is False


def test_analyze_with_options_no_sentiment(test_client, sample_text):
    """Disabling sentiment should return null sentiment field."""
    response = test_client.post(
        "/api/v1/analyze",
        json={
            "text": sample_text,
            "options": {"run_sentiment": False},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment"] is None


def test_analyze_top_flags_present(test_client, sample_text):
    """Top flags should be a non-empty list for predatory loan text."""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": sample_text},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["top_flags"]) > 0


def test_health_endpoint(test_client):
    """Health endpoint should return 200 with status field."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "uptime_seconds" in data
    assert "version" in data


def test_categories_endpoint(test_client):
    """Categories endpoint should return 8 risk categories."""
    response = test_client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) == 9
    assert data["total_keywords"] > 0
    for cat in data["categories"]:
        assert "id" in cat
        assert "severity" in cat
        assert "keywords" in cat


def test_history_not_found(test_client):
    """Unknown doc_id should return 404."""
    response = test_client.get("/api/v1/history/nonexistent-id-12345")
    assert response.status_code == 404


def test_analyze_and_retrieve_history(test_client, sample_text):
    """After analysis, result should be retrievable by doc_id."""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": sample_text},
    )
    assert response.status_code == 200
    doc_id = response.json()["doc_id"]

    history_response = test_client.get(f"/api/v1/history/{doc_id}")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["doc_id"] == doc_id
    assert history_data["status"] == "completed"
