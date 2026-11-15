"""counsellor profiles: who a person can book with, by name, role and language

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

APP_ROLE = "samvid_app"


def upgrade() -> None:
    op.create_table(
        "counsellor_profile",
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("languages", postgresql.ARRAY(sa.String(length=8)), nullable=False),
        sa.Column("fictional", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('genetic_counsellor', 'clinical_geneticist', 'counselling_nurse')",
            name=op.f("ck_counsellor_profile_role"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"], ["person.id"], name=op.f("fk_counsellor_profile_person_id_person")
        ),
        sa.PrimaryKeyConstraint("person_id", name=op.f("pk_counsellor_profile")),
    )
    # No DELETE: a profile is retired by its person leaving the team, not by erasing history.
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON counsellor_profile TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table("counsellor_profile")
