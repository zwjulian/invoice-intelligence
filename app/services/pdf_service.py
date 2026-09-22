from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from a PDF."""


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    pages: list[str] = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True).strip()

            if text:
                pages.append(
                    f"--- PAGE {page_number} ---\n{text}"
                )

    full_text = "\n\n".join(pages)

    if not full_text.strip():
        raise PDFExtractionError(
            "No text could be extracted from the PDF. "
            "The document may be scanned and require OCR."
        )

    return full_text