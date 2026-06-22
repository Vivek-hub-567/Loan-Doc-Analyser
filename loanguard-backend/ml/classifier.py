"""
ml/classifier.py — Multi-label risk classifier for LoanGuard AI.

Architecture:
  - TF-IDF vectorizer (15,000 features, ngram 1-3, sublinear_tf)
  - OneVsRest Logistic Regression (C=1.5, balanced class weights)

Provides:
  - load_model(path)         : loads persisted pipeline + mlb from pickle
  - predict_sentence(text)   : {category: confidence} for a single text
  - predict_document(text)   : sliding window predictions over full document
"""

from __future__ import annotations

import pickle
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CATEGORY_LABELS = {
    "hidden_fee_risk": "Hidden Fee Risk",
    "default_recovery_risk": "Default Recovery Risk",
    "legal_clause_detection": "Legal Clause Detection",
    "financial_entity_extraction": "Financial Entity",
    "power_imbalance_risk": "Power Imbalance Risk",
    "privacy_data_risk": "Privacy & Data Risk",
    "regulatory_compliance": "Regulatory Compliance",
    "predatory_lending_signals": "Predatory Lending Signal",
}


def load_model(model_path: str | Path) -> tuple[Any, Any] | tuple[None, None]:
    """
    Load the pickled sklearn pipeline and MultiLabelBinarizer.
    Returns (pipeline, mlb) or (None, None) on failure.
    """
    path = Path(model_path)
    if not path.exists():
        logger.warning(f"Model file not found at {path}. Classifier disabled.")
        return None, None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        pipeline = data["pipeline"]
        mlb = data["mlb"]
        logger.info(f"Classifier model loaded from {path}")
        return pipeline, mlb
    except Exception as e:
        logger.error(f"Failed to load classifier model: {e}")
        return None, None


def predict_sentence(
    text: str,
    pipeline: Any,
    mlb: Any,
    threshold: float = 0.3,
) -> dict[str, float]:
    """
    Predict risk categories for a single sentence/chunk.

    Returns:
        {category_id: confidence_score} — only categories above threshold.
    """
    if pipeline is None or mlb is None:
        return {}
    try:
        proba = pipeline.predict_proba([text])
        classes = mlb.classes_
        result = {}
        for i, cls in enumerate(classes):
            score = float(proba[0][i]) if hasattr(proba[0], "__len__") else 0.0
            if score >= threshold:
                result[cls] = round(score, 4)
        return dict(sorted(result.items(), key=lambda x: -x[1]))
    except Exception as e:
        logger.error(f"predict_sentence failed: {e}")
        return {}


def predict_document(
    text: str,
    pipeline: Any,
    mlb: Any,
    window: int = 3,
    threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Sliding window predictions over the document.

    Args:
        text    : full document text
        pipeline: fitted sklearn pipeline
        mlb     : MultiLabelBinarizer
        window  : number of sentences per chunk
        threshold: confidence threshold

    Returns:
        list of {chunk, predictions, top_label}
    """
    if pipeline is None or mlb is None:
        return []

    # Split into sentences
    sentences = _split_sentences(text)
    if not sentences:
        return []

    results = []
    for i in range(0, len(sentences), max(window // 2, 1)):
        chunk_sents = sentences[i : i + window]
        chunk_text = " ".join(chunk_sents)
        if not chunk_text.strip():
            continue

        preds = predict_sentence(chunk_text, pipeline, mlb, threshold)
        if not preds:
            continue

        top_cat = max(preds, key=preds.get)  # type: ignore[arg-type]
        top_label = _CATEGORY_LABELS.get(top_cat, top_cat)

        results.append(
            {
                "chunk": chunk_text[:200],
                "predictions": preds,
                "top_label": top_label,
            }
        )

    return results


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitter (fallback-safe)."""
    try:
        from nltk.tokenize import sent_tokenize

        return sent_tokenize(text)
    except Exception:
        import re

        return re.split(r"(?<=[.!?])\s+", text.strip())
