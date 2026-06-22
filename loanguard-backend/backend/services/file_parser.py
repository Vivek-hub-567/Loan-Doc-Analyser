"""
backend/services/file_parser.py — File extraction service for LoanGuard AI.

Supports:
  - PDF  : pdfplumber, page-by-page, joined with newline
  - DOCX : python-docx, paragraph-by-paragraph
  - TXT  : UTF-8 with latin-1 fallback
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ParsedFile:
    __slots__ = ("text", "file_name", "file_type", "page_count")

    def __init__(
        self,
        text: str,
        file_name: str,
        file_type: str,
        page_count: int | None = None,
    ) -> None:
        self.text = text
        self.file_name = file_name
        self.file_type = file_type
        self.page_count = page_count


def parse_file(content: bytes, filename: str) -> ParsedFile:
    """
    Extract text from file content bytes.

    Args:
        content  : raw file bytes
        filename : original filename (used to detect type)

    Returns:
        ParsedFile with text, metadata
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(content, filename)
    elif ext == ".docx":
        return _parse_docx(content, filename)
    elif ext == ".txt":
        return _parse_txt(content, filename)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


# ---------------------------------------------------------------------------

def _parse_pdf(content: bytes, filename: str) -> ParsedFile:
    try:
        import pdfplumber

        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(page_text)
        text = "\n\n".join(pages)
        logger.info("PDF parsed: %s, %d pages", filename, len(pages))
        return ParsedFile(
            text=text,
            file_name=filename,
            file_type="pdf",
            page_count=len(pages),
        )
    except ImportError:
        raise RuntimeError("pdfplumber is not installed. Install it with: pip install pdfplumber")
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF '{filename}': {e}") from e


def _parse_docx(content: bytes, filename: str) -> ParsedFile:
    try:
        import docx

        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        logger.info("DOCX parsed: %s, %d paragraphs", filename, len(paragraphs))
        return ParsedFile(text=text, file_name=filename, file_type="docx")
    except ImportError:
        raise RuntimeError("python-docx is not installed. Install it with: pip install python-docx")
    except Exception as e:
        raise RuntimeError(f"Failed to parse DOCX '{filename}': {e}") from e


def _parse_txt(content: bytes, filename: str) -> ParsedFile:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
            logger.info("TXT decoded with latin-1 fallback: %s", filename)
        except Exception as e:
            raise RuntimeError(f"Failed to decode TXT '{filename}': {e}") from e
    return ParsedFile(text=text, file_name=filename, file_type="txt")
