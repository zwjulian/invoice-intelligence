from collections import defaultdict
from decimal import Decimal

from pydantic import BaseModel

from app.models.invoice import Invoice


class ValidationResult(BaseModel):
    valid: bool
    warnings: list[str]


MONEY_TOLERANCE = Decimal("0.02")


def differs_more_than_tolerance(
    first: Decimal,
    second: Decimal,
) -> bool:
    return abs(first - second) > MONEY_TOLERANCE


def validate_invoice(invoice: Invoice) -> ValidationResult:
    warnings: list[str] = []

    # ---------------------------------------------------------
    # 1. Date validation
    # ---------------------------------------------------------

    if (
        invoice.invoice_date is not None
        and invoice.due_date is not None
        and invoice.due_date < invoice.invoice_date
    ):
        warnings.append(
            "Due date occurs before invoice date."
        )

    # ---------------------------------------------------------
    # 2. subtotal + VAT = total
    # ---------------------------------------------------------

    if (
        invoice.subtotal is not None
        and invoice.vat_amount is not None
        and invoice.total_amount is not None
    ):
        expected_total = (
            invoice.subtotal
            + invoice.vat_amount
        )

        if differs_more_than_tolerance(
            expected_total,
            invoice.total_amount,
        ):
            warnings.append(
                "Subtotal plus VAT does not match total amount. "
                f"Expected {expected_total}, "
                f"but extracted total is {invoice.total_amount}."
            )

    # ---------------------------------------------------------
    # 3. Sum of line item totals = subtotal
    # ---------------------------------------------------------

    if (
        invoice.line_items
        and invoice.subtotal is not None
    ):
        line_totals = [
            item.total
            for item in invoice.line_items
            if item.total is not None
        ]

        if len(line_totals) == len(invoice.line_items):
            calculated_subtotal = sum(
                line_totals,
                Decimal(0),
            )

            if differs_more_than_tolerance(
                calculated_subtotal,
                invoice.subtotal,
            ):
                warnings.append(
                    "Sum of line items does not match subtotal. "
                    f"Calculated {calculated_subtotal}, "
                    f"but extracted subtotal is {invoice.subtotal}."
                )

    # ---------------------------------------------------------
    # 4. quantity × unit_price = line total
    # ---------------------------------------------------------

    for index, item in enumerate(
        invoice.line_items,
        start=1,
    ):
        if (
            item.quantity is not None
            and item.unit_price is not None
            and item.total is not None
        ):
            expected_line_total = (
                item.quantity
                * item.unit_price
            )

            if differs_more_than_tolerance(
                expected_line_total,
                item.total,
            ):
                warnings.append(
                    f"Line item {index} total does not match "
                    "quantity multiplied by unit price. "
                    f"Expected {expected_line_total}, "
                    f"but extracted total is {item.total}."
                )

    # ---------------------------------------------------------
    # 5. Sum VAT breakdown = total VAT
    # ---------------------------------------------------------

    if (
        invoice.vat_breakdown
        and invoice.vat_amount is not None
    ):
        calculated_vat_total = sum(
            (
                breakdown.vat_amount
                for breakdown in invoice.vat_breakdown
            ),
            Decimal(0),
        )

        if differs_more_than_tolerance(
            calculated_vat_total,
            invoice.vat_amount,
        ):
            warnings.append(
                "Sum of VAT breakdown does not match total VAT amount. "
                f"Calculated {calculated_vat_total}, "
                f"but extracted VAT total is {invoice.vat_amount}."
            )

    # ---------------------------------------------------------
    # 6. taxable amount × VAT rate = VAT amount
    # ---------------------------------------------------------

    for breakdown in invoice.vat_breakdown:
        if breakdown.taxable_amount is not None:
            expected_vat = (
                breakdown.taxable_amount
                * breakdown.rate
                / Decimal(100)
            )

            if differs_more_than_tolerance(
                expected_vat,
                breakdown.vat_amount,
            ):
                warnings.append(
                    f"VAT calculation for rate {breakdown.rate}% "
                    "is inconsistent. "
                    f"Expected {expected_vat}, "
                    f"but extracted VAT amount is "
                    f"{breakdown.vat_amount}."
                )

    # ---------------------------------------------------------
    # 7. Compare VAT breakdown taxable amounts with line items
    # ---------------------------------------------------------

    can_group_line_items = bool(
        invoice.line_items
    ) and all(
        item.vat_rate is not None
        and item.total is not None
        for item in invoice.line_items
    )

    if invoice.vat_breakdown and can_group_line_items:
        taxable_by_rate: dict[
            Decimal,
            Decimal,
        ] = defaultdict(
            lambda: Decimal(0)
        )

        for item in invoice.line_items:
            assert item.vat_rate is not None
            assert item.total is not None

            taxable_by_rate[item.vat_rate] += (
                item.total
            )

        breakdown_by_rate = {
            breakdown.rate: breakdown
            for breakdown in invoice.vat_breakdown
        }

        for rate, taxable_amount in (
            taxable_by_rate.items()
        ):
            breakdown = breakdown_by_rate.get(
                rate
            )

            if breakdown is None:
                warnings.append(
                    f"VAT breakdown is missing rate {rate}%."
                )
                continue

            if breakdown.taxable_amount is None:
                continue

            if differs_more_than_tolerance(
                taxable_amount,
                breakdown.taxable_amount,
            ):
                warnings.append(
                    f"VAT taxable amount for rate {rate}% "
                    "does not match line items. "
                    f"Calculated {taxable_amount}, "
                    f"but extracted taxable amount is "
                    f"{breakdown.taxable_amount}."
                )

    return ValidationResult(
        valid=len(warnings) == 0,
        warnings=warnings,
    )