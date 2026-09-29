from decimal import (
    Decimal,
    InvalidOperation,
)

from sqlalchemy import (
    func,
    select,
)

from app.database import SessionLocal
from app.db_models import (
    StoredInvoice,
    StoredInvoiceLineItem,
)


def to_decimal(
    value,
) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(
            str(value)
        )
    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return None


def main() -> None:
    print("=" * 70)
    print("BACKFILL INVOICE LINE ITEMS")
    print("=" * 70)

    created_items = 0
    processed_invoices = 0
    skipped_invoices = 0

    with SessionLocal() as session:
        invoices = list(
            session.scalars(
                select(
                    StoredInvoice
                )
                .order_by(
                    StoredInvoice.id
                )
            ).all()
        )

        print()
        print(
            f"Invoices found: {len(invoices)}"
        )

        for invoice in invoices:
            existing_count = (
                session.scalar(
                    select(
                        func.count(
                            StoredInvoiceLineItem.id
                        )
                    )
                    .where(
                        StoredInvoiceLineItem.invoice_id
                        == invoice.id
                    )
                )
                or 0
            )

            if existing_count > 0:
                print(
                    f"Invoice {invoice.id}: "
                    f"already has "
                    f"{existing_count} line item(s), "
                    "skipping."
                )

                skipped_invoices += 1
                continue

            invoice_data = (
                invoice.invoice_data
                if isinstance(
                    invoice.invoice_data,
                    dict,
                )
                else {}
            )

            line_items = (
                invoice_data.get(
                    "line_items",
                    [],
                )
            )

            if not isinstance(
                line_items,
                list,
            ):
                print(
                    f"Invoice {invoice.id}: "
                    "line_items is not a list, "
                    "skipping."
                )

                skipped_invoices += 1
                continue

            if not line_items:
                print(
                    f"Invoice {invoice.id}: "
                    "no line items found."
                )

                processed_invoices += 1
                continue

            invoice_created_items = 0

            for item in line_items:
                if not isinstance(
                    item,
                    dict,
                ):
                    print(
                        f"Invoice {invoice.id}: "
                        "invalid line item, skipping item."
                    )
                    continue

                description = str(
                    item.get(
                        "description",
                        "",
                    )
                ).strip()

                if not description:
                    print(
                        f"Invoice {invoice.id}: "
                        "line item without description, "
                        "skipping item."
                    )
                    continue

                stored_line_item = (
                    StoredInvoiceLineItem(
                        invoice_id=invoice.id,
                        description=description,
                        quantity=to_decimal(
                            item.get(
                                "quantity"
                            )
                        ),
                        unit_price=to_decimal(
                            item.get(
                                "unit_price"
                            )
                        ),
                        vat_rate=to_decimal(
                            item.get(
                                "vat_rate"
                            )
                        ),
                        total=to_decimal(
                            item.get(
                                "total"
                            )
                        ),
                    )
                )

                session.add(
                    stored_line_item
                )

                invoice_created_items += 1
                created_items += 1

            processed_invoices += 1

            print(
                f"Invoice {invoice.id}: "
                f"created "
                f"{invoice_created_items} "
                "line item(s)."
            )

        session.commit()

        total_line_items = (
            session.scalar(
                select(
                    func.count(
                        StoredInvoiceLineItem.id
                    )
                )
            )
            or 0
        )

    print()
    print("-" * 70)
    print(
        f"Processed invoices: {processed_invoices}"
    )
    print(
        f"Skipped invoices:   {skipped_invoices}"
    )
    print(
        f"Created line items:  {created_items}"
    )
    print(
        f"Total line items:    {total_line_items}"
    )
    print("-" * 70)
    print("Backfill completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()