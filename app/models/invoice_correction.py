from datetime import (
    date,
    datetime,
)
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.invoice import (
    LineItem,
)


class InvoiceCorrectionRequest(
    BaseModel
):
    changed_by: str = Field(
        default="manual-review",
        min_length=1,
        max_length=100,
    )

    invoice_number: str | None = None

    invoice_date: date | None = None

    due_date: date | None = None

    supplier_name: str | None = None

    supplier_address: str | None = None

    supplier_vat_number: str | None = None

    customer_name: str | None = None

    customer_address: str | None = None

    customer_vat_number: str | None = None

    currency: str | None = None

    subtotal: Decimal | None = None

    vat_amount: Decimal | None = None

    total_amount: Decimal | None = None

    line_items: (
        list[LineItem]
        | None
    ) = None


class InvoiceCorrectionResponse(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    invoice_id: int

    field_name: str

    old_value: object | None

    new_value: object | None

    changed_by: str

    source: str

    changed_at: datetime