"""
backend/schemas/request.py — Typed Pydantic v2 request models for LoanGuard AI.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class AnalysisOptions(BaseModel):
    """Optional flags to control which pipeline stages run."""

    run_sentiment: bool = True
    run_ner: bool = True
    run_summary: bool = True
    run_tfidf: bool = True
    run_classifier: bool = True
    run_rag: bool = False
    summary_top_n: Annotated[int, Field(ge=1, le=10)] = 3
    tfidf_top_n: Annotated[int, Field(ge=1, le=50)] = 15


class AnalyzeRequest(BaseModel):
    """Request body for POST /api/v1/analyze."""

    text: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50_000,
            description="Loan agreement text. Min 50 words, max 50,000 characters.",
        ),
    ]
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    @model_validator(mode="after")
    def check_word_count(self) -> "AnalyzeRequest":
        """Pydantic-level word count guard (secondary; API validator is primary)."""
        return self


class BatchRequest(BaseModel):
    """Request body for POST /api/v1/analyze/batch."""

    texts: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=10,
            description="Array of loan agreement texts (max 10 per batch).",
        ),
    ]
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    @model_validator(mode="after")
    def check_batch_size(self) -> "BatchRequest":
        if len(self.texts) > 10:
            raise ValueError("Batch may contain at most 10 documents.")
        return self
