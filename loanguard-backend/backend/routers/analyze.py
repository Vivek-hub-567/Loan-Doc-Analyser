"""
backend/routers/analyze.py — Analysis endpoints for LoanGuard AI.

Routes:
  POST /api/v1/analyze          — text analysis
  POST /api/v1/analyze/file     — file upload analysis
  POST /api/v1/analyze/batch    — batch text analysis (background)
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, File

from backend.dependencies import get_extractor, get_model, get_rag_explainer, get_database_service
from backend.schemas.request import AnalyzeRequest, BatchRequest
from backend.schemas.response import AnalyzeResponse, BatchResponse
from backend.services.analyzer import analyze_document
from backend.services.file_parser import parse_file
from backend.utils.validators import validate_text, validate_file, validate_file_size
from backend.utils.logger import request_id_ctx
from backend.middleware.rate_limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# POST /api/v1/analyze
# ---------------------------------------------------------------------------

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze Loan Agreement Text",
    description=(
        "Submit loan agreement text for full risk analysis. "
        "Returns risk score, sentiment, entities, keywords, summary, and classifier predictions."
    ),
    status_code=200,
)
@limiter.limit("10/minute")
async def analyze_text(
    request: Request,
    body: AnalyzeRequest,
    extractor=Depends(get_extractor),
    db=Depends(get_database_service),
    rag=Depends(get_rag_explainer),
) -> AnalyzeResponse:
    pipeline, mlb = get_model(request)

    # Validate text (word count, char limit)
    validate_text(body.text, instance="/api/v1/analyze")

    logger.info(
        "Analyzing text",
        extra={"endpoint": "/api/v1/analyze", "request_id": request_id_ctx.get("")},
    )

    result = analyze_document(
        text=body.text,
        options=body.options,
        extractor=extractor,
        pipeline=pipeline,
        mlb=mlb,
        rag_explainer=rag,
    )

    # Persist result
    await db.save_analysis(result.doc_id, result.model_dump())

    return result


# ---------------------------------------------------------------------------
# POST /api/v1/analyze/file
# ---------------------------------------------------------------------------

@router.post(
    "/analyze/file",
    response_model=AnalyzeResponse,
    summary="Analyze Uploaded Loan Agreement File",
    description="Upload a .txt, .pdf, or .docx file for risk analysis. Max file size: 5MB.",
    status_code=200,
)
@limiter.limit("10/minute")
async def analyze_file(
    request: Request,
    file: UploadFile = File(..., description="Loan agreement file (.txt, .pdf, .docx)"),
    extractor=Depends(get_extractor),
    db=Depends(get_database_service),
    rag=Depends(get_rag_explainer),
) -> AnalyzeResponse:
    pipeline, mlb = get_model(request)

    # Validate file type
    validate_file(file, instance="/api/v1/analyze/file")

    # Read content
    content = await file.read()
    await validate_file_size(content, instance="/api/v1/analyze/file")

    # Parse file
    parsed = parse_file(content, file.filename or "upload.txt")

    # Validate extracted text
    validate_text(parsed.text, instance="/api/v1/analyze/file")

    logger.info(
        "Analyzing file",
        extra={
            "endpoint": "/api/v1/analyze/file",
            "request_id": request_id_ctx.get(""),
            "file_name": file.filename,
            "file_type": parsed.file_type,
        },
    )

    # Default options (all enabled)
    from backend.schemas.request import AnalysisOptions
    options = AnalysisOptions()

    result = analyze_document(
        text=parsed.text,
        options=options,
        extractor=extractor,
        pipeline=pipeline,
        mlb=mlb,
        rag_explainer=rag,
        file_name=parsed.file_name,
        file_type=parsed.file_type,
        page_count=parsed.page_count,
    )

    await db.save_analysis(result.doc_id, result.model_dump())
    return result


# ---------------------------------------------------------------------------
# POST /api/v1/analyze/batch
# ---------------------------------------------------------------------------

@router.post(
    "/analyze/batch",
    response_model=BatchResponse,
    summary="Batch Analyze Loan Agreements",
    description="Submit up to 10 loan agreement texts for background batch processing. Returns immediately with a batch_id.",
    status_code=202,
)
@limiter.limit("5/minute")
async def analyze_batch(
    request: Request,
    body: BatchRequest,
    background_tasks: BackgroundTasks,
    extractor=Depends(get_extractor),
    db=Depends(get_database_service),
    rag=Depends(get_rag_explainer),
) -> BatchResponse:
    pipeline, mlb = get_model(request)

    if len(body.texts) > 10:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://loanGuard.ai/errors/validation-error",
                "title": "Batch Too Large",
                "status": 400,
                "detail": "Batch may contain at most 10 documents.",
                "instance": "/api/v1/analyze/batch",
                "request_id": request_id_ctx.get(""),
            },
        )

    batch_id = str(uuid.uuid4())
    await db.save_batch(
        batch_id,
        {"status": "processing", "result": None, "document_count": len(body.texts)},
    )

    background_tasks.add_task(
        _process_batch,
        batch_id=batch_id,
        texts=body.texts,
        options=body.options,
        extractor=extractor,
        pipeline=pipeline,
        mlb=mlb,
        rag_explainer=rag,
        db=db,
    )

    return BatchResponse(
        batch_id=batch_id,
        status="processing",
        document_count=len(body.texts),
        message=f"Batch of {len(body.texts)} documents queued. "
                f"Fetch results via GET /api/v1/history/{batch_id}",
    )


async def _process_batch(
    batch_id: str,
    texts: list[str],
    options,
    extractor,
    pipeline,
    mlb,
    rag_explainer,
    db,
) -> None:
    """Background task to process a batch of documents."""
    results = []
    for text in texts:
        try:
            # Quick word count validation
            if len(text.split()) < 50:
                results.append({"error": "Too short", "text_preview": text[:50]})
                continue
            res = analyze_document(
                text=text,
                options=options,
                extractor=extractor,
                pipeline=pipeline,
                mlb=mlb,
                rag_explainer=rag_explainer,
            )
            results.append(res.model_dump())
        except Exception as e:
            logger.error("Batch item failed: %s", e)
            results.append({"error": str(e)})

    await db.update_batch_result(
        batch_id,
        {"status": "completed", "result": results},
    )
    logger.info("Batch %s completed: %d documents", batch_id, len(texts))
