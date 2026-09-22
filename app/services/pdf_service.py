from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be processed."""


def extract_text_from_pdf(
    pdf_path: str | Path,
) -> str:
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    pages: list[str] = []

    try:
        with pymupdf.open(pdf_path) as document:
            for page_number, page in enumerate(
                document,
                start=1,
            ):
                text = page.get_text(
                    "text",
                    sort=True,
                ).strip()

                if text:
                    pages.append(
                        f"--- PAGE {page_number} ---\n"
                        f"{text}"
                    )

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to read PDF: {exc}"
        ) from exc

    return "\n\n".join(pages)


def has_extractable_text(
    pdf_path: str | Path,
) -> bool:
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
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    rendered_pages: list[bytes] = []

    try:
        with pymupdf.open(pdf_path) as document:
            for page in document:
                pixmap = page.get_pixmap(
                    dpi=dpi,
                    alpha=False,
                )

                png_bytes = pixmap.tobytes(
                    "png"
                )

                rendered_pages.append(
                    png_bytes
                )

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to render PDF pages: {exc}"
        ) from exc

    if not rendered_pages:
        raise PDFExtractionError(
            "PDF contains no pages."
        )

    return rendered_pages