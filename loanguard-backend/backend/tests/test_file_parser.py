"""
backend/tests/test_file_parser.py — Unit tests for file parsing service.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.services.file_parser import parse_file, ParsedFile


# ---------------------------------------------------------------------------
# TXT tests
# ---------------------------------------------------------------------------

def test_parse_txt_utf8():
    content = b"This is a loan agreement. The borrower agrees to repay the loan."
    result = parse_file(content, "test.txt")
    assert isinstance(result, ParsedFile)
    assert result.file_type == "txt"
    assert "loan" in result.text.lower()
    assert result.page_count is None


def test_parse_txt_latin1_fallback():
    """Latin-1 encoded content should be decoded via fallback."""
    content = "The borrower shall repay ₹10,000 with interest.".encode("latin-1", errors="replace")
    result = parse_file(content, "test_latin.txt")
    assert result.file_type == "txt"
    assert len(result.text) > 0


def test_parse_txt_filename_preserved():
    content = b"Some loan text here with enough content."
    result = parse_file(content, "my_loan_doc.txt")
    assert result.file_name == "my_loan_doc.txt"


# ---------------------------------------------------------------------------
# DOCX tests (create minimal docx in memory)
# ---------------------------------------------------------------------------

def _create_minimal_docx(paragraphs: list[str]) -> bytes:
    """Create an in-memory DOCX file with given paragraphs."""
    try:
        import docx
        from io import BytesIO
        doc = docx.Document()
        for para in paragraphs:
            doc.add_paragraph(para)
        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except ImportError:
        return b""


def test_parse_docx_extracts_paragraphs():
    paragraphs = [
        "This Loan Agreement is entered between the Lender and the Borrower.",
        "The loan amount sanctioned is Rs. 50,000.",
        "Interest rate shall be 18% per annum.",
    ]
    content = _create_minimal_docx(paragraphs)
    if not content:
        import pytest
        pytest.skip("python-docx not installed")

    result = parse_file(content, "test.docx")
    assert result.file_type == "docx"
    assert "Loan Agreement" in result.text or "loan" in result.text.lower()
    assert result.page_count is None


# ---------------------------------------------------------------------------
# Unsupported type
# ---------------------------------------------------------------------------

def test_parse_unsupported_extension_raises():
    import pytest
    with pytest.raises(ValueError, match="Unsupported file extension"):
        parse_file(b"some content", "document.xlsx")


# ---------------------------------------------------------------------------
# PDF tests (requires pdfplumber — skip if not installed)
# ---------------------------------------------------------------------------

def test_parse_pdf_skip_if_no_pdfplumber():
    """PDF parsing test is skipped if pdfplumber is not installed."""
    try:
        import pdfplumber
    except ImportError:
        import pytest
        pytest.skip("pdfplumber not installed")

    # If pdfplumber IS installed, test with a trivial case
    # (We don't have a real PDF in tests, so just verify error handling)
    import pytest
    with pytest.raises(Exception):
        parse_file(b"not a real pdf", "fake.pdf")
