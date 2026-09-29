import json

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import InvoiceRecord


def main() -> None:
    with SessionLocal() as db:
        invoice = db.scalar(
            select(InvoiceRecord)
            .where(InvoiceRecord.invoice_number == "INV-2026-0042")
            .order_by(InvoiceRecord.id.desc())
            .limit(1)
        )

        if invoice is None:
            print("Invoice INV-2026-0042 not found.")
            return

        print("=" * 70)
        print("INVOICE DATA INSPECTION")
        print("=" * 70)

        print()
        print(f"Database ID:     {invoice.id}")
        print(f"Filename:        {invoice.filename}")
        print(f"Invoice number:  {invoice.invoice_number}")

        print()
        print("LINE ITEMS")
        print("-" * 70)

        line_items = invoice.invoice_data.get(
            "line_items",
            [],
        )

        print(
            json.dumps(
                line_items,
                indent=2,
                ensure_ascii=False,
            )
        )

        print()
        print("VAT BREAKDOWN")
        print("-" * 70)

        vat_breakdown = invoice.invoice_data.get(
            "vat_breakdown",
            [],
        )

        print(
            json.dumps(
                vat_breakdown,
                indent=2,
                ensure_ascii=False,
            )
        )

        print()
        print("=" * 70)


if __name__ == "__main__":
    main()