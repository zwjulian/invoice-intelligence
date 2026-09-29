from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now_naive() -> datetime:
    """
    Return the current UTC time without timezone information.

    The existing PostgreSQL schema uses TIMESTAMP rather than
    TIMESTAMP WITH TIME ZONE, so we store a naive UTC datetime.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class InvoiceRecord(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
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
    )

    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    subtotal: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    vat_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    total_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    warnings: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    invoice_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now_naive,
    )

    status_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    line_items: Mapped[list["LineItemRecord"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class LineItemRecord(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    vat_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    total: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    invoice: Mapped["InvoiceRecord"] = relationship(
        back_populates="line_items",
    )