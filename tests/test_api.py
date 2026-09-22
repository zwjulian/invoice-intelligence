from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_extract_invoice_success():
    pdf_path = Path("sample_data/test_invoice.pdf")

    with pdf_path.open("rb") as pdf_file:
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
    assert data["filename"] == "test_invoice.pdf"

    assert (
        data["invoice"]["invoice_number"]
        == "INV-2026-0042"
    )

    assert (
        data["invoice"]["supplier"]["name"]
        == "NorthStar Software B.V."
    )

    assert (
        data["invoice"]["customer"]["name"]
        == "Data Example B.V."
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

    assert data["detail"] == "Only PDF files are supported."