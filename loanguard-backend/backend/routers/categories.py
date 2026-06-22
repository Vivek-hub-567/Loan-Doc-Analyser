"""
backend/routers/categories.py — GET /api/v1/categories
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from backend.dependencies import get_extractor
from backend.schemas.response import CategoriesResponse, CategoryInfo
from backend.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get(
    "/categories",
    response_model=CategoriesResponse,
    summary="List Risk Categories",
    description="Returns all 8 risk categories with their keywords, severity levels, and metadata.",
)
async def list_categories(
    extractor=Depends(get_extractor),
) -> CategoriesResponse:
    raw = extractor.get_categories_info()
    categories = [CategoryInfo(**cat) for cat in raw]
    total_keywords = sum(c.keyword_count for c in categories)

    return CategoriesResponse(
        categories=categories,
        total_keywords=total_keywords,
        version=settings.app_version,
    )
