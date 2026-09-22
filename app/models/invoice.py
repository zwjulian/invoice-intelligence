from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class Party(BaseModel):
    name: str | None = Field(
        default=None,
        description="Name of the company or person."
    )

    address: str | None = Field(
        default=None,
        description="Full postal address if available."
    )

    vat_number: str | None = Field(
        default=None,
        description="VAT identification number if present."
    )


class LineItem(BaseModel):
    description: str = Field(
        description="Description of the billed product or service."
    )

    quantity: Decimal | None = Field(
        default=None,
        description="Quantity purchased."
    )

    unit_price: Decimal | None = Field(
        default=None,
        description="Price per unit excluding VAT if available."
    )

    vat_rate: Decimal | None = Field(
        default=None,
        description="VAT percentage, for example 21 for 21 percent VAT."
    )

    total: Decimal | None = Field(
        default=None,
        description="Total amount for this line excluding VAT if available."
    )


class Invoice(BaseModel):
    invoice_number: str | None = Field(
        default=None,
        description="Unique invoice number."
    )

    invoice_date: date | None = Field(
        default=None,
        description="Date the invoice was issued."
    )

    due_date: date | None = Field(
        default=None,
        description="Payment due date."
    )

    supplier: Party = Field(
        description="Party sending the invoice."
    )

    customer: Party | None = Field(
        default=None,
        description="Party receiving the invoice."
    )

    currency: str | None = Field(
        default=None,
        description="ISO currency code such as EUR, USD or GBP."
    )

    subtotal: Decimal | None = Field(
        default=None,
        description="Total amount excluding VAT."
    )

    vat_amount: Decimal | None = Field(
        default=None,
        description="Total VAT amount."
    )

    total_amount: Decimal | None = Field(
        default=None,
        description="Final invoice amount including VAT."
    )

    line_items: list[LineItem] = Field(
        default_factory=list,
        description="Individual products or services on the invoice."
    )