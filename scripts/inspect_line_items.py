from sqlalchemy import (
    func,
    select,
)

from app.database import SessionLocal
from app.db_models import (
    StoredInvoice,
    StoredInvoiceLineItem,
)


def main() -> None:
    with SessionLocal() as session:
        invoice_count = (
            session.scalar(
                select(
                    func.count(
                        StoredInvoice.id
                    )
                )
            )
            or 0
        )

        line_item_count = (
            session.scalar(
                select(
                    func.count(
                        StoredInvoiceLineItem.id
                    )
                )
            )
            or 0
        )

        print("=" * 70)
        print("DATABASE LINE ITEM CHECK")
        print("=" * 70)

        print()
        print(
            f"Invoices:   {invoice_count}"
        )
        print(
            f"Line items: {line_item_count}"
        )

        print()
        print("LINE ITEMS PER INVOICE")
        print("-" * 70)

        rows = session.execute(
            select(
                StoredInvoice.id,
                StoredInvoice.invoice_number,
                func.count(
                    StoredInvoiceLineItem.id
                ),
            )
            .outerjoin(
                StoredInvoiceLineItem,
                StoredInvoiceLineItem.invoice_id
                == StoredInvoice.id,
            )
            .group_by(
                StoredInvoice.id,
                StoredInvoice.invoice_number,
            )
            .order_by(
                StoredInvoice.id,
            )
        ).all()

        for (
            invoice_id,
            invoice_number,
            count,
        ) in rows:
            print(
                f"ID {invoice_id:<3} "
                f"{str(invoice_number):<25} "
                f"{count} line item(s)"
            )

        print()
        print("=" * 70)


if __name__ == "__main__":
    main()