from decimal import Decimal

from pydantic import BaseModel

from app.models.invoice import Invoice


class ValidationResult(BaseModel):
    valid: bool
    warnings: list[str]


MONEY_TOLERANCE = Decimal("0.02")


def validate_invoice(invoice: Invoice) -> ValidationResult:
    warnings: list[str] = []

    # 1. Due date mag niet vóór invoice date liggen
    if (
        invoice.invoice_date is not None
        and invoice.due_date is not None
        and invoice.due_date < invoice.invoice_date
    ):
        warnings.append(
            "Due date occurs before invoice date."
        )

    # 2. subtotal + VAT moet gelijk zijn aan total
    if (
        invoice.subtotal is not None
        and invoice.vat_amount is not None
        and invoice.total_amount is not None
    ):
        expected_total = invoice.subtotal + invoice.vat_amount

        difference = abs(
            expected_total - invoice.total_amount
        )

        if difference > MONEY_TOLERANCE:
            warnings.append(
                "Subtotal plus VAT does not match total amount. "
                f"Expected {expected_total}, "
                f"but extracted total is {invoice.total_amount}."
            )

    # 3. Som van alle line items moet gelijk zijn aan subtotal
    if invoice.line_items and invoice.subtotal is not None:
        line_totals = [
            item.total
            for item in invoice.line_items
            if item.total is not None
        ]

        # Alleen controleren als ieder line item een total heeft
        if len(line_totals) == len(invoice.line_items):
            calculated_subtotal = sum(
                line_totals,
                Decimal("0")
            )

            difference = abs(
                calculated_subtotal - invoice.subtotal
            )

            if difference > MONEY_TOLERANCE:
                warnings.append(
                    "Sum of line items does not match subtotal. "
                    f"Calculated {calculated_subtotal}, "
                    f"but extracted subtotal is {invoice.subtotal}."
                )

    return ValidationResult(
        valid=len(warnings) == 0,
        warnings=warnings,
    )