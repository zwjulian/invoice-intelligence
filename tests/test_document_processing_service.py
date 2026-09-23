from typing import cast

import pymupdf
import pytest

from app.models.invoice import Invoice
from app.services.document_processing_service import (
    InvalidDocumentError,
    process_invoice_pdf,
)


class DummyExtractor:
    def __init__(self) -> None:
        self.text_called = False
        self.vision_called = False

    def extract(
        self,
        invoice_text: str,
    ) -> Invoice:
        self.text_called = True

        return cast(
            Invoice,
            object(),
        )

    def extract_from_images(
        self,
        page_images: list[bytes],
    ) -> Invoice:
        self.vision_called = True

        assert len(page_images) > 0

        return cast(
            Invoice,
            object(),
        )


def create_pdf_with_text(
    text: str,
) -> bytes:
    document = pymupdf.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        text,
    )

    pdf_bytes = document.tobytes()

    document.close()

    return pdf_bytes


def test_digital_pdf_uses_text_extraction():
    extractor = DummyExtractor()

    pdf_bytes = create_pdf_with_text(
        
            "INVOICE INV-2026-001 "
            "NorthStar Software BV "
            "Invoice date 2026-09-23 "
            "Subtotal EUR 100.00 "
            "VAT EUR 21.00 "
            "Total EUR 121.00 "
            "Payment due within 30 days."
        
    )

    result = process_invoice_pdf(
        pdf_bytes=pdf_bytes,
        extractor=extractor,
    )

    assert (
        result.extraction_method
        == "text"
    )

    assert extractor.text_called
    assert not extractor.vision_called

    assert (
        result.extracted_text_characters
        >= 80
    )

    assert result.page_count == 1


def test_pdf_with_tiny_text_uses_vision():
    extractor = DummyExtractor()

    pdf_bytes = create_pdf_with_text(
        "Page 1"
    )

    result = process_invoice_pdf(
        pdf_bytes=pdf_bytes,
        extractor=extractor,
    )

    assert (
        result.extraction_method
        == "vision"
    )

    assert not extractor.text_called
    assert extractor.vision_called

    assert (
        result.extracted_text_characters
        < 80
    )

    assert result.page_count == 1


def test_empty_upload_is_rejected():
    extractor = DummyExtractor()

    with pytest.raises(
        InvalidDocumentError,
        match="Uploaded PDF is empty",
    ):
        process_invoice_pdf(
            pdf_bytes=b"",
            extractor=extractor,
        )


def test_fake_pdf_is_rejected():
    extractor = DummyExtractor()

    with pytest.raises(
        InvalidDocumentError,
        match=(
            "does not appear to be "
            "a valid PDF"
        ),
    ):
        process_invoice_pdf(
            pdf_bytes=(
                b"This is not a real PDF."
            ),
            extractor=extractor,
        )