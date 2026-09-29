from pathlib import Path

from fastapi.testclient import (
    TestClient,
)

from app.main import app

client = TestClient(
    app
)


def create_test_invoice() -> int:
    pdf_path = Path(
        "sample_data/test_invoice.pdf"
    )

    with pdf_path.open(
        "rb"
    ) as pdf_file:
        response = client.post(
            "/api/invoices/extract",
            files={
                "file": (
                    "test_invoice.pdf",
                    pdf_file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200

    return response.json()[
        "database_id"
    ]


def test_human_correction_updates_invoice():
    invoice_id = (
        create_test_invoice()
    )

    response = client.patch(
        f"/api/invoices/{invoice_id}",
        json={
            "changed_by": "test-reviewer",
            "supplier_name": (
                "Corrected Supplier B.V."
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["supplier_name"]
        == "Corrected Supplier B.V."
    )

    assert (
        data["invoice_data"]
        ["supplier"]
        ["name"]
        == "Corrected Supplier B.V."
    )

    history = client.get(
        f"/api/invoices/{invoice_id}/corrections"
    )

    assert history.status_code == 200

    corrections = history.json()

    assert len(
        corrections
    ) == 1

    assert (
        corrections[0][
            "field_name"
        ]
        == "supplier_name"
    )

    assert (
        corrections[0][
            "changed_by"
        ]
        == "test-reviewer"
    )

    assert (
        corrections[0][
            "source"
        ]
        == "human"
    )


def test_line_item_correction_replaces_normalized_items():
    invoice_id = (
        create_test_invoice()
    )

    response = client.patch(
        f"/api/invoices/{invoice_id}",
        json={
            "changed_by": "test-reviewer",

            "line_items": [
                {
                    "description": (
                        "Corrected service"
                    ),
                    "quantity": 2,
                    "unit_price": 100,
                    "vat_rate": 21,
                    "total": 200,
                }
            ],

            "subtotal": 200,

            "vat_amount": 42,

            "total_amount": 242,
        },
    )

    assert response.status_code == 200

    line_items_response = (
        client.get(
            f"/api/invoices/{invoice_id}/line-items"
        )
    )

    assert (
        line_items_response.status_code
        == 200
    )

    items = (
        line_items_response.json()
    )

    assert len(items) == 1

    assert (
        items[0][
            "description"
        ]
        == "Corrected service"
    )

    assert (
        float(
            items[0][
                "total"
            ]
        )
        == 200.0
    )


def test_editing_approved_invoice_returns_it_to_new():
    invoice_id = (
        create_test_invoice()
    )

    approve_response = (
        client.patch(
            f"/api/invoices/{invoice_id}/status",
            json={
                "status": "approved"
            },
        )
    )

    assert (
        approve_response.status_code
        == 200
    )

    correction_response = (
        client.patch(
            f"/api/invoices/{invoice_id}",
            json={
                "changed_by": (
                    "test-reviewer"
                ),
                "invoice_number": (
                    "CORRECTED-001"
                ),
            },
        )
    )

    assert (
        correction_response.status_code
        == 200
    )

    corrected = (
        correction_response.json()
    )

    assert (
        corrected["status"]
        == "new"
    )

    assert (
        corrected[
            "approved_at"
        ]
        is None
    )

    history_response = (
        client.get(
            f"/api/invoices/{invoice_id}/corrections"
        )
    )

    history = (
        history_response.json()
    )

    fields = {
        item["field_name"]
        for item in history
    }

    assert (
        "invoice_number"
        in fields
    )

    assert (
        "status"
        in fields
    )

    status_change = next(
        item
        for item in history
        if item[
            "field_name"
        ]
        == "status"
    )

    assert (
        status_change[
            "source"
        ]
        == "system"
    )