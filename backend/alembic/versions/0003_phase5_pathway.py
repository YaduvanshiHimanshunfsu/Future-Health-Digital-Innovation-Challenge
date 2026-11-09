"""care pathway reminders: one per step, and a person's choice to have none

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "care_case", sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "person",
        sa.Column(
            "reminders_opt_out", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade() -> None:
    op.drop_column("person", "reminders_opt_out")
    op.drop_column("care_case", "reminded_at")
