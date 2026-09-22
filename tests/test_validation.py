from datetime import date
from decimal import Decimal

from app.models.invoice import (
    Invoice,
    LineItem,
    Party,
    VATBreakdown,
)
from app.services.validation_service import (
    validate_invoice,
)


def create_valid_invoice() -> Invoice:
    return Invoice(
        invoice_number="INV-2026-0042",
        invoice_date=date(2026, 9, 15),
        due_date=date(2026, 10, 15),

        supplier=Party(
            name="NorthStar Software B.V.",
            address=(
                "Zernikepark 12, "
                "9747 AN Groningen, Netherlands"
            ),
            vat_number="NL865432109B01",
        ),

        customer=Party(
            name="Data Example B.V.",
            address=(
                "Helperpark 100, "
                "9723 ZA Groningen, Netherlands"
            ),
            vat_number="NL123456789B01",
        ),

        currency="EUR",

        subtotal=Decimal("1990.00"),
        vat_amount=Decimal("417.90"),

        vat_breakdown=[
            VATBreakdown(
                rate=Decimal(21),
                taxable_amount=Decimal("1990.00"),
                vat_amount=Decimal("417.90"),
            )
        ],

        total_amount=Decimal("2407.90"),

        line_items=[
            LineItem(
                description=(
                    "AI consultancy - "
                    "architecture workshop"
                ),
                quantity=Decimal(2),
                unit_price=Decimal("450.00"),
                vat_rate=Decimal(21),
                total=Decimal("900.00"),
            ),
            LineItem(
                description=(
                    "Document extraction prototype"
                ),
                quantity=Decimal(8),
                unit_price=Decimal("95.00"),
                vat_rate=Decimal(21),
                total=Decimal("760.00"),
            ),
            LineItem(
                description="Cloud deployment support",
                quantity=Decimal(3),
                unit_price=Decimal("110.00"),
                vat_rate=Decimal(21),
                total=Decimal("330.00"),
            ),
        ],
    )


def create_mixed_vat_invoice() -> Invoice:
    return Invoice(
        invoice_number="MIXED-VAT-001",
        invoice_date=date(2026, 9, 20),
        due_date=date(2026, 10, 20),

        supplier=Party(
            name="Mixed VAT Example B.V.",
            vat_number="NL999999999B01",
        ),

        customer=Party(
            name="Example Customer B.V.",
            vat_number="NL888888888B01",
        ),

        currency="EUR",

        subtotal=Decimal("350.00"),
        vat_amount=Decimal("49.50"),

        vat_breakdown=[
            VATBreakdown(
                rate=Decimal(21),
                taxable_amount=Decimal("150.00"),
                vat_amount=Decimal("31.50"),
            ),
            VATBreakdown(
                rate=Decimal(9),
                taxable_amount=Decimal("200.00"),
                vat_amount=Decimal("18.00"),
            ),
        ],

        total_amount=Decimal("399.50"),

        line_items=[
            LineItem(
                description="Software service",
                quantity=Decimal(1),
                unit_price=Decimal("100.00"),
                vat_rate=Decimal(21),
                total=Decimal("100.00"),
            ),
            LineItem(
                description="Printed publication",
                quantity=Decimal(2),
                unit_price=Decimal("100.00"),
                vat_rate=Decimal(9),
                total=Decimal("200.00"),
            ),
            LineItem(
                description="Technical support",
                quantity=Decimal(1),
                unit_price=Decimal("50.00"),
                vat_rate=Decimal(21),
                total=Decimal("50.00"),
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


def test_wrong_line_item_total_is_detected():
    invoice = create_valid_invoice()

    invoice.line_items[0].total = Decimal(
        "950.00"
    )

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "quantity multiplied by unit price"
        in warning
        for warning in result.warnings
    )


def test_mixed_vat_invoice_is_valid():
    invoice = create_mixed_vat_invoice()

    result = validate_invoice(invoice)

    assert result.valid is True
    assert result.warnings == []


def test_wrong_vat_breakdown_total_is_detected():
    invoice = create_mixed_vat_invoice()

    invoice.vat_breakdown[0].vat_amount = (
        Decimal("35.00")
    )

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "Sum of VAT breakdown does not match"
        in warning
        for warning in result.warnings
    )


def test_wrong_vat_calculation_is_detected():
    invoice = create_mixed_vat_invoice()

    invoice.vat_breakdown[1].vat_amount = (
        Decimal("20.00")
    )

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "VAT calculation for rate 9%"
        in warning
        for warning in result.warnings
    )


def test_vat_taxable_amount_mismatch_is_detected():
    invoice = create_mixed_vat_invoice()

    invoice.vat_breakdown[0].taxable_amount = (
        Decimal("160.00")
    )

    result = validate_invoice(invoice)

    assert result.valid is False

    assert any(
        "does not match line items"
        in warning
        for warning in result.warnings
    )