from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from pypdf import PdfReader

from core.config import Settings
from database.db import save_document
from core.gemini import GeminiService

CHUNK_SIZE = 1100
CHUNK_OVERLAP = 160
EMBEDDING_BATCH_SIZE = 32


class PDFProcessingError(ValueError):
    """A user-correctable PDF validation or extraction error."""


@dataclass(frozen=True)
class PageChunk:
    page_number: int
    text: str


def extract_pdf_pages(pdf_bytes: bytes, max_pdf_bytes: int) -> list[tuple[int, str]]:
    if not pdf_bytes:
        raise PDFProcessingError("The PDF is empty.")
    if len(pdf_bytes) > max_pdf_bytes:
        limit_mb = max_pdf_bytes // (1024 * 1024)
        raise PDFProcessingError(f"This file is too large. The maximum PDF size is {limit_mb} MB.")
    if b"%PDF-" not in pdf_bytes[:1024]:
        raise PDFProcessingError("This file does not look like a PDF. Choose a valid .pdf file.")
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
        if reader.is_encrypted:
            raise PDFProcessingError("This PDF is password-protected. Upload an unlocked copy.")
        pages = [(number, (page.extract_text() or "").strip()) for number, page in enumerate(reader.pages, start=1)]
    except PDFProcessingError:
        raise
    except Exception as exc:
        raise PDFProcessingError("The PDF could not be read. It may be damaged or use unsupported encryption.") from exc
    if not any(text for _, text in pages):
        raise PDFProcessingError(
            "No selectable text was found in this PDF. Scanned-image PDFs need OCR before uploading."
        )
    return pages


def chunk_pages(pages: list[tuple[int, str]]) -> list[PageChunk]:
    chunks: list[PageChunk] = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for page_number, text in pages:
        for start in range(0, len(text), step):
            chunk = text[start : start + CHUNK_SIZE].strip()
            if chunk:
                chunks.append(PageChunk(page_number=page_number, text=chunk))
    return chunks


def index_pdf(
    filename: str,
    pdf_bytes: bytes,
    settings: Settings,
    ai: GeminiService,
) -> int:
    pages = extract_pdf_pages(pdf_bytes, settings.max_pdf_bytes)
    chunks = chunk_pages(pages)
    vectors: list[list[float]] = []
    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[start : start + EMBEDDING_BATCH_SIZE]
        vectors.extend(ai.embed_texts([chunk.text for chunk in batch]))
    if len(vectors) != len(chunks):
        raise PDFProcessingError("Not every page of this PDF could be indexed. Please try again.")
    safe_filename = filename.replace("\\", "/").split("/")[-1].strip()
    if not safe_filename.lower().endswith(".pdf"):
        safe_filename = f"{safe_filename}.pdf"
    return save_document(
        settings.database_path,
        name=safe_filename,
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        page_count=max(page_number for page_number, _ in pages),
        chunks=[(chunk.page_number, chunk.text, vector) for chunk, vector in zip(chunks, vectors, strict=True)],
    )
