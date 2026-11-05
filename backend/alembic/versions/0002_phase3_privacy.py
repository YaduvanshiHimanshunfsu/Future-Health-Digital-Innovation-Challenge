"""right not to know, and expiry on authorisation changes

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "person", sa.Column("results_withheld_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "authz_outbox", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("authz_outbox", "expires_at")
    op.drop_column("person", "results_withheld_at")
