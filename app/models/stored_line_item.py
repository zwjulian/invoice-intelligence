from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
)


class StoredLineItem(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    invoice_id: int

    description: str

    quantity: Decimal | None

    unit_price: Decimal | None

    vat_rate: Decimal | None

    total: Decimal | None