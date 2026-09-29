"""add invoice correction audit history

Revision ID: 20260929_01
Revises: 20260922_01
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260929_01"

down_revision: str | None = (
    "20260922_01"
)

branch_labels: (
    str
    | Sequence[str]
    | None
) = None

depends_on: (
    str
    | Sequence[str]
    | None
) = None


def upgrade() -> None:
    op.create_table(
        "invoice_corrections",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "invoice_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "field_name",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "old_value",
            sa.JSON(),
            nullable=True,
        ),

        sa.Column(
            "new_value",
            sa.JSON(),
            nullable=True,
        ),

        sa.Column(
            "changed_by",
            sa.String(
                length=100
            ),
            nullable=False,
        ),

        sa.Column(
            "source",
            sa.String(
                length=20
            ),
            nullable=False,
            server_default="human",
        ),

        sa.Column(
            "changed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),

        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_invoice_corrections_invoice_id",
        "invoice_corrections",
        ["invoice_id"],
    )

    op.create_index(
        "ix_invoice_corrections_changed_at",
        "invoice_corrections",
        ["changed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_invoice_corrections_changed_at",
        table_name="invoice_corrections",
    )

    op.drop_index(
        "ix_invoice_corrections_invoice_id",
        table_name="invoice_corrections",
    )

    op.drop_table(
        "invoice_corrections"
    )