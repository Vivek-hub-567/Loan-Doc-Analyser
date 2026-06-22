"""
Multi-model training and comparison.

Splits data 70% train / 15% validation / 15% test.
Trains and compares:
  - Random Forest
  - Logistic Regression
  - XGBoost
  - Gradient Boosting
  - Linear SVM
  - Naive Bayes (baseline)

Selects the best model on validation accuracy, then reports
final unbiased performance on the held-out test set.
"""

import os
import sys
import json
import time
import numpy as np
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import GaussianNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from data.synthetic_data import generate_dataset, RISK_LABELS
from nlp.feature_extractor import FeatureExtractor

MODEL_DIR = os.path.join(os.path.dirname(__file__))
RESULTS_PATH = os.path.join(MODEL_DIR, "model_comparison.json")


def build_feature_matrix(texts: list[str], extractor: FeatureExtractor) -> np.ndarray:
    rows = [extractor.extract(t)["feature_vector"] for t in texts]
    return np.vstack(rows)


def get_candidate_models() -> dict:
    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_split=4,
            min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1,
        ),
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.1, random_state=42,
        ),
        "linear_svm": CalibratedClassifierCV(
            LinearSVC(class_weight="balanced", max_iter=5000, random_state=42),
            cv=3,
        ),
        "naive_bayes": GaussianNB(),
    }
    if XGB_AVAILABLE:
        models["xgboost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            objective="multi:softprob", num_class=4,
            eval_metric="mlogloss", random_state=42, n_jobs=-1,
        )
    return models


def evaluate(model, X, y, label_names) -> dict:
    y_pred = model.predict(X)
    return {
        "accuracy":  round(accuracy_score(y, y_pred), 4),
        "precision": round(precision_score(y, y_pred, average="macro", zero_division=0), 4),
        "recall":    round(recall_score(y, y_pred, average="macro", zero_division=0), 4),
        "f1":        round(f1_score(y, y_pred, average="macro", zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
        "report": classification_report(y, y_pred, target_names=label_names, output_dict=True),
    }


def main():
    print("=" * 70)
    print("  Loan Risk Classifier — Multi-Model Training & Comparison")
    print("=" * 70)

    # ── 1. Generate data ────────────────────────────────────────────
    print("\n[1/5] Generating synthetic dataset...")
    texts, labels = generate_dataset(n_per_class=250)
    print(f"      Total samples: {len(texts)}")

    # ── 2. Split 70/15/15 ───────────────────────────────────────────
    print("\n[2/5] Splitting data: 70% train / 15% validation / 15% test...")
    X_train_txt, X_temp_txt, y_train, y_temp = train_test_split(
        texts, labels, test_size=0.30, random_state=42, stratify=labels
    )
    X_val_txt, X_test_txt, y_val, y_test = train_test_split(
        X_temp_txt, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    print(f"      Train:      {len(X_train_txt)} ({len(X_train_txt)/len(texts):.0%})")
    print(f"      Validation: {len(X_val_txt)} ({len(X_val_txt)/len(texts):.0%})")
    print(f"      Test:       {len(X_test_txt)} ({len(X_test_txt)/len(texts):.0%})")

    # ── 3. Feature extraction (fit TF-IDF on TRAIN only) ────────────
    print("\n[3/5] Extracting NLP features (keyword + TF-IDF)...")
    extractor = FeatureExtractor()
    extractor.fit_tfidf(X_train_txt)   # fit only on train to avoid leakage
    extractor.save_tfidf()

    X_train = build_feature_matrix(X_train_txt, extractor)
    X_val   = build_feature_matrix(X_val_txt, extractor)
    X_test  = build_feature_matrix(X_test_txt, extractor)

    # Scale features for models sensitive to scale (LogReg, SVM, NB)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled   = scaler.transform(X_val)
    X_test_scaled  = scaler.transform(X_test)
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))

    print(f"      Feature vector size: {X_train.shape[1]} dims")

    # ── 4. Train + validate all candidate models ────────────────────
    print("\n[4/5] Training candidate models...")
    models = get_candidate_models()
    results = {}

    SCALED_MODELS = {"logistic_regression", "linear_svm", "naive_bayes"}

    for name, model in models.items():
        t0 = time.time()
        Xtr = X_train_scaled if name in SCALED_MODELS else X_train
        Xva = X_val_scaled if name in SCALED_MODELS else X_val
        Xte = X_test_scaled if name in SCALED_MODELS else X_test

        model.fit(Xtr, y_train)
        train_time = time.time() - t0

        val_metrics = evaluate(model, Xva, y_val, RISK_LABELS)
        results[name] = {
            "val_metrics": val_metrics,
            "train_time_sec": round(train_time, 2),
        }
        print(f"      {name:22s} val_accuracy={val_metrics['accuracy']:.4f}  "
              f"val_f1={val_metrics['f1']:.4f}  ({train_time:.1f}s)")

    # ── 5. Select best model by validation F1, report test performance ──
    best_name = max(results, key=lambda n: results[n]["val_metrics"]["f1"])
    best_model = models[best_name]
    Xte_final = X_test_scaled if best_name in SCALED_MODELS else X_test

    print(f"\n[5/5] Best model on validation: {best_name}")
    test_metrics = evaluate(best_model, Xte_final, y_test, RISK_LABELS)
    results[best_name]["test_metrics"] = test_metrics

    print("\n" + "=" * 70)
    print(f"  FINAL TEST SET RESULTS — {best_name}")
    print("=" * 70)
    print(f"  Accuracy:  {test_metrics['accuracy']:.2%}")
    print(f"  Precision: {test_metrics['precision']:.2%}")
    print(f"  Recall:    {test_metrics['recall']:.2%}")
    print(f"  F1-score:  {test_metrics['f1']:.2%}")
    print("\n  Per-class breakdown:")
    print(classification_report(y_test, best_model.predict(Xte_final), target_names=RISK_LABELS))

    # ── Save best model + comparison report ──────────────────────────
    joblib.dump(best_model, os.path.join(MODEL_DIR, "best_model.joblib"))
    with open(os.path.join(MODEL_DIR, "best_model_name.txt"), "w") as f:
        f.write(best_name)

    summary = {
        "best_model": best_name,
        "split": {"train": len(X_train_txt), "val": len(X_val_txt), "test": len(X_test_txt)},
        "scaled_models": list(SCALED_MODELS),
        "all_models_val_comparison": {
            name: {
                "accuracy": r["val_metrics"]["accuracy"],
                "precision": r["val_metrics"]["precision"],
                "recall": r["val_metrics"]["recall"],
                "f1": r["val_metrics"]["f1"],
                "train_time_sec": r["train_time_sec"],
            }
            for name, r in results.items()
        },
        "best_model_test_metrics": {
            "accuracy": test_metrics["accuracy"],
            "precision": test_metrics["precision"],
            "recall": test_metrics["recall"],
            "f1": test_metrics["f1"],
        },
    }
    with open(RESULTS_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Best model saved: best_model.joblib ({best_name})")
    print(f"✓ Comparison report saved: model_comparison.json")
    print(f"✓ TF-IDF vectorizer saved: tfidf_vectorizer.joblib")
    print(f"✓ Scaler saved: scaler.joblib")

    return summary


if __name__ == "__main__":
    main()
