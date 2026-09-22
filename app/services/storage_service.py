from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    and_,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.db_models import StoredInvoice
from app.models.analytics import (
    AnalyticsSummary,
    CurrencyAmountSummary,
    SupplierSpendSummary,
)
from app.models.invoice import Invoice
from app.services.validation_service import (
    ValidationResult,
)


def find_duplicate(
    session: Session,
    invoice: Invoice,
) -> StoredInvoice | None:
    if not invoice.invoice_number:
        return None

    if not invoice.supplier.name:
        return None

    invoice_number = (
        invoice.invoice_number.strip()
    )

    supplier_name = (
        invoice.supplier.name
        .strip()
        .lower()
    )

    statement = (
        select(
            StoredInvoice
        )
        .where(
            func.lower(
                StoredInvoice.supplier_name
            )
            == supplier_name,
            StoredInvoice.invoice_number
            == invoice_number,
        )
        .order_by(
            StoredInvoice.id
        )
        .limit(1)
    )

    return session.scalar(
        statement
    )


def store_invoice(
    filename: str,
    extraction_method: str,
    invoice: Invoice,
    validation: ValidationResult,
) -> StoredInvoice:
    with SessionLocal() as session:
        duplicate = find_duplicate(
            session,
            invoice,
        )

        stored_invoice = StoredInvoice(
            filename=filename,
            extraction_method=(
                extraction_method
            ),
            status="new",
            invoice_number=(
                invoice.invoice_number
            ),
            supplier_name=(
                invoice.supplier.name
            ),
            customer_name=(
                invoice.customer.name
                if invoice.customer
                else None
            ),
            invoice_date=(
                invoice.invoice_date
            ),
            due_date=(
                invoice.due_date
            ),
            currency=(
                invoice.currency
            ),
            subtotal=(
                invoice.subtotal
            ),
            vat_amount=(
                invoice.vat_amount
            ),
            total_amount=(
                invoice.total_amount
            ),
            valid=validation.valid,
            warnings=(
                validation.warnings
            ),
            invoice_data=(
                invoice.model_dump(
                    mode="json"
                )
            ),
            duplicate_of_id=(
                duplicate.id
                if duplicate
                else None
            ),
        )

        session.add(
            stored_invoice
        )

        session.commit()

        session.refresh(
            stored_invoice
        )

        return stored_invoice


def list_stored_invoices(
    limit: int = 100,
) -> list[StoredInvoice]:
    with SessionLocal() as session:
        statement = (
            select(
                StoredInvoice
            )
            .order_by(
                StoredInvoice.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            session.scalars(
                statement
            ).all()
        )


def get_stored_invoice(
    invoice_id: int,
) -> StoredInvoice | None:
    with SessionLocal() as session:
        return session.get(
            StoredInvoice,
            invoice_id,
        )


def update_invoice_status(
    invoice_id: int,
    status: str,
) -> StoredInvoice | None:
    with SessionLocal() as session:
        invoice = session.get(
            StoredInvoice,
            invoice_id,
        )

        if invoice is None:
            return None

        invoice.status = status

        session.commit()

        session.refresh(
            invoice
        )

        return invoice


def _count_invoices(
    session: Session,
    *filters,
) -> int:
    statement = select(
        func.count(
            StoredInvoice.id
        )
    )

    if filters:
        statement = statement.where(
            *filters
        )

    return int(
        session.scalar(
            statement
        )
        or 0
    )


def _currency_amounts(
    session: Session,
    statuses: tuple[str, ...],
) -> list[CurrencyAmountSummary]:
    statement = (
        select(
            StoredInvoice.currency,
            func.count(
                StoredInvoice.id
            ),
            func.sum(
                StoredInvoice.total_amount
            ),
        )
        .where(
            StoredInvoice.valid.is_(True),
            StoredInvoice.duplicate_of_id.is_(
                None
            ),
            StoredInvoice.currency.is_not(
                None
            ),
            StoredInvoice.total_amount.is_not(
                None
            ),
            StoredInvoice.status.in_(
                statuses
            ),
        )
        .group_by(
            StoredInvoice.currency
        )
        .order_by(
            StoredInvoice.currency
        )
    )

    rows = session.execute(
        statement
    ).all()

    return [
        CurrencyAmountSummary(
            currency=currency,
            invoice_count=invoice_count,
            amount=amount,
        )
        for (
            currency,
            invoice_count,
            amount,
        ) in rows
        if currency is not None
        and amount is not None
    ]


def _supplier_totals(
    session: Session,
) -> list[SupplierSpendSummary]:
    total_expression = func.sum(
        StoredInvoice.total_amount
    ).label(
        "supplier_total"
    )

    statement = (
        select(
            StoredInvoice.supplier_name,
            StoredInvoice.currency,
            func.count(
                StoredInvoice.id
            ),
            total_expression,
        )
        .where(
            StoredInvoice.valid.is_(True),
            StoredInvoice.duplicate_of_id.is_(
                None
            ),
            StoredInvoice.supplier_name.is_not(
                None
            ),
            StoredInvoice.currency.is_not(
                None
            ),
            StoredInvoice.total_amount.is_not(
                None
            ),
        )
        .group_by(
            StoredInvoice.supplier_name,
            StoredInvoice.currency,
        )
        .order_by(
            StoredInvoice.currency,
            total_expression.desc(),
        )
    )

    rows = session.execute(
        statement
    ).all()

    return [
        SupplierSpendSummary(
            supplier_name=supplier_name,
            currency=currency,
            invoice_count=invoice_count,
            total_amount=total_amount,
        )
        for (
            supplier_name,
            currency,
            invoice_count,
            total_amount,
        ) in rows
        if supplier_name is not None
        and currency is not None
        and total_amount is not None
    ]


def get_analytics_summary() -> AnalyticsSummary:
    today = datetime.now(
        timezone.utc
    ).date()

    with SessionLocal() as session:
        total_invoices = _count_invoices(
            session
        )

        new_invoices = _count_invoices(
            session,
            StoredInvoice.status == "new",
        )

        approved_invoices = _count_invoices(
            session,
            StoredInvoice.status
            == "approved",
        )

        paid_invoices = _count_invoices(
            session,
            StoredInvoice.status == "paid",
        )

        duplicate_invoices = _count_invoices(
            session,
            StoredInvoice.duplicate_of_id.is_not(
                None
            ),
        )

        overdue_condition = and_(
            StoredInvoice.due_date.is_not(
                None
            ),
            StoredInvoice.due_date < today,
            StoredInvoice.status != "paid",
        )

        overdue_invoices = _count_invoices(
            session,
            overdue_condition,
        )

        requires_attention = _count_invoices(
            session,
            or_(
                StoredInvoice.valid.is_(False),
                StoredInvoice.duplicate_of_id.is_not(
                    None
                ),
                overdue_condition,
            ),
        )

        open_amounts = _currency_amounts(
            session,
            (
                "new",
                "approved",
            ),
        )

        paid_amounts = _currency_amounts(
            session,
            ("paid",),
        )

        supplier_totals = _supplier_totals(
            session
        )

        return AnalyticsSummary(
            total_invoices=total_invoices,
            new_invoices=new_invoices,
            approved_invoices=(
                approved_invoices
            ),
            paid_invoices=paid_invoices,
            overdue_invoices=(
                overdue_invoices
            ),
            duplicate_invoices=(
                duplicate_invoices
            ),
            requires_attention=(
                requires_attention
            ),
            open_amounts=open_amounts,
            paid_amounts=paid_amounts,
            supplier_totals=(
                supplier_totals
            ),
        )