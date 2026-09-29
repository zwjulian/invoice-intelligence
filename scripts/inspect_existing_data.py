from sqlalchemy import func, select, text

from app.db.database import SessionLocal
from app.db.models import InvoiceRecord, LineItemRecord


def main() -> None:
    print("=" * 70)
    print("EXISTING DATABASE DATA")
    print("=" * 70)

    with SessionLocal() as db:
        # Alembic version
        alembic_version = db.execute(
            text(
                "SELECT version_num "
                "FROM alembic_version"
            )
        ).scalar_one_or_none()

        print()
        print("ALEMBIC VERSION")
        print(f"  {alembic_version}")

        # Invoice count
        invoice_count = db.scalar(
            select(
                func.count(InvoiceRecord.id)
            )
        )

        line_item_count = db.scalar(
            select(
                func.count(LineItemRecord.id)
            )
        )

        print()
        print("ROW COUNTS")
        print(f"  invoices:           {invoice_count}")
        print(f"  invoice_line_items: {line_item_count}")

        # Existing extraction methods
        extraction_methods = db.execute(
            select(
                InvoiceRecord.extraction_method,
                func.count(InvoiceRecord.id),
            )
            .group_by(
                InvoiceRecord.extraction_method
            )
            .order_by(
                InvoiceRecord.extraction_method
            )
        ).all()

        print()
        print("EXTRACTION METHODS")

        for method, count in extraction_methods:
            print(
                f"  {method}: {count}"
            )

        # Existing statuses
        statuses = db.execute(
            select(
                InvoiceRecord.status,
                func.count(InvoiceRecord.id),
            )
            .group_by(
                InvoiceRecord.status
            )
            .order_by(
                InvoiceRecord.status
            )
        ).all()

        print()
        print("STATUSES")

        for status, count in statuses:
            print(
                f"  {status}: {count}"
            )

        # Show a few invoices, but not full potentially-sensitive data
        invoices = db.scalars(
            select(InvoiceRecord)
            .order_by(
                InvoiceRecord.id.desc()
            )
            .limit(5)
        ).all()

        print()
        print("LATEST INVOICES")

        if not invoices:
            print("  No invoices found.")

        for invoice in invoices:
            print()
            print(
                f"  ID:                {invoice.id}"
            )
            print(
                f"  Filename:          {invoice.filename}"
            )
            print(
                f"  Invoice number:    {invoice.invoice_number}"
            )
            print(
                f"  Extraction method: {invoice.extraction_method}"
            )
            print(
                f"  Status:            {invoice.status}"
            )
            print(
                f"  Valid:             {invoice.valid}"
            )
            print(
                f"  Duplicate of:      {invoice.duplicate_of_id}"
            )

            if isinstance(
                invoice.invoice_data,
                dict,
            ):
                keys = sorted(
                    invoice.invoice_data.keys()
                )

                print(
                    f"  invoice_data keys: {keys}"
                )
            else:
                print(
                    "  invoice_data is not a JSON object"
                )

        print()
        print("=" * 70)
        print("Inspection completed.")
        print("=" * 70)


if __name__ == "__main__":
    main()