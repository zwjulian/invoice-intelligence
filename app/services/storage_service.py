from datetime import (
    UTC,
    datetime,
    timedelta,
)
from decimal import Decimal

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
    MonthlyAmountSummary,
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
    now = datetime.now(
        UTC
    )

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
            status_updated_at=now,
            approved_at=None,
            paid_at=None,
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
    now = datetime.now(
        UTC
    )

    with SessionLocal() as session:
        invoice = session.get(
            StoredInvoice,
            invoice_id,
        )

        if invoice is None:
            return None

        previous_status = (
            invoice.status
        )

        invoice.status = status

        invoice.status_updated_at = now

        if (
            previous_status == "new"
            and status == "approved"
        ):
            invoice.approved_at = now

        elif (
            previous_status
            == "approved"
            and status == "new"
        ):
            invoice.approved_at = None
            invoice.paid_at = None

        elif (
            previous_status
            == "approved"
            and status == "paid"
        ):
            invoice.paid_at = now

        elif (
            previous_status == "paid"
            and status == "approved"
        ):
            invoice.paid_at = None

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
    *extra_filters,
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
            *extra_filters,
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


def _ensure_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=UTC
        )

    return value.astimezone(
        UTC
    )


def _average_duration_days(
    session: Session,
    timestamp_column,
) -> float | None:
    statement = (
        select(
            StoredInvoice.created_at,
            timestamp_column,
        )
        .where(
            StoredInvoice.valid.is_(True),
            StoredInvoice.duplicate_of_id.is_(
                None
            ),
            timestamp_column.is_not(
                None
            ),
        )
    )

    rows = session.execute(
        statement
    ).all()

    durations: list[float] = []

    for (
        created_at,
        completed_at,
    ) in rows:
        if (
            created_at is None
            or completed_at is None
        ):
            continue

        duration = (
            _ensure_utc(
                completed_at
            )
            - _ensure_utc(
                created_at
            )
        )

        durations.append(
            duration.total_seconds()
            / 86400
        )

    if not durations:
        return None

    return round(
        sum(durations)
        / len(durations),
        2,
    )


def _monthly_paid(
    session: Session,
    now: datetime,
) -> list[MonthlyAmountSummary]:
    cutoff = now - timedelta(
        days=366
    )

    statement = (
        select(
            StoredInvoice.paid_at,
            StoredInvoice.currency,
            StoredInvoice.total_amount,
        )
        .where(
            StoredInvoice.valid.is_(True),
            StoredInvoice.duplicate_of_id.is_(
                None
            ),
            StoredInvoice.status
            == "paid",
            StoredInvoice.paid_at.is_not(
                None
            ),
            StoredInvoice.paid_at
            >= cutoff,
            StoredInvoice.currency.is_not(
                None
            ),
            StoredInvoice.total_amount.is_not(
                None
            ),
        )
    )

    rows = session.execute(
        statement
    ).all()

    totals: dict[
        tuple[str, str],
        dict[str, int | Decimal],
    ] = {}

    for (
        paid_at,
        currency,
        amount,
    ) in rows:
        if (
            paid_at is None
            or currency is None
            or amount is None
        ):
            continue

        month = _ensure_utc(
            paid_at
        ).strftime(
            "%Y-%m"
        )

        key = (
            month,
            currency,
        )

        if key not in totals:
            totals[key] = {
                "invoice_count": 0,
                "amount": Decimal(0),
            }

        totals[key][
            "invoice_count"
        ] += 1

        totals[key][
            "amount"
        ] += amount

    return [
        MonthlyAmountSummary(
            month=month,
            currency=currency,
            invoice_count=int(
                values[
                    "invoice_count"
                ]
            ),
            amount=Decimal(
                values["amount"]
            ),
        )
        for (
            month,
            currency,
        ), values in sorted(
            totals.items()
        )
    ]


def get_analytics_summary() -> AnalyticsSummary:
    now = datetime.now(
        UTC
    )

    today = now.date()

    month_start = datetime(
        year=now.year,
        month=now.month,
        day=1,
        tzinfo=UTC,
    )

    if now.month == 12:
        next_month = datetime(
            year=now.year + 1,
            month=1,
            day=1,
            tzinfo=UTC,
        )
    else:
        next_month = datetime(
            year=now.year,
            month=now.month + 1,
            day=1,
            tzinfo=UTC,
        )

    approval_cutoff = (
        now
        - timedelta(
            days=7
        )
    )

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

        waiting_approval = _count_invoices(
            session,
            StoredInvoice.status == "new",
            StoredInvoice.created_at
            < approval_cutoff,
            StoredInvoice.duplicate_of_id.is_(
                None
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

        paid_this_month = (
            _currency_amounts(
                session,
                ("paid",),
                StoredInvoice.paid_at.is_not(
                    None
                ),
                StoredInvoice.paid_at
                >= month_start,
                StoredInvoice.paid_at
                < next_month,
            )
        )

        supplier_totals = _supplier_totals(
            session
        )

        average_days_to_approval = (
            _average_duration_days(
                session,
                StoredInvoice.approved_at,
            )
        )

        average_days_to_payment = (
            _average_duration_days(
                session,
                StoredInvoice.paid_at,
            )
        )

        monthly_paid = _monthly_paid(
            session,
            now,
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
            waiting_approval_over_7_days=(
                waiting_approval
            ),
            average_days_to_approval=(
                average_days_to_approval
            ),
            average_days_to_payment=(
                average_days_to_payment
            ),
            open_amounts=open_amounts,
            paid_amounts=paid_amounts,
            paid_this_month=(
                paid_this_month
            ),
            supplier_totals=(
                supplier_totals
            ),
            monthly_paid=monthly_paid,
        )