"""
backend/main.py — FastAPI application entry point for LoanGuard AI.

Startup:
  - Downloads NLTK datasets (punkt, wordnet, stopwords, averaged_perceptron_tagger)
  - Loads ML classifier model (ml/model.pkl)
  - Loads keyword extractor config (ml/keywords_config.json)
  - Initialises RAG explainer (knowledge_base/)
  - Initialises database service stub

Middleware:
  - CORS
  - Request ID (UUID4 per request → X-Request-ID header)
  - Rate Limiter (slowapi)
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Add project root to sys.path for ml/ and nlp/ imports
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.config import get_settings
from backend.middleware.cors import add_cors_middleware
from backend.middleware.rate_limiter import limiter
from backend.middleware.request_id import RequestIDMiddleware
from backend.routers import analyze, categories, health, history
from backend.services.database import get_database
from backend.utils.logger import request_id_ctx, setup_logging

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Startup / Shutdown — Lifespan Context Manager
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load all heavy resources once at startup."""
    logger.info("LoanGuard AI backend starting up (v%s)…", settings.app_version)

    # 1. NLTK datasets
    _ensure_nltk_data()

    # 2. Keyword extractor
    from ml.keyword_extractor import KeywordExtractor, load_keywords_config
    kw_config = load_keywords_config(settings.keywords_config_path)
    app.state.extractor = KeywordExtractor(kw_config)
    logger.info("KeywordExtractor loaded.")

    # 3. Classifier model
    from ml.classifier import load_model
    pipeline, mlb = load_model(settings.model_path)
    app.state.pipeline = pipeline
    app.state.mlb = mlb
    if pipeline is None:
        logger.warning(
            "Classifier model not found at '%s'. "
            "Run `python -m ml.train_classifier` to generate it. "
            "Classifier predictions will be disabled.",
            settings.model_path,
        )

    # 4. RAG explainer
    try:
        from ml.rag_explainer import RAGExplainer
        app.state.rag_explainer = RAGExplainer()
        logger.info("RAGExplainer initialised.")
    except Exception as e:
        app.state.rag_explainer = None
        logger.warning("RAGExplainer failed to load: %s", e)

    # 5. Database service
    app.state.db = get_database()
    logger.info("DatabaseService initialised.")

    logger.info("All resources loaded — server is ready.")
    yield

    logger.info("LoanGuard AI backend shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="LoanGuard AI",
        description=(
            "A Loan Agreement Risk Analyzer protecting Indian borrowers from predatory digital lending. "
            "Scans loan agreements and returns structured risk reports covering hidden fees, "
            "default clauses, privacy violations, power imbalance, and regulatory non-compliance."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- Middleware ---
    add_cors_middleware(app)
    app.add_middleware(RequestIDMiddleware)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # --- Routers ---
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix, tags=["Health"])
    app.include_router(categories.router, prefix=api_prefix, tags=["Categories"])
    app.include_router(analyze.router, prefix=api_prefix, tags=["Analysis"])
    app.include_router(history.router, prefix=api_prefix, tags=["History"])

    # --- Exception handlers ---
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "type": "https://loanGuard.ai/errors/rate-limit-exceeded",
                "title": "Too Many Requests",
                "status": 429,
                "detail": f"Rate limit exceeded: {exc.detail}. Please wait before retrying.",
                "instance": str(request.url.path),
                "request_id": request_id_ctx.get(""),
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "type": "https://loanGuard.ai/errors/not-found",
                "title": "Not Found",
                "status": 404,
                "detail": f"The requested resource '{request.url.path}' was not found.",
                "instance": str(request.url.path),
                "request_id": request_id_ctx.get(""),
            },
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc) -> JSONResponse:
        logger.exception("Unhandled server error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://loanGuard.ai/errors/internal-server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred. Please try again or contact support.",
                "instance": str(request.url.path),
                "request_id": request_id_ctx.get(""),
            },
        )

    return app


app = create_app()


# ---------------------------------------------------------------------------
# NLTK bootstrap helper
# ---------------------------------------------------------------------------

def _ensure_nltk_data() -> None:
    """Download required NLTK datasets if not already present."""
    try:
        import nltk

        datasets = [
            ("tokenizers/punkt", "punkt"),
            ("tokenizers/punkt_tab", "punkt_tab"),
            ("corpora/wordnet", "wordnet"),
            ("corpora/stopwords", "stopwords"),
            ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
            ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
        ]
        for check_path, download_name in datasets:
            try:
                nltk.data.find(check_path)
            except LookupError:
                logger.info("Downloading NLTK dataset: %s", download_name)
                nltk.download(download_name, quiet=True)

        logger.info("NLTK datasets ready.")
    except ImportError:
        logger.warning("NLTK not installed — preprocessing will use regex fallbacks.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
