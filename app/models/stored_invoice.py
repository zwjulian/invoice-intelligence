from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)

InvoiceStatus = Literal[
    "new",
    "approved",
    "paid",
]


class InvoiceStatusUpdate(
    BaseModel
):
    status: InvoiceStatus


class StoredInvoiceSummary(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    filename: str

    invoice_number: str | None

    supplier_name: str | None

    customer_name: str | None

    invoice_date: date | None

    due_date: date | None

    currency: str | None

    total_amount: Decimal | None

    valid: bool

    status: str

    extraction_method: str

    duplicate_of_id: int | None

    created_at: datetime

    status_updated_at: (
        datetime | None
    )

    approved_at: datetime | None

    paid_at: datetime | None


class StoredInvoiceDetail(
    StoredInvoiceSummary
):
    subtotal: Decimal | None

    vat_amount: Decimal | None

    warnings: list[str]

    invoice_data: dict