from copy import deepcopy
from datetime import (
    UTC,
    date,
    datetime,
    timedelta,
)
from decimal import Decimal

from sqlalchemy import (
    and_,
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.db_models import (
    InvoiceCorrectionRecord,
    StoredInvoice,
    StoredInvoiceLineItem,
)
from app.models.analytics import (
    AnalyticsSummary,
    CurrencyAmountSummary,
    MonthlyAmountSummary,
    SupplierSpendSummary,
)
from app.models.invoice import Invoice
from app.models.invoice_correction import (
    InvoiceCorrectionRequest,
)
from app.services.validation_service import (
    ValidationResult,
    validate_invoice,
)


def find_duplicate(
    session: Session,
    invoice: Invoice,
    exclude_invoice_id: int | None = None,
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

    filters = [
        func.lower(
            StoredInvoice.supplier_name
        )
        == supplier_name,
        StoredInvoice.invoice_number
        == invoice_number,
    ]

    if exclude_invoice_id is not None:
        filters.append(
            StoredInvoice.id
            != exclude_invoice_id
        )

    statement = (
        select(
            StoredInvoice
        )
        .where(
            *filters
        )
        .order_by(
            StoredInvoice.id
        )
        .limit(1)
    )

    return session.scalar(
        statement
    )


def _replace_line_items(
    session: Session,
    invoice_id: int,
    invoice: Invoice,
) -> None:
    session.execute(
        delete(
            StoredInvoiceLineItem
        )
        .where(
            StoredInvoiceLineItem.invoice_id
            == invoice_id
        )
    )

    for item in invoice.line_items:
        stored_line_item = (
            StoredInvoiceLineItem(
                invoice_id=invoice_id,
                description=(
                    item.description
                ),
                quantity=(
                    item.quantity
                ),
                unit_price=(
                    item.unit_price
                ),
                vat_rate=(
                    item.vat_rate
                ),
                total=(
                    item.total
                ),
            )
        )

        session.add(
            stored_line_item
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

        session.flush()

        _replace_line_items(
            session=session,
            invoice_id=(
                stored_invoice.id
            ),
            invoice=invoice,
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
                StoredInvoice
                .created_at
                .desc()
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

        invoice.status_updated_at = (
            now
        )

        if (
            previous_status == "new"
            and status == "approved"
        ):
            invoice.approved_at = now

        elif (
            previous_status == "approved"
            and status == "new"
        ):
            invoice.approved_at = None
            invoice.paid_at = None

        elif (
            previous_status == "approved"
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


def get_invoice_corrections(
    invoice_id: int,
) -> list[
    InvoiceCorrectionRecord
]:
    with SessionLocal() as session:
        statement = (
            select(
                InvoiceCorrectionRecord
            )
            .where(
                InvoiceCorrectionRecord.invoice_id
                == invoice_id
            )
            .order_by(
                InvoiceCorrectionRecord
                .changed_at
                .desc(),
                InvoiceCorrectionRecord
                .id
                .desc(),
            )
        )

        return list(
            session.scalars(
                statement
            ).all()
        )


def _json_value(
    value,
):
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        Decimal,
    ):
        return str(value)

    if isinstance(
        value,
        list,
    ):
        result = []

        for item in value:
            if hasattr(
                item,
                "model_dump",
            ):
                result.append(
                    item.model_dump(
                        mode="json"
                    )
                )
            else:
                result.append(
                    _json_value(
                        item
                    )
                )

        return result

    if hasattr(
        value,
        "model_dump",
    ):
        return value.model_dump(
            mode="json"
        )

    return value


def _get_data_value(
    data: dict,
    field_name: str,
):
    nested_fields = {
        "supplier_name": (
            "supplier",
            "name",
        ),
        "supplier_address": (
            "supplier",
            "address",
        ),
        "supplier_vat_number": (
            "supplier",
            "vat_number",
        ),
        "customer_name": (
            "customer",
            "name",
        ),
        "customer_address": (
            "customer",
            "address",
        ),
        "customer_vat_number": (
            "customer",
            "vat_number",
        ),
    }

    if field_name in nested_fields:
        section_name, key = (
            nested_fields[
                field_name
            ]
        )

        section = data.get(
            section_name
        )

        if not isinstance(
            section,
            dict,
        ):
            return None

        return section.get(
            key
        )

    return data.get(
        field_name
    )


def _set_data_value(
    data: dict,
    field_name: str,
    value,
) -> None:
    nested_fields = {
        "supplier_name": (
            "supplier",
            "name",
        ),
        "supplier_address": (
            "supplier",
            "address",
        ),
        "supplier_vat_number": (
            "supplier",
            "vat_number",
        ),
        "customer_name": (
            "customer",
            "name",
        ),
        "customer_address": (
            "customer",
            "address",
        ),
        "customer_vat_number": (
            "customer",
            "vat_number",
        ),
    }

    if field_name in nested_fields:
        section_name, key = (
            nested_fields[
                field_name
            ]
        )

        section = data.get(
            section_name
        )

        if not isinstance(
            section,
            dict,
        ):
            section = {}

            data[
                section_name
            ] = section

        section[key] = value

        return

    data[
        field_name
    ] = value


def _values_equal(
    field_name: str,
    old_value,
    new_value,
) -> bool:
    decimal_fields = {
        "subtotal",
        "vat_amount",
        "total_amount",
    }

    if (
        field_name in decimal_fields
        and old_value is not None
        and new_value is not None
    ):
        try:
            return (
                Decimal(
                    str(old_value)
                )
                ==
                Decimal(
                    str(new_value)
                )
            )
        except (
            ValueError,
            TypeError,
        ):
            pass

    return (
        old_value
        == new_value
    )


def update_invoice_from_correction(
    invoice_id: int,
    update: InvoiceCorrectionRequest,
) -> StoredInvoice | None:
    now = datetime.now(
        UTC
    )

    changed_by = (
        update.changed_by.strip()
        or "manual-review"
    )

    editable_fields = {
        "invoice_number",
        "invoice_date",
        "due_date",
        "supplier_name",
        "supplier_address",
        "supplier_vat_number",
        "customer_name",
        "customer_address",
        "customer_vat_number",
        "currency",
        "subtotal",
        "vat_amount",
        "total_amount",
        "line_items",
    }

    requested_fields = (
        update.model_fields_set
        & editable_fields
    )

    with SessionLocal() as session:
        stored_invoice = session.get(
            StoredInvoice,
            invoice_id,
        )

        if stored_invoice is None:
            return None

        data = deepcopy(
            stored_invoice.invoice_data
        )

        changes: list[
            tuple[
                str,
                object | None,
                object | None,
            ]
        ] = []

        for field_name in sorted(
            requested_fields
        ):
            old_value = (
                _get_data_value(
                    data,
                    field_name,
                )
            )

            new_value = _json_value(
                getattr(
                    update,
                    field_name,
                )
            )

            if (
                field_name == "line_items"
                and new_value is None
            ):
                new_value = []

            if _values_equal(
                field_name,
                old_value,
                new_value,
            ):
                continue

            _set_data_value(
                data,
                field_name,
                new_value,
            )

            changes.append(
                (
                    field_name,
                    old_value,
                    new_value,
                )
            )

        if not changes:
            return stored_invoice

        corrected_invoice = (
            Invoice.model_validate(
                data
            )
        )

        validation = (
            validate_invoice(
                corrected_invoice
            )
        )

        stored_invoice.invoice_number = (
            corrected_invoice
            .invoice_number
        )

        stored_invoice.supplier_name = (
            corrected_invoice
            .supplier
            .name
        )

        stored_invoice.customer_name = (
            corrected_invoice
            .customer
            .name
            if corrected_invoice.customer
            else None
        )

        stored_invoice.invoice_date = (
            corrected_invoice
            .invoice_date
        )

        stored_invoice.due_date = (
            corrected_invoice
            .due_date
        )

        stored_invoice.currency = (
            corrected_invoice
            .currency
        )

        stored_invoice.subtotal = (
            corrected_invoice
            .subtotal
        )

        stored_invoice.vat_amount = (
            corrected_invoice
            .vat_amount
        )

        stored_invoice.total_amount = (
            corrected_invoice
            .total_amount
        )

        stored_invoice.valid = (
            validation.valid
        )

        stored_invoice.warnings = (
            validation.warnings
        )

        stored_invoice.invoice_data = (
            corrected_invoice.model_dump(
                mode="json"
            )
        )

        duplicate = find_duplicate(
            session=session,
            invoice=corrected_invoice,
            exclude_invoice_id=(
                stored_invoice.id
            ),
        )

        stored_invoice.duplicate_of_id = (
            duplicate.id
            if duplicate
            else None
        )

        changed_field_names = {
            field_name
            for (
                field_name,
                _,
                _,
            )
            in changes
        }

        if (
            "line_items"
            in changed_field_names
        ):
            _replace_line_items(
                session=session,
                invoice_id=(
                    stored_invoice.id
                ),
                invoice=(
                    corrected_invoice
                ),
            )

        for (
            field_name,
            old_value,
            new_value,
        ) in changes:
            correction = (
                InvoiceCorrectionRecord(
                    invoice_id=(
                        stored_invoice.id
                    ),
                    field_name=(
                        field_name
                    ),
                    old_value=(
                        old_value
                    ),
                    new_value=(
                        new_value
                    ),
                    changed_by=(
                        changed_by
                    ),
                    source="human",
                    changed_at=now,
                )
            )

            session.add(
                correction
            )

        if (
            stored_invoice.status
            != "new"
        ):
            previous_status = (
                stored_invoice.status
            )

            status_correction = (
                InvoiceCorrectionRecord(
                    invoice_id=(
                        stored_invoice.id
                    ),
                    field_name="status",
                    old_value=(
                        previous_status
                    ),
                    new_value="new",
                    changed_by=(
                        changed_by
                    ),
                    source="system",
                    changed_at=now,
                )
            )

            session.add(
                status_correction
            )

            stored_invoice.status = (
                "new"
            )

            stored_invoice.status_updated_at = (
                now
            )

            stored_invoice.approved_at = (
                None
            )

            stored_invoice.paid_at = (
                None
            )

        session.commit()

        session.refresh(
            stored_invoice
        )

        return stored_invoice


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
) -> list[
    CurrencyAmountSummary
]:
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
            StoredInvoice.valid.is_(
                True
            ),
            StoredInvoice
            .duplicate_of_id
            .is_(
                None
            ),
            StoredInvoice
            .currency
            .is_not(
                None
            ),
            StoredInvoice
            .total_amount
            .is_not(
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
            invoice_count=(
                invoice_count
            ),
            amount=amount,
        )
        for (
            currency,
            invoice_count,
            amount,
        )
        in rows
        if currency is not None
        and amount is not None
    ]


def _supplier_totals(
    session: Session,
) -> list[
    SupplierSpendSummary
]:
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
            StoredInvoice.valid.is_(
                True
            ),
            StoredInvoice
            .duplicate_of_id
            .is_(
                None
            ),
            StoredInvoice
            .supplier_name
            .is_not(
                None
            ),
            StoredInvoice
            .currency
            .is_not(
                None
            ),
            StoredInvoice
            .total_amount
            .is_not(
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
            supplier_name=(
                supplier_name
            ),
            currency=currency,
            invoice_count=(
                invoice_count
            ),
            total_amount=(
                total_amount
            ),
        )
        for (
            supplier_name,
            currency,
            invoice_count,
            total_amount,
        )
        in rows
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
            StoredInvoice.valid.is_(
                True
            ),
            StoredInvoice
            .duplicate_of_id
            .is_(
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

    durations: list[
        float
    ] = []

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
) -> list[
    MonthlyAmountSummary
]:
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
            StoredInvoice.valid.is_(
                True
            ),
            StoredInvoice
            .duplicate_of_id
            .is_(
                None
            ),
            StoredInvoice.status
            == "paid",
            StoredInvoice
            .paid_at
            .is_not(
                None
            ),
            StoredInvoice.paid_at
            >= cutoff,
            StoredInvoice
            .currency
            .is_not(
                None
            ),
            StoredInvoice
            .total_amount
            .is_not(
                None
            ),
        )
    )

    rows = session.execute(
        statement
    ).all()

    totals: dict[
        tuple[str, str],
        dict[
            str,
            int | Decimal,
        ],
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
                values[
                    "amount"
                ]
            ),
        )
        for (
            month,
            currency,
        ), values
        in sorted(
            totals.items()
        )
    ]


def get_analytics_summary(
) -> AnalyticsSummary:
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
        total_invoices = (
            _count_invoices(
                session
            )
        )

        new_invoices = (
            _count_invoices(
                session,
                StoredInvoice.status
                == "new",
            )
        )

        approved_invoices = (
            _count_invoices(
                session,
                StoredInvoice.status
                == "approved",
            )
        )

        paid_invoices = (
            _count_invoices(
                session,
                StoredInvoice.status
                == "paid",
            )
        )

        duplicate_invoices = (
            _count_invoices(
                session,
                StoredInvoice
                .duplicate_of_id
                .is_not(
                    None
                ),
            )
        )

        overdue_condition = and_(
            StoredInvoice
            .due_date
            .is_not(
                None
            ),
            StoredInvoice.due_date
            < today,
            StoredInvoice.status
            != "paid",
        )

        overdue_invoices = (
            _count_invoices(
                session,
                overdue_condition,
            )
        )

        requires_attention = (
            _count_invoices(
                session,
                or_(
                    StoredInvoice.valid
                    .is_(
                        False
                    ),
                    StoredInvoice
                    .duplicate_of_id
                    .is_not(
                        None
                    ),
                    overdue_condition,
                ),
            )
        )

        waiting_approval = (
            _count_invoices(
                session,
                StoredInvoice.status
                == "new",
                StoredInvoice.created_at
                < approval_cutoff,
                StoredInvoice
                .duplicate_of_id
                .is_(
                    None
                ),
            )
        )

        open_amounts = (
            _currency_amounts(
                session,
                (
                    "new",
                    "approved",
                ),
            )
        )

        paid_amounts = (
            _currency_amounts(
                session,
                (
                    "paid",
                ),
            )
        )

        paid_this_month = (
            _currency_amounts(
                session,
                (
                    "paid",
                ),
                StoredInvoice
                .paid_at
                .is_not(
                    None
                ),
                StoredInvoice.paid_at
                >= month_start,
                StoredInvoice.paid_at
                < next_month,
            )
        )

        supplier_totals = (
            _supplier_totals(
                session
            )
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

        monthly_paid = (
            _monthly_paid(
                session,
                now,
            )
        )

        return AnalyticsSummary(
            total_invoices=(
                total_invoices
            ),
            new_invoices=(
                new_invoices
            ),
            approved_invoices=(
                approved_invoices
            ),
            paid_invoices=(
                paid_invoices
            ),
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
            open_amounts=(
                open_amounts
            ),
            paid_amounts=(
                paid_amounts
            ),
            paid_this_month=(
                paid_this_month
            ),
            supplier_totals=(
                supplier_totals
            ),
            monthly_paid=(
                monthly_paid
            ),
        )