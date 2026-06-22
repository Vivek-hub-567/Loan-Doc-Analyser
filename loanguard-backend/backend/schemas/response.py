"""
backend/schemas/response.py — Typed Pydantic v2 response models for LoanGuard AI.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------

class WorstClause(BaseModel):
    sentence: str
    compound: float


class SentimentResponse(BaseModel):
    label: Literal[
        "THREATENING", "NEGATIVE", "NEUTRAL", "NEUTRAL_POSITIVE", "BORROWER_FRIENDLY"
    ]
    compound_score: float
    positive: float
    negative: float
    neutral: float
    aggressive_score: float
    aggressive_hits: list[str]
    friendly_score: float
    friendly_hits: list[str]
    worst_clauses: list[WorstClause]


# ---------------------------------------------------------------------------
# NER / Entities
# ---------------------------------------------------------------------------

class EntityMatch(BaseModel):
    text: str
    normalized: str
    start: int
    end: int


class EntitySummary(BaseModel):
    total_entities: int
    money_mentions: int
    rate_mentions: int
    fee_mentions: int
    clause_types: list[str] = Field(default_factory=list)
    regulations: list[str] = Field(default_factory=list)


class EntityResponse(BaseModel):
    MONEY: list[EntityMatch] = Field(default_factory=list)
    RATE: list[EntityMatch] = Field(default_factory=list)
    FEE_AMOUNT: list[EntityMatch] = Field(default_factory=list)
    LOAN_AMOUNT: list[EntityMatch] = Field(default_factory=list)
    DURATION: list[EntityMatch] = Field(default_factory=list)
    DATE: list[EntityMatch] = Field(default_factory=list)
    ORG: list[EntityMatch] = Field(default_factory=list)
    CLAUSE_TYPE: list[EntityMatch] = Field(default_factory=list)
    REGULATION: list[EntityMatch] = Field(default_factory=list)
    summary: EntitySummary


# ---------------------------------------------------------------------------
# TF-IDF Terms
# ---------------------------------------------------------------------------

class TFIDFTerm(BaseModel):
    term: str
    score: float


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class KeySentence(BaseModel):
    sentence: str
    score: float
    position: int
    rank: int


class SummaryResponse(BaseModel):
    text: str
    key_sentences: list[KeySentence]
    sentence_count: int
    compression_ratio: float
    method: Literal["textrank", "tfidf"]


# ---------------------------------------------------------------------------
# Category Breakdown
# ---------------------------------------------------------------------------

class CategoryBreakdown(BaseModel):
    category_id: str
    label: str
    severity: str
    keyword_hits: int
    matched_keywords: list[str]
    risk_weight: int
    weighted_score: float
    negated_hits: int = 0


# ---------------------------------------------------------------------------
# Classifier Predictions
# ---------------------------------------------------------------------------

class ClassifierPrediction(BaseModel):
    chunk: str
    predictions: dict[str, float]
    top_label: str


# ---------------------------------------------------------------------------
# RAG Result
# ---------------------------------------------------------------------------

class RAGSource(BaseModel):
    title: str
    snippet: str
    score: float


class FlaggedClause(BaseModel):
    category: str
    severity: str
    keywords: list[str]
    explanation: str


class RAGResult(BaseModel):
    should_sign: bool
    overall_summary: str
    flagged_clauses: list[FlaggedClause]
    regulatory_violations: list[FlaggedClause]
    borrower_action_plan: list[str]
    questions_to_ask_lender: list[str]
    retrieved_sources: list[RAGSource]


# ---------------------------------------------------------------------------
# Main Analysis Response
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    doc_id: str
    risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    should_sign: bool
    processing_time_ms: float
    word_count: int
    sentence_count: int
    sentiment: SentimentResponse | None = None
    entities: EntityResponse | None = None
    category_breakdown: list[CategoryBreakdown] = Field(default_factory=list)
    top_flags: list[str] = Field(default_factory=list)
    tfidf_terms: list[TFIDFTerm] | None = None
    summary: SummaryResponse | None = None
    classifier_predictions: list[ClassifierPrediction] | None = None
    rag_result: RAGResult | None = None

    # File upload extras (None for text-only requests)
    file_name: str | None = None
    file_type: str | None = None
    page_count: int | None = None


# ---------------------------------------------------------------------------
# Batch Response
# ---------------------------------------------------------------------------

class BatchResponse(BaseModel):
    batch_id: str
    status: Literal["processing", "completed", "failed"]
    document_count: int
    message: str


# ---------------------------------------------------------------------------
# Categories Endpoint
# ---------------------------------------------------------------------------

class CategoryInfo(BaseModel):
    id: str
    label: str
    severity: str
    keyword_count: int
    keywords: list[str]


class CategoriesResponse(BaseModel):
    categories: list[CategoryInfo]
    total_keywords: int
    version: str


# ---------------------------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    model_loaded: bool
    vader_available: bool
    nltk_data_ready: bool
    uptime_seconds: float
    version: str


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class HistoryItem(BaseModel):
    doc_id: str
    status: Literal["processing", "completed", "failed"]
    result: AnalyzeResponse | None = None


# ---------------------------------------------------------------------------
# Error (RFC 7807)
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    request_id: str = ""
