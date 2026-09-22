from datetime import date
from decimal import Decimal

from app.models.invoice import (
    Invoice,
    LineItem,
    Party,
    VATBreakdown,
)


class MockInvoiceExtractor:
    """
    Deterministic extractor used for development
    and automated tests.
    """

    def _build_invoice(self) -> Invoice:
        return Invoice(
            invoice_number="INV-2026-0042",
            invoice_date=date(
                2026,
                9,
                15,
            ),
            due_date=date(
                2026,
                10,
                15,
            ),

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
                    taxable_amount=Decimal(
                        "1990.00"
                    ),
                    vat_amount=Decimal(
                        "417.90"
                    ),
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
                    unit_price=Decimal(
                        "450.00"
                    ),
                    vat_rate=Decimal(21),
                    total=Decimal(
                        "900.00"
                    ),
                ),
                LineItem(
                    description=(
                        "Document extraction prototype"
                    ),
                    quantity=Decimal(8),
                    unit_price=Decimal(
                        "95.00"
                    ),
                    vat_rate=Decimal(21),
                    total=Decimal(
                        "760.00"
                    ),
                ),
                LineItem(
                    description=(
                        "Cloud deployment support"
                    ),
                    quantity=Decimal(3),
                    unit_price=Decimal(
                        "110.00"
                    ),
                    vat_rate=Decimal(21),
                    total=Decimal(
                        "330.00"
                    ),
                ),
            ],
        )

    def extract(
        self,
        invoice_text: str,
    ) -> Invoice:
        return self._build_invoice()

    def extract_from_images(
        self,
        page_images: list[bytes],
    ) -> Invoice:
        return self._build_invoice()