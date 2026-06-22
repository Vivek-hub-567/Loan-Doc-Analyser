"""
backend/routers/history.py — GET/DELETE /api/v1/history/{doc_id}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_database_service
from backend.schemas.response import AnalyzeResponse, HistoryItem
from backend.utils.logger import request_id_ctx

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/history/{doc_id}",
    response_model=HistoryItem,
    summary="Get Analysis Result",
    description="Retrieve a previously computed analysis result by document ID or batch ID.",
)
async def get_history(
    doc_id: str,
    db=Depends(get_database_service),
) -> HistoryItem:
    result = await db.get_analysis(doc_id)
    if result is None:
        # Also check batch store
        batch = await db.get_batch(doc_id)
        if batch is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": "https://loanGuard.ai/errors/not-found",
                    "title": "Analysis Not Found",
                    "status": 404,
                    "detail": f"No analysis found for doc_id '{doc_id}'.",
                    "instance": f"/api/v1/history/{doc_id}",
                    "request_id": request_id_ctx.get(""),
                },
            )
        return HistoryItem(
            doc_id=doc_id,
            status=batch.get("status", "processing"),
            result=batch.get("result"),
        )

    return HistoryItem(
        doc_id=doc_id,
        status="completed",
        result=AnalyzeResponse(**result) if isinstance(result, dict) else result,
    )


@router.delete(
    "/history/{doc_id}",
    summary="Delete Analysis Result",
    description="Delete a stored analysis result by document ID.",
)
async def delete_history(
    doc_id: str,
    db=Depends(get_database_service),
) -> dict:
    deleted = await db.delete_analysis(doc_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://loanGuard.ai/errors/not-found",
                "title": "Analysis Not Found",
                "status": 404,
                "detail": f"No analysis found for doc_id '{doc_id}' to delete.",
                "instance": f"/api/v1/history/{doc_id}",
                "request_id": request_id_ctx.get(""),
            },
        )
    return {"deleted": True, "doc_id": doc_id}
