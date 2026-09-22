from decimal import Decimal

from pydantic import BaseModel


class CurrencyAmountSummary(
    BaseModel
):
    currency: str

    invoice_count: int

    amount: Decimal


class SupplierSpendSummary(
    BaseModel
):
    supplier_name: str

    currency: str

    invoice_count: int

    total_amount: Decimal


class MonthlyAmountSummary(
    BaseModel
):
    month: str

    currency: str

    invoice_count: int

    amount: Decimal


class AnalyticsSummary(
    BaseModel
):
    total_invoices: int

    new_invoices: int

    approved_invoices: int

    paid_invoices: int

    overdue_invoices: int

    duplicate_invoices: int

    requires_attention: int

    waiting_approval_over_7_days: int

    average_days_to_approval: (
        float | None
    )

    average_days_to_payment: (
        float | None
    )

    open_amounts: list[
        CurrencyAmountSummary
    ]

    paid_amounts: list[
        CurrencyAmountSummary
    ]

    paid_this_month: list[
        CurrencyAmountSummary
    ]

    supplier_totals: list[
        SupplierSpendSummary
    ]

    monthly_paid: list[
        MonthlyAmountSummary
    ]