from datetime import (
    UTC,
    date,
    datetime,
)
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


class StoredInvoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    extraction_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="new",
        index=True,
    )

    invoice_number: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    supplier_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    customer_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    invoice_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    due_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    currency: Mapped[
        str | None
    ] = mapped_column(
        String(10),
        nullable=True,
    )

    subtotal: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    vat_amount: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    total_amount: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    warnings: Mapped[
        list[str]
    ] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    invoice_data: Mapped[
        dict
    ] = mapped_column(
        JSON,
        nullable=False,
    )

    duplicate_of_id: Mapped[
        int | None
    ] = mapped_column(
        ForeignKey(
            "invoices.id"
        ),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=lambda: datetime.now(
            UTC
        ),
    )

    status_updated_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
        default=lambda: datetime.now(
            UTC
        ),
    )

    approved_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    paid_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    line_items: Mapped[
        list["StoredInvoiceLineItem"]
    ] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class StoredInvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey(
            "invoices.id"
        ),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    quantity: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=14,
            scale=4,
        ),
        nullable=True,
    )

    unit_price: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    vat_rate: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=8,
            scale=4,
        ),
        nullable=True,
    )

    total: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    invoice: Mapped[
        "StoredInvoice"
    ] = relationship(
        back_populates="line_items",
    )