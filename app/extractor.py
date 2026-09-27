"""
extractor.py
------------
Reads a .pdf, .docx or .txt file from disk and returns its plain text.
Every failure mode (unsupported type, empty/scanned document, bad encoding)
is turned into a clear ExtractionError instead of crashing the app.
"""

import os
import pdfplumber
from docx import Document


class ExtractionError(Exception):
    """Raised when text cannot be reliably pulled out of a document."""
    pass


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if not os.path.exists(file_path):
        raise ExtractionError(f"File not found: {file_path}")

    try:
        if ext == ".pdf":
            return _extract_pdf(file_path)
        elif ext == ".docx":
            return _extract_docx(file_path)
        elif ext == ".txt":
            return _extract_txt(file_path)
        else:
            raise ExtractionError(
                f"Unsupported file type '{ext}'. Only .pdf, .docx and .txt are supported."
            )
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Failed to read '{os.path.basename(file_path)}': {e}")


def _extract_pdf(file_path: str) -> str:
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ExtractionError(f"Could not open PDF: {e}")

    text = "\n".join(text_parts).strip()
    if not text:
        raise ExtractionError(
            "No extractable text found in this PDF. It may be a scanned/image-only "
            "PDF, which this system does not OCR."
        )
    return text


def _extract_docx(file_path: str) -> str:
    try:
        doc = Document(file_path)
    except Exception as e:
        raise ExtractionError(f"Could not open DOCX: {e}")

    text_parts = [p.text for p in doc.paragraphs if p.text.strip()]

    # Tables often carry meaningful content too (e.g. spec sheets)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text_parts.append(cell.text)

    text = "\n".join(text_parts).strip()
    if not text:
        raise ExtractionError("No extractable text found in this DOCX file.")
    return text


def _extract_txt(file_path: str) -> str:
    encodings = ["utf-8", "utf-16", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                text = f.read().strip()
            if text:
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            raise ExtractionError(f"Could not read TXT file: {e}")

    raise ExtractionError(
        "Could not decode this TXT file with common encodings (utf-8/utf-16/latin-1)."
    )
