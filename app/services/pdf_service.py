from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be inspected, read or rendered."""


def _validate_pdf_path(
    pdf_path: str | Path,
) -> Path:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"PDF path is not a file: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    return path


def get_pdf_page_count(
    pdf_path: str | Path,
) -> int:
    path = _validate_pdf_path(
        pdf_path
    )

    try:
        with pymupdf.open(path) as document:
            return document.page_count

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to inspect PDF: {exc}"
        ) from exc


def extract_text_from_pdf(
    pdf_path: str | Path,
) -> str:
    path = _validate_pdf_path(
        pdf_path
    )

    pages: list[str] = []

    try:
        with pymupdf.open(path) as document:
            if document.page_count == 0:
                raise PDFExtractionError(
                    "PDF contains no pages."
                )

            for page_number, page in enumerate(
                document,
                start=1,
            ):
                text = page.get_text(
                    "text",
                    sort=True,
                ).strip()

                if not text:
                    continue

                pages.append(
                    
                        f"--- PAGE {page_number} ---\n"
                        f"{text}"
                    
                )

    except PDFExtractionError:
        raise

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to read PDF: {exc}"
        ) from exc

    return "\n\n".join(
        pages
    )


def has_extractable_text(
    pdf_path: str | Path,
) -> bool:
    """
    Return True when PyMuPDF can extract at least some text.

    Note that the document router performs a stricter check and
    requires a minimum number of meaningful characters before
    choosing text-based LLM extraction.
    """

    text = extract_text_from_pdf(
        pdf_path
    )

    return bool(
        text.strip()
    )


def render_pdf_pages_as_png(
    pdf_path: str | Path,
    dpi: int = 150,
) -> list[bytes]:
    path = _validate_pdf_path(
        pdf_path
    )

    rendered_pages: list[bytes] = []

    try:
        with pymupdf.open(path) as document:
            if document.page_count == 0:
                raise PDFExtractionError(
                    "PDF contains no pages."
                )

            for page in document:
                pixmap = page.get_pixmap(
                    dpi=dpi,
                    alpha=False,
                )

                rendered_pages.append(
                    pixmap.tobytes("png")
                )

    except PDFExtractionError:
        raise

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to render PDF pages: {exc}"
        ) from exc

    return rendered_pages