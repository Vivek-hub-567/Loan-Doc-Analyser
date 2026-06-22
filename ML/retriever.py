"""
RAG Retriever for the loan document analyzer.

This is the core RAG component:
  1. INDEX   — embed all 55 knowledge base documents into vectors
  2. RETRIEVE — given a flagged keyword/clause, find the most relevant
                knowledge base entries by cosine similarity
  3. AUGMENT  — attach retrieved context to the ML's flagged clauses

No external LLM call is required for retrieval — only for the final
generation step (separate, optional module). This retriever uses
TF-IDF + cosine similarity, which is a legitimate, classic RAG
retrieval method and works fully offline.
"""

import os
import sys
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from knowledge_base.loader import load_all_documents

INDEX_DIR = os.path.dirname(__file__)
VECTORIZER_PATH = os.path.join(INDEX_DIR, "rag_vectorizer.joblib")
MATRIX_PATH = os.path.join(INDEX_DIR, "rag_doc_matrix.joblib")
DOCS_PATH = os.path.join(INDEX_DIR, "rag_docs.joblib")


class RagRetriever:
    """
    TF-IDF based retriever over the loan-knowledge knowledge base.
    Build once (build_index), then reuse (load_index) for fast retrieval.
    """

    def __init__(self):
        self.vectorizer: TfidfVectorizer | None = None
        self.doc_matrix = None
        self.documents: list[dict] = []
        self._ready = False

    # ── Index building ───────────────────────────────────────────────

    def build_index(self):
        """Build the retrieval index from the knowledge base."""
        self.documents = load_all_documents()

        # Index on title + content + keywords for richer matching
        corpus = [
            f"{d['title']} {d['content']} {' '.join(d.get('keywords', []))}"
            for d in self.documents
        ]

        self.vectorizer = TfidfVectorizer(
            max_features=4000,
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
            sublinear_tf=True,
        )
        self.doc_matrix = self.vectorizer.fit_transform(corpus)
        self._ready = True
        return self

    def save_index(self):
        joblib.dump(self.vectorizer, VECTORIZER_PATH)
        joblib.dump(self.doc_matrix, MATRIX_PATH)
        joblib.dump(self.documents, DOCS_PATH)

    def load_index(self):
        self.vectorizer = joblib.load(VECTORIZER_PATH)
        self.doc_matrix = joblib.load(MATRIX_PATH)
        self.documents = joblib.load(DOCS_PATH)
        self._ready = True
        return self

    def index_exists(self) -> bool:
        return all(os.path.exists(p) for p in [VECTORIZER_PATH, MATRIX_PATH, DOCS_PATH])

    # ── Retrieval ─────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.05) -> list[dict]:
        """
        Retrieve the top_k most relevant knowledge base documents for a query.
        Query is typically a flagged keyword or clause name, e.g.
        "auto-debit without consent" or "sole discretion".
        """
        if not self._ready:
            raise RuntimeError("Index not built/loaded. Call build_index() or load_index() first.")

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_matrix).flatten()

        ranked_idx = np.argsort(scores)[::-1]
        results = []
        for idx in ranked_idx[:top_k]:
            if scores[idx] < min_score:
                continue
            doc = self.documents[idx]
            results.append({
                "doc_id": doc["id"],
                "title": doc["title"],
                "source": doc["source"],
                "category": doc["category"],
                "content": doc["content"],
                "risk_level": doc.get("risk_level", "info"),
                "relevance_score": round(float(scores[idx]), 4),
            })
        return results

    def retrieve_for_keywords(self, keywords: list[str], top_k_per_keyword: int = 2) -> dict:
        """
        Retrieve relevant knowledge for a list of flagged keywords
        (typically the ML model's top_flags). Deduplicates documents
        that match multiple keywords.
        """
        seen_ids = set()
        retrieved = []

        for kw in keywords:
            hits = self.retrieve(kw, top_k=top_k_per_keyword)
            for hit in hits:
                if hit["doc_id"] not in seen_ids:
                    hit["matched_keyword"] = kw
                    retrieved.append(hit)
                    seen_ids.add(hit["doc_id"])

        # Sort by relevance descending
        retrieved.sort(key=lambda x: x["relevance_score"], reverse=True)
        return {
            "query_keywords": keywords,
            "retrieved_documents": retrieved,
            "total_retrieved": len(retrieved),
        }

    def retrieve_by_category(self, category_id: str, top_k: int = 5) -> list[dict]:
        """
        Direct exact-match retrieval for a specific keyword category
        (e.g. 'predatory', 'power_imbalance') by matching category keywords.
        """
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
        from nlp.keywords import KEYWORD_CATEGORIES

        cat = KEYWORD_CATEGORIES.get(category_id)
        if not cat:
            return []
        query = " ".join(cat["keywords"])
        return self.retrieve(query, top_k=top_k)


def build_and_save_index():
    """CLI helper: build the RAG index and persist it to disk."""
    retriever = RagRetriever()
    retriever.build_index()
    retriever.save_index()
    print(f"✓ RAG index built: {len(retriever.documents)} documents indexed")
    print(f"✓ Saved to: {INDEX_DIR}")
    return retriever


if __name__ == "__main__":
    build_and_save_index()
