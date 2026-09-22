from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260922_01"

down_revision: str | None = None

branch_labels: Sequence[str] | None = None

depends_on: Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()

    inspector = sa.inspect(
        connection
    )

    table_names = (
        inspector.get_table_names()
    )

    if "invoices" not in table_names:
        op.create_table(
            "invoices",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "filename",
                sa.String(
                    length=255
                ),
                nullable=False,
            ),
            sa.Column(
                "extraction_method",
                sa.String(
                    length=20
                ),
                nullable=False,
            ),
            sa.Column(
                "status",
                sa.String(
                    length=20
                ),
                nullable=False,
            ),
            sa.Column(
                "invoice_number",
                sa.String(
                    length=100
                ),
                nullable=True,
            ),
            sa.Column(
                "supplier_name",
                sa.String(
                    length=255
                ),
                nullable=True,
            ),
            sa.Column(
                "customer_name",
                sa.String(
                    length=255
                ),
                nullable=True,
            ),
            sa.Column(
                "invoice_date",
                sa.Date(),
                nullable=True,
            ),
            sa.Column(
                "due_date",
                sa.Date(),
                nullable=True,
            ),
            sa.Column(
                "currency",
                sa.String(
                    length=10
                ),
                nullable=True,
            ),
            sa.Column(
                "subtotal",
                sa.Numeric(
                    precision=14,
                    scale=2,
                ),
                nullable=True,
            ),
            sa.Column(
                "vat_amount",
                sa.Numeric(
                    precision=14,
                    scale=2,
                ),
                nullable=True,
            ),
            sa.Column(
                "total_amount",
                sa.Numeric(
                    precision=14,
                    scale=2,
                ),
                nullable=True,
            ),
            sa.Column(
                "valid",
                sa.Boolean(),
                nullable=False,
            ),
            sa.Column(
                "warnings",
                sa.JSON(),
                nullable=False,
            ),
            sa.Column(
                "invoice_data",
                sa.JSON(),
                nullable=False,
            ),
            sa.Column(
                "duplicate_of_id",
                sa.Integer(),
                sa.ForeignKey(
                    "invoices.id"
                ),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=False,
            ),
            sa.Column(
                "status_updated_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=True,
            ),
            sa.Column(
                "approved_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=True,
            ),
            sa.Column(
                "paid_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=True,
            ),
        )

        op.create_index(
            "ix_invoices_status",
            "invoices",
            ["status"],
        )

        op.create_index(
            "ix_invoices_invoice_number",
            "invoices",
            ["invoice_number"],
        )

        op.create_index(
            "ix_invoices_supplier_name",
            "invoices",
            ["supplier_name"],
        )

        op.create_index(
            "ix_invoices_due_date",
            "invoices",
            ["due_date"],
        )

        return

    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "invoices"
        )
    }

    if (
        "status_updated_at"
        not in columns
    ):
        op.add_column(
            "invoices",
            sa.Column(
                "status_updated_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=True,
            ),
        )

    if "approved_at" not in columns:
        op.add_column(
            "invoices",
            sa.Column(
                "approved_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=True,
            ),
        )

    if "paid_at" not in columns:
        op.add_column(
            "invoices",
            sa.Column(
                "paid_at",
                sa.DateTime(
                    timezone=True
                ),
                nullable=True,
            ),
        )


def downgrade() -> None:
    connection = op.get_bind()

    inspector = sa.inspect(
        connection
    )

    if (
        "invoices"
        not in inspector.get_table_names()
    ):
        return

    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "invoices"
        )
    }

    if "paid_at" in columns:
        op.drop_column(
            "invoices",
            "paid_at",
        )

    if "approved_at" in columns:
        op.drop_column(
            "invoices",
            "approved_at",
        )

    if (
        "status_updated_at"
        in columns
    ):
        op.drop_column(
            "invoices",
            "status_updated_at",
        )