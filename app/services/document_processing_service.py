from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, Protocol

from app.core.document_config import document_settings
from app.models.invoice import Invoice
from app.services.pdf_service import (
    extract_text_from_pdf,
    get_pdf_page_count,
    render_pdf_pages_as_png,
)


class InvoiceExtractor(Protocol):
    """
    Interface required by the document-processing pipeline.

    Both the real Gemini extractor and the mock extractor can
    implement this interface.
    """

    def extract(
        self,
        invoice_text: str,
    ) -> Invoice:
        ...

    def extract_from_images(
        self,
        page_images: list[bytes],
    ) -> Invoice:
        ...


class InvalidDocumentError(Exception):
    """Raised when an uploaded document is invalid."""


class DocumentTooLargeError(Exception):
    """Raised when an uploaded document exceeds the size limit."""


class DocumentTooManyPagesError(Exception):
    """Raised when a PDF contains too many pages."""


@dataclass(frozen=True)
class DocumentProcessingResult:
    invoice: Invoice

    extraction_method: Literal[
        "text",
        "vision",
    ]

    extracted_text_characters: int

    page_count: int


def _validate_pdf_bytes(
    pdf_bytes: bytes,
) -> None:
    if not pdf_bytes:
        raise InvalidDocumentError(
            "Uploaded PDF is empty."
        )

    max_size_bytes = (
        document_settings.max_upload_size_mb
        * 1024
        * 1024
    )

    if len(pdf_bytes) > max_size_bytes:
        raise DocumentTooLargeError(
            
                "Uploaded PDF exceeds the maximum "
                f"size of "
                f"{document_settings.max_upload_size_mb} MB."
            
        )

    # A valid PDF should contain the %PDF- signature very close
    # to the start of the file. Checking the first 1024 bytes is
    # slightly more tolerant than requiring byte zero.
    if b"%PDF-" not in pdf_bytes[:1024]:
        raise InvalidDocumentError(
            
                "Uploaded file does not appear "
                "to be a valid PDF document."
            
        )


def _meaningful_character_count(
    text: str,
) -> int:
    """
    Count non-whitespace characters.

    This prevents a PDF containing only whitespace or a tiny
    amount of metadata text from incorrectly taking the text
    extraction route.
    """

    return sum(
        1
        for character in text
        if not character.isspace()
    )


def process_invoice_pdf(
    *,
    pdf_bytes: bytes,
    extractor: InvoiceExtractor,
) -> DocumentProcessingResult:
    """
    Process an invoice PDF.

    Digital PDFs with sufficient embedded text use text-based
    extraction. PDFs with little or no useful text are rendered
    as images and processed using the vision extraction path.
    """

    _validate_pdf_bytes(
        pdf_bytes
    )

    temp_path: Path | None = None

    try:
        with NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            temp_file.write(
                pdf_bytes
            )

            temp_path = Path(
                temp_file.name
            )

        page_count = get_pdf_page_count(
            temp_path
        )

        if page_count <= 0:
            raise InvalidDocumentError(
                "PDF contains no pages."
            )

        if (
            page_count
            > document_settings.max_pdf_pages
        ):
            raise DocumentTooManyPagesError(
                
                    f"PDF contains {page_count} pages, "
                    "while the maximum supported number "
                    f"is {document_settings.max_pdf_pages}."
                
            )

        invoice_text = extract_text_from_pdf(
            temp_path
        )

        text_character_count = (
            _meaningful_character_count(
                invoice_text
            )
        )

        if (
            text_character_count
            >= document_settings.min_text_characters
        ):
            invoice = extractor.extract(
                invoice_text
            )

            return DocumentProcessingResult(
                invoice=invoice,
                extraction_method="text",
                extracted_text_characters=(
                    text_character_count
                ),
                page_count=page_count,
            )

        page_images = render_pdf_pages_as_png(
            temp_path,
            dpi=document_settings.vision_render_dpi,
        )

        invoice = extractor.extract_from_images(
            page_images
        )

        return DocumentProcessingResult(
            invoice=invoice,
            extraction_method="vision",
            extracted_text_characters=(
                text_character_count
            ),
            page_count=page_count,
        )

    finally:
        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )