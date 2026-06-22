"""
backend/services/analyzer.py — Pipeline orchestrator for LoanGuard AI.

Calls all NLP and ML services in sequence and maps results
to typed Pydantic response models.
"""

from __future__ import annotations

import time
import uuid
import logging
from typing import Any

from backend.schemas.response import (
    AnalyzeResponse,
    CategoryBreakdown,
    ClassifierPrediction,
    EntityMatch,
    EntityResponse,
    EntitySummary,
    FlaggedClause,
    KeySentence,
    RAGResult,
    RAGSource,
    SentimentResponse,
    SummaryResponse,
    TFIDFTerm,
    WorstClause,
)
from backend.services.extractor import run_keyword_extraction
from backend.services.sentiment import run_sentiment_analysis
from backend.services.ner import run_ner
from backend.services.summarizer import run_summarization
from backend.services.classifier import run_classifier_document
from nlp.preprocessing import TFIDFAnalyzer, preprocess

logger = logging.getLogger(__name__)


def analyze_document(
    text: str,
    options: Any,
    extractor: Any,
    pipeline: Any,
    mlb: Any,
    rag_explainer: Any | None = None,
    file_name: str | None = None,
    file_type: str | None = None,
    page_count: int | None = None,
) -> AnalyzeResponse:
    """
    Orchestrate the full LoanGuard AI analysis pipeline.

    Args:
        text         : cleaned document text
        options      : AnalysisOptions model
        extractor    : KeywordExtractor instance
        pipeline     : sklearn classifier pipeline
        mlb          : MultiLabelBinarizer
        rag_explainer: RAGExplainer instance (or None)
        file_name    : original filename (for file endpoint)
        file_type    : detected file type
        page_count   : number of pages (PDF only)

    Returns:
        AnalyzeResponse
    """
    start_ts = time.monotonic()
    doc_id = str(uuid.uuid4())

    # --- 1. Preprocessing ---
    preprocessed = preprocess(text)
    word_count: int = preprocessed["word_count"]
    sentence_count: int = preprocessed["sentence_count"]

    # --- 2. Keyword Extraction (always runs) ---
    kw_result = run_keyword_extraction(text, extractor)
    risk_score: float = kw_result["risk_score"]
    risk_level: str = kw_result["risk_level"]
    top_flags: list[str] = kw_result["top_flags"]
    category_breakdown_raw: list[dict] = kw_result["category_breakdown"]

    # --- 3. Sentiment Analysis ---
    sentiment_response: SentimentResponse | None = None
    if options.run_sentiment:
        sent = run_sentiment_analysis(text)
        sentiment_response = SentimentResponse(
            label=sent["label"],
            compound_score=sent["compound_score"],
            positive=sent["positive"],
            negative=sent["negative"],
            neutral=sent["neutral"],
            aggressive_score=sent["aggressive_score"],
            aggressive_hits=sent["aggressive_hits"],
            friendly_score=sent["friendly_score"],
            friendly_hits=sent["friendly_hits"],
            worst_clauses=[
                WorstClause(sentence=c["sentence"], compound=c["compound"])
                for c in sent["worst_clauses"]
            ],
        )

    # --- 4. NER ---
    entity_response: EntityResponse | None = None
    if options.run_ner:
        ner = run_ner(text)
        summary_data = ner.get("summary", {})
        entity_response = EntityResponse(
            MONEY=_to_entity_matches(ner.get("MONEY", [])),
            RATE=_to_entity_matches(ner.get("RATE", [])),
            FEE_AMOUNT=_to_entity_matches(ner.get("FEE_AMOUNT", [])),
            LOAN_AMOUNT=_to_entity_matches(ner.get("LOAN_AMOUNT", [])),
            DURATION=_to_entity_matches(ner.get("DURATION", [])),
            DATE=_to_entity_matches(ner.get("DATE", [])),
            ORG=_to_entity_matches(ner.get("ORG", [])),
            CLAUSE_TYPE=_to_entity_matches(ner.get("CLAUSE_TYPE", [])),
            REGULATION=_to_entity_matches(ner.get("REGULATION", [])),
            summary=EntitySummary(
                total_entities=summary_data.get("total_entities", 0),
                money_mentions=summary_data.get("money_mentions", 0),
                rate_mentions=summary_data.get("rate_mentions", 0),
                fee_mentions=summary_data.get("fee_mentions", 0),
                clause_types=summary_data.get("clause_types", []),
                regulations=summary_data.get("regulations", []),
            ),
        )

    # --- 5. TF-IDF Terms ---
    tfidf_terms: list[TFIDFTerm] | None = None
    if options.run_tfidf:
        try:
            tfidf_analyzer = TFIDFAnalyzer()
            terms = tfidf_analyzer.top_terms(text, top_n=options.tfidf_top_n)
            tfidf_terms = [TFIDFTerm(term=t["term"], score=t["score"]) for t in terms]
        except Exception as e:
            logger.error("TF-IDF term extraction failed: %s", e)

    # --- 6. Summarization ---
    summary_response: SummaryResponse | None = None
    if options.run_summary:
        summ = run_summarization(text, top_n=options.summary_top_n)
        summary_response = SummaryResponse(
            text=summ["text"],
            key_sentences=[
                KeySentence(
                    sentence=s["sentence"],
                    score=s["score"],
                    position=s["position"],
                    rank=s["rank"],
                )
                for s in summ["key_sentences"]
            ],
            sentence_count=summ["sentence_count"],
            compression_ratio=summ["compression_ratio"],
            method=summ["method"],
        )

    # --- 7. Classifier ---
    classifier_predictions: list[ClassifierPrediction] | None = None
    if options.run_classifier and pipeline is not None:
        preds = run_classifier_document(text, pipeline, mlb)
        classifier_predictions = [
            ClassifierPrediction(
                chunk=p["chunk"],
                predictions=p["predictions"],
                top_label=p["top_label"],
            )
            for p in preds
        ]

    # --- 8. RAG Explainer ---
    rag_result: RAGResult | None = None
    if options.run_rag and rag_explainer is not None:
        try:
            sentiment_label = sentiment_response.label if sentiment_response else "NEUTRAL"
            rag_raw = rag_explainer.explain(
                top_flags=top_flags,
                risk_level=risk_level,
                category_breakdown=category_breakdown_raw,
                sentiment_label=sentiment_label,
            )
            rag_result = RAGResult(
                should_sign=rag_raw["should_sign"],
                overall_summary=rag_raw["overall_summary"],
                flagged_clauses=[
                    FlaggedClause(**c) for c in rag_raw["flagged_clauses"]
                ],
                regulatory_violations=[
                    FlaggedClause(**c) for c in rag_raw["regulatory_violations"]
                ],
                borrower_action_plan=rag_raw["borrower_action_plan"],
                questions_to_ask_lender=rag_raw["questions_to_ask_lender"],
                retrieved_sources=[
                    RAGSource(title=s["title"], snippet=s["snippet"], score=s["score"])
                    for s in rag_raw["retrieved_sources"]
                ],
            )
        except Exception as e:
            logger.error("RAG explainer failed: %s", e)

    # --- Determine should_sign ---
    should_sign = risk_level not in ("CRITICAL", "HIGH")
    if sentiment_response and sentiment_response.label == "THREATENING":
        should_sign = False

    # --- Category breakdown typed ---
    category_breakdown = [
        CategoryBreakdown(
            category_id=cat["category_id"],
            label=cat["label"],
            severity=cat["severity"],
            keyword_hits=cat["keyword_hits"],
            matched_keywords=cat["matched_keywords"],
            risk_weight=cat["risk_weight"],
            weighted_score=cat["weighted_score"],
            negated_hits=cat.get("negated_hits", 0),
        )
        for cat in category_breakdown_raw
    ]

    elapsed_ms = round((time.monotonic() - start_ts) * 1000, 2)

    return AnalyzeResponse(
        doc_id=doc_id,
        risk_score=risk_score,
        risk_level=risk_level,  # type: ignore[arg-type]
        should_sign=should_sign,
        processing_time_ms=elapsed_ms,
        word_count=word_count,
        sentence_count=sentence_count,
        sentiment=sentiment_response,
        entities=entity_response,
        category_breakdown=category_breakdown,
        top_flags=top_flags,
        tfidf_terms=tfidf_terms,
        summary=summary_response,
        classifier_predictions=classifier_predictions,
        rag_result=rag_result,
        file_name=file_name,
        file_type=file_type,
        page_count=page_count,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_entity_matches(raw: list[dict]) -> list[EntityMatch]:
    result = []
    for item in raw:
        if isinstance(item, dict) and "text" in item:
            result.append(
                EntityMatch(
                    text=item["text"],
                    normalized=item.get("normalized", item["text"]),
                    start=item.get("start", 0),
                    end=item.get("end", 0),
                )
            )
    return result
