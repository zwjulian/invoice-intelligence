from datetime import date
from decimal import Decimal

from app.models.invoice import Invoice, LineItem, Party
from app.services.validation_service import validate_invoice


def create_valid_invoice() -> Invoice:
    return Invoice(
        invoice_number="INV-2026-0042",
        invoice_date=date(2026, 9, 15),
        due_date=date(2026, 10, 15),
        supplier=Party(
            name="NorthStar Software B.V.",
            address="Zernikepark 12, 9747 AN Groningen, Netherlands",
            vat_number="NL865432109B01",
        ),
        customer=Party(
            name="Data Example B.V.",
            address="Helperpark 100, 9723 ZA Groningen, Netherlands",
            vat_number="NL123456789B01",
        ),
        currency="EUR",
        subtotal=Decimal("1990.00"),
        vat_amount=Decimal("417.90"),
        total_amount=Decimal("2407.90"),
        line_items=[
            LineItem(
                description="AI consultancy - architecture workshop",
                quantity=Decimal("2"),
                unit_price=Decimal("450.00"),
                vat_rate=Decimal("21"),
                total=Decimal("900.00"),
            ),
            LineItem(
                description="Document extraction prototype",
                quantity=Decimal("8"),
                unit_price=Decimal("95.00"),
                vat_rate=Decimal("21"),
                total=Decimal("760.00"),
            ),
            LineItem(
                description="Cloud deployment support",
                quantity=Decimal("3"),
                unit_price=Decimal("110.00"),
                vat_rate=Decimal("21"),
                total=Decimal("330.00"),
            ),
        ],
    )


def test_valid_invoice():
    invoice = create_valid_invoice()

    result = validate_invoice(invoice)

    assert result.valid is True
    assert result.warnings == []


def test_wrong_total_is_detected():
    invoice = create_valid_invoice()

    invoice.total_amount = Decimal("2500.00")

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "Subtotal plus VAT does not match total amount"
        in warning
        for warning in result.warnings
    )


def test_wrong_subtotal_is_detected():
    invoice = create_valid_invoice()

    invoice.subtotal = Decimal("2000.00")

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "Sum of line items does not match subtotal"
        in warning
        for warning in result.warnings
    )


def test_due_date_before_invoice_date_is_detected():
    invoice = create_valid_invoice()

    invoice.due_date = date(2026, 9, 1)

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "Due date occurs before invoice date"
        in warning
        for warning in result.warnings
    )


def test_small_rounding_difference_is_allowed():
    invoice = create_valid_invoice()

    invoice.total_amount = Decimal("2407.91")

    result = validate_invoice(invoice)

    assert result.valid is True