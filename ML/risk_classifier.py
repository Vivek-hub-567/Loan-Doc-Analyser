"""
Loan document risk classifier — production wrapper.

Loads whichever model won the train_compare.py model bake-off
(random_forest, xgboost, logistic_regression, etc.) and exposes a
single predict() interface used by the rest of the app (RAG explainer,
API layer), regardless of which underlying algorithm was selected.
"""

import os
import sys
import json
import joblib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nlp.feature_extractor import FeatureExtractor
from nlp.keywords import KEYWORD_CATEGORIES

MODEL_DIR = os.path.dirname(__file__)
BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model.joblib")
BEST_MODEL_NAME_PATH = os.path.join(MODEL_DIR, "best_model_name.txt")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
COMPARISON_PATH = os.path.join(MODEL_DIR, "model_comparison.json")

SCALED_MODELS = {"logistic_regression", "linear_svm", "naive_bayes"}

RISK_LABELS = ["low_risk", "medium_risk", "high_risk", "predatory"]
RISK_DISPLAY = {
    "low_risk": "Low Risk", "medium_risk": "Medium Risk",
    "high_risk": "High Risk", "predatory": "Predatory",
}


class LoanRiskClassifier:
    """Production classifier: NLP feature extraction + best-performing ML model."""

    def __init__(self):
        self.model = None
        self.model_name = None
        self.scaler = None
        self.extractor = FeatureExtractor()
        self.is_trained = False
        self.comparison_report = {}

    def load(self):
        """Load the best model + fitted TF-IDF vectorizer + scaler from disk."""
        self.model = joblib.load(BEST_MODEL_PATH)
        with open(BEST_MODEL_NAME_PATH) as f:
            self.model_name = f.read().strip()
        self.extractor.load_tfidf()
        if os.path.exists(SCALER_PATH):
            self.scaler = joblib.load(SCALER_PATH)
        if os.path.exists(COMPARISON_PATH):
            with open(COMPARISON_PATH) as f:
                self.comparison_report = json.load(f)
        self.is_trained = True
        return self

    def predict(self, text: str) -> dict:
        if not self.is_trained:
            raise RuntimeError("Model not loaded. Call load() first (after running train_compare.py).")

        features = self.extractor.extract(text)
        X = features["feature_vector"].reshape(1, -1)

        if self.model_name in SCALED_MODELS and self.scaler is not None:
            X = self.scaler.transform(X)

        label_idx = int(self.model.predict(X)[0])
        proba = self.model.predict_proba(X)[0] if hasattr(self.model, "predict_proba") else None

        if proba is not None:
            confidence = float(proba[label_idx])
            risk_score = round(min(100.0, sum(i * p * 33.3 for i, p in enumerate(proba))), 1)
            class_probs = {RISK_LABELS[i]: round(float(p), 4) for i, p in enumerate(proba)}
        else:
            confidence = 1.0
            risk_score = float(label_idx) * 33.3
            class_probs = {RISK_LABELS[i]: (1.0 if i == label_idx else 0.0) for i in range(4)}

        label = RISK_LABELS[label_idx]

        category_breakdown = []
        for cat_id, cat_data in KEYWORD_CATEGORIES.items():
            count = features["cat_counts"].get(cat_id, 0)
            category_breakdown.append({
                "category_id": cat_id,
                "label": cat_data["label"],
                "keyword_hits": count,
                "weighted_score": round(features["cat_scores"].get(cat_id, 0), 2),
                "matched_keywords": features["hits"].get(cat_id, []),
                "risk_weight": cat_data["risk_weight"],
                "risk_level": cat_data["risk_level"],
            })
        category_breakdown.sort(key=lambda x: x["weighted_score"], reverse=True)

        top_flags = [kw for cat in category_breakdown[:4] for kw in cat["matched_keywords"]][:10]

        return {
            "risk_label": label,
            "risk_display": RISK_DISPLAY[label],
            "risk_score": risk_score,
            "confidence": round(confidence, 4),
            "confidence_pct": f"{confidence:.0%}",
            "class_probabilities": class_probs,
            "total_keywords_found": features["total_keywords"],
            "keyword_density": round(features["keyword_density"], 3),
            "category_breakdown": category_breakdown,
            "top_flags": top_flags,
            "word_count": features["word_count"],
            "model_used": self.model_name,
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        return [self.predict(t) for t in texts]

    def status(self) -> dict:
        return {
            "is_trained": self.is_trained,
            "model_used": self.model_name,
            "validation_comparison": self.comparison_report.get("all_models_val_comparison", {}),
            "test_metrics": self.comparison_report.get("best_model_test_metrics", {}),
        }
