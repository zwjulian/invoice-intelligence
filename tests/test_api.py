from pathlib import Path
from tempfile import NamedTemporaryFile

import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(
    app
)


def test_health_endpoint():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_extract_invoice_success():
    pdf_path = Path(
        "sample_data/test_invoice.pdf"
    )

    with pdf_path.open(
        "rb"
    ) as pdf_file:
        response = client.post(
            "/invoices/extract",
            files={
                "file": (
                    "test_invoice.pdf",
                    pdf_file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is True
    assert data["warnings"] == []

    assert (
        data["filename"]
        == "test_invoice.pdf"
    )

    assert (
        data["extraction_method"]
        == "text"
    )

    assert (
        data["invoice"]["invoice_number"]
        == "INV-2026-0042"
    )


def test_scanned_pdf_uses_vision_fallback():
    document = pymupdf.open()

    page = document.new_page(
        width=595,
        height=842,
    )

    pixmap = pymupdf.Pixmap(
        pymupdf.csRGB,
        pymupdf.IRect(
            0,
            0,
            595,
            842,
        ),
        False,
    )

    page.insert_image(
        page.rect,
        pixmap=pixmap,
    )

    with NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as temp_file:
        temp_path = Path(
            temp_file.name
        )

    document.save(
        temp_path
    )
    document.close()

    try:
        with temp_path.open(
            "rb"
        ) as pdf_file:
            response = client.post(
                "/invoices/extract",
                files={
                    "file": (
                        "scan.pdf",
                        pdf_file,
                        "application/pdf",
                    )
                },
            )

        assert (
            response.status_code
            == 200
        )

        data = response.json()

        assert (
            data["extraction_method"]
            == "vision"
        )

        assert (
            data["valid"]
            is True
        )

    finally:
        temp_path.unlink(
            missing_ok=True
        )


def test_reject_non_pdf_file():
    response = client.post(
        "/invoices/extract",
        files={
            "file": (
                "test.txt",
                b"this is not a pdf",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "Only PDF files are supported."
    )