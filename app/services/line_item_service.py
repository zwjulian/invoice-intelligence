from sqlalchemy import (
    func,
    select,
)

from app.database import SessionLocal
from app.db_models import (
    StoredInvoiceLineItem,
)


def list_invoice_line_items(
    invoice_id: int,
) -> list[StoredInvoiceLineItem]:
    with SessionLocal() as session:
        statement = (
            select(
                StoredInvoiceLineItem
            )
            .where(
                StoredInvoiceLineItem.invoice_id
                == invoice_id
            )
            .order_by(
                StoredInvoiceLineItem.id
            )
        )

        return list(
            session.scalars(
                statement
            ).all()
        )


def get_line_item_counts(
) -> dict[int, int]:
    with SessionLocal() as session:
        statement = (
            select(
                StoredInvoiceLineItem.invoice_id,
                func.count(
                    StoredInvoiceLineItem.id
                ),
            )
            .group_by(
                StoredInvoiceLineItem.invoice_id
            )
        )

        rows = session.execute(
            statement
        ).all()

        return {
            int(invoice_id): int(count)
            for invoice_id, count
            in rows
        }