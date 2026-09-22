from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.db_models import StoredInvoice
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