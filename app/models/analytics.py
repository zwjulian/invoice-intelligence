from decimal import Decimal

from pydantic import BaseModel


class CurrencyAmountSummary(BaseModel):
    currency: str
    invoice_count: int
    amount: Decimal


class SupplierSpendSummary(BaseModel):
    supplier_name: str
    currency: str
    invoice_count: int
    total_amount: Decimal


class AnalyticsSummary(BaseModel):
    total_invoices: int
    new_invoices: int
    approved_invoices: int
    paid_invoices: int

    overdue_invoices: int
    duplicate_invoices: int
    requires_attention: int

    open_amounts: list[CurrencyAmountSummary]
    paid_amounts: list[CurrencyAmountSummary]

    supplier_totals: list[SupplierSpendSummary]