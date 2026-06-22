"""
Full feature extraction pipeline for the ML model.

Combines THREE signal sources:
  1. Keyword features   — lemma-aware matching across 8 risk categories
  2. TF-IDF features     — word-importance vector over a fitted vocabulary
                            (captures patterns beyond exact keyword lists)
  3. Document statistics — length, density, sentence structure

This is what makes it "NLP + ML" rather than just regex + ML:
TF-IDF lets the model learn from word patterns it was never explicitly
told about, while the keyword layer gives interpretable, explainable
risk flags for the RAG/explanation layer.
"""

import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nlp.keywords import KEYWORD_CATEGORIES, RISK_LEVEL_RANK
from nlp.preprocessing import clean_text, lemmatize_text, sentence_split
from nlp.keyword_matcher import extract_keyword_hits

TFIDF_VOCAB_SIZE = 300
TFIDF_PATH = os.path.join(os.path.dirname(__file__), "tfidf_vectorizer.joblib")


class FeatureExtractor:
    """
    Stateful feature extractor — the TF-IDF vectorizer must be FIT on the
    training corpus once, then reused (loaded) for all future inference.
    """

    def __init__(self):
        self.tfidf: TfidfVectorizer | None = None
        self._is_fit = False

    # ── TF-IDF lifecycle ──────────────────────────────────────────────

    def fit_tfidf(self, texts: list[str]):
        """Fit the TF-IDF vectorizer on lemmatized training texts."""
        lemmatized_corpus = [lemmatize_text(clean_text(t)) for t in texts]
        self.tfidf = TfidfVectorizer(
            max_features=TFIDF_VOCAB_SIZE,
            ngram_range=(1, 2),     # unigrams + bigrams ("penal interest")
            min_df=2,
            max_df=0.9,
            sublinear_tf=True,
        )
        self.tfidf.fit(lemmatized_corpus)
        self._is_fit = True
        return self

    def save_tfidf(self, path: str = TFIDF_PATH):
        import joblib
        joblib.dump(self.tfidf, path)

    def load_tfidf(self, path: str = TFIDF_PATH):
        import joblib
        self.tfidf = joblib.load(path)
        self._is_fit = True
        return self

    # ── Feature extraction ────────────────────────────────────────────

    def _keyword_features(self, text: str) -> dict:
        hits = extract_keyword_hits(text)
        cleaned = clean_text(text)
        word_count = len(cleaned.split())

        cat_counts, cat_scores, vec = {}, {}, []
        max_risk_rank = 0

        for cat_id, cat_data in KEYWORD_CATEGORIES.items():
            count = len(hits.get(cat_id, []))
            weight = cat_data["risk_weight"]
            score = count * weight

            cat_counts[cat_id] = count
            cat_scores[cat_id] = score
            vec.extend([count, score, float(count > 0)])

            if count > 0:
                rank = RISK_LEVEL_RANK.get(cat_data["risk_level"], 0)
                max_risk_rank = max(max_risk_rank, rank)

        total_keywords = sum(cat_counts.values())
        total_weighted = sum(cat_scores.values())
        density = total_keywords / max(1, word_count) * 100

        vec.extend([total_keywords, total_weighted, density, word_count, max_risk_rank])

        return {
            "hits": hits,
            "cat_counts": cat_counts,
            "cat_scores": cat_scores,
            "total_keywords": total_keywords,
            "total_weighted_score": total_weighted,
            "keyword_density": density,
            "word_count": word_count,
            "max_risk_rank": max_risk_rank,
            "vector": vec,
        }

    def _tfidf_features(self, text: str) -> np.ndarray:
        if not self._is_fit:
            raise RuntimeError("TF-IDF vectorizer not fit. Call fit_tfidf() or load_tfidf() first.")
        lemmatized = lemmatize_text(clean_text(text))
        return self.tfidf.transform([lemmatized]).toarray()[0]

    def extract(self, text: str) -> dict:
        """
        Full feature extraction. Returns keyword analysis (for explanation/RAG)
        PLUS the combined numeric feature vector (for the ML model).
        """
        kw = self._keyword_features(text)
        tfidf_vec = self._tfidf_features(text)
        sentences = sentence_split(text)

        full_vector = np.concatenate([
            np.array(kw["vector"], dtype=np.float32),
            tfidf_vec.astype(np.float32),
        ])

        return {
            "hits": kw["hits"],
            "cat_counts": kw["cat_counts"],
            "cat_scores": kw["cat_scores"],
            "total_keywords": kw["total_keywords"],
            "total_weighted_score": kw["total_weighted_score"],
            "keyword_density": kw["keyword_density"],
            "word_count": kw["word_count"],
            "sentence_count": max(1, len(sentences)),
            "max_risk_rank": kw["max_risk_rank"],
            "feature_vector": full_vector,
        }

    def feature_names(self) -> list[str]:
        names = []
        for cat_id in KEYWORD_CATEGORIES:
            names.extend([f"{cat_id}_count", f"{cat_id}_weighted_score", f"{cat_id}_present"])
        names.extend(["total_keywords", "total_weighted_score", "keyword_density",
                      "word_count", "max_risk_rank"])
        if self._is_fit:
            names.extend([f"tfidf_{t}" for t in self.tfidf.get_feature_names_out()])
        return names
