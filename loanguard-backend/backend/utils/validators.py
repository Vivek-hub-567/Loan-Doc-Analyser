"""
backend/utils/validators.py — Validation helpers for text and file inputs.
"""

from __future__ import annotations

import re
from fastapi import UploadFile, HTTPException

from backend.config import get_settings

settings = get_settings()

ACCEPTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
ACCEPTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def validate_text(text: str, instance: str = "/api/v1/analyze") -> None:
    """
    Validate document text for length and content requirements.
    Raises HTTPException with RFC 7807-style body on failure.
    """
    from backend.utils.logger import request_id_ctx

    rid = request_id_ctx.get("")

    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://loanGuard.ai/errors/empty-document",
                "title": "Empty Document",
                "status": 400,
                "detail": "Document appears to be empty. Please provide loan agreement text.",
                "instance": instance,
                "request_id": rid,
            },
        )

    word_count = len(text.split())
    if word_count < settings.min_word_count:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://loanGuard.ai/errors/validation-error",
                "title": "Document Too Short",
                "status": 400,
                "detail": (
                    f"The provided text contains only {word_count} words. "
                    f"Minimum required is {settings.min_word_count} words for meaningful analysis."
                ),
                "instance": instance,
                "request_id": rid,
            },
        )

    if len(text) > settings.max_text_length:
        raise HTTPException(
            status_code=413,
            detail={
                "type": "https://loanGuard.ai/errors/payload-too-large",
                "title": "Document Too Large",
                "status": 413,
                "detail": (
                    f"The provided text is {len(text):,} characters long. "
                    f"Maximum allowed is {settings.max_text_length:,} characters."
                ),
                "instance": instance,
                "request_id": rid,
            },
        )

    # Non-latin script warning (Hindi / Marathi — warn but allow)
    latin_ratio = len(re.findall(r"[a-zA-Z]", text)) / max(len(text), 1)
    if latin_ratio < 0.1:
        # Log warning but do not block — non-latin scripts are valid
        import logging
        logging.getLogger(__name__).warning(
            "Low Latin character ratio (%.2f) — document may be non-English. Processing anyway.",
            latin_ratio,
        )


def validate_file(file: UploadFile, instance: str = "/api/v1/analyze/file") -> None:
    """Validate uploaded file type and size."""
    from backend.utils.logger import request_id_ctx

    rid = request_id_ctx.get("")

    # Check extension
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ACCEPTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "type": "https://loanGuard.ai/errors/unsupported-media-type",
                "title": "Unsupported File Type",
                "status": 415,
                "detail": (
                    f"File type '{ext}' is not supported. "
                    f"Accepted types: {', '.join(sorted(ACCEPTED_EXTENSIONS))}"
                ),
                "instance": instance,
                "request_id": rid,
            },
        )


async def validate_file_size(
    content: bytes,
    instance: str = "/api/v1/analyze/file",
) -> None:
    """Validate file content does not exceed max size."""
    from backend.utils.logger import request_id_ctx

    rid = request_id_ctx.get("")

    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "type": "https://loanGuard.ai/errors/payload-too-large",
                "title": "File Too Large",
                "status": 413,
                "detail": (
                    f"Uploaded file is {len(content) / 1_048_576:.1f} MB. "
                    f"Maximum allowed file size is {settings.max_file_size_mb} MB."
                ),
                "instance": instance,
                "request_id": rid,
            },
        )
