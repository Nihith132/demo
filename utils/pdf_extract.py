from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pypdf import PdfReader


@dataclass
class PdfExtractionResult:
    extracted_text: str
    pages_processed: int
    ocr_required: bool
    notes: List[str]


def extract_text_from_pdf(pdf_path: str, max_pages: int | None = None) -> PdfExtractionResult:
    """Extract text from a PDF via PyPDF.

    MVP behavior:
    - Extract the entire PDF (no page limit).
    - If extraction yields little/no text, flag `ocr_required=True` for later.

    OCR is intentionally not performed here (post-MVP callback).
    """

    notes: List[str] = []
    reader = PdfReader(pdf_path)

    pages = reader.pages if max_pages is None else reader.pages[:max_pages]

    extracted_chunks: List[str] = []
    pages_processed = 0

    for i, page in enumerate(pages):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            text = ""
            notes.append(f"page_{i}_extract_failed: {e}")

        extracted_chunks.append(text)
        pages_processed += 1

    extracted_text = "\n\n".join([c.strip() for c in extracted_chunks if c is not None]).strip()

    # Heuristic: if almost nothing extracted, likely scanned PDF.
    ocr_required = len(extracted_text) < 200
    if ocr_required:
        notes.append("low_text_extracted_flag_ocr")

    return PdfExtractionResult(
        extracted_text=extracted_text,
        pages_processed=pages_processed,
        ocr_required=ocr_required,
        notes=notes,
    )
