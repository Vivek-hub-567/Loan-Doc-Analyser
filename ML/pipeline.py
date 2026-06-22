"""
Full end-to-end loan document analysis pipeline.

  raw text
     -> NLP preprocessing (lemmatization, cleaning)
     -> Keyword + TF-IDF feature extraction
     -> ML risk classifier (best model from comparison)
     -> RAG retrieval (knowledge base lookup for flagged clauses)
     -> RAG explanation generation (structured report)
     -> final result

No external LLM API is used anywhere in this pipeline.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ml.risk_classifier import LoanRiskClassifier
from rag.retriever import RagRetriever
from rag.explainer import RagExplainer


class LoanAnalysisPipeline:
    """Single entry point: raw text in, full risk report out."""

    def __init__(self):
        self.classifier = LoanRiskClassifier().load()
        self.retriever = RagRetriever()
        if self.retriever.index_exists():
            self.retriever.load_index()
        else:
            self.retriever.build_index()
            self.retriever.save_index()
        self.explainer = RagExplainer(retriever=self.retriever)

    def analyze(self, text: str) -> dict:
        if not text or not text.strip():
            return {"error": "Empty document provided"}

        t0 = time.time()
        ml_result = self.classifier.predict(text)
        ml_time = round((time.time() - t0) * 1000)

        t1 = time.time()
        rag_result = self.explainer.explain(ml_result)
        rag_time = round((time.time() - t1) * 1000)

        return {
            "risk_label": ml_result["risk_label"],
            "risk_display": ml_result["risk_display"],
            "risk_score": ml_result["risk_score"],
            "confidence": ml_result["confidence_pct"],
            "should_sign": rag_result["should_sign"],
            "overall_summary": rag_result["overall_summary"],
            "flagged_clauses": rag_result["flagged_clauses"],
            "regulatory_violations": rag_result["regulatory_violations"],
            "borrower_action_plan": rag_result["borrower_action_plan"],
            "questions_to_ask_lender": rag_result["questions_to_ask_lender"],
            "retrieved_sources": rag_result["retrieved_sources"],
            "ml": ml_result,
            "meta": {
                "ml_latency_ms": ml_time,
                "rag_latency_ms": rag_time,
                "total_latency_ms": ml_time + rag_time,
                "model_used": ml_result["model_used"],
            },
        }

    def status(self) -> dict:
        return {
            "classifier": self.classifier.status(),
            "rag_documents_indexed": len(self.retriever.documents),
        }
