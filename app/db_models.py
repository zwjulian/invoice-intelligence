from datetime import (
    date,
    datetime,
    timezone,
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
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
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

    extraction_method: Mapped[str] = (
        mapped_column(
            String(20),
            nullable=False,
        )
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

    warnings: Mapped[list[str]] = (
        mapped_column(
            JSON,
            nullable=False,
            default=list,
        )
    )

    invoice_data: Mapped[dict] = (
        mapped_column(
            JSON,
            nullable=False,
        )
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
            timezone.utc
        ),
    )