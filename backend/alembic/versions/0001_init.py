"""init

Revision ID: 0001
Revises:
"""

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

APP_ROLE = "samvid_app"

# The API's database role gets the least it needs. Records of what happened (consents, pathway steps,
# measurement events) can be added to and, where the flow needs it, updated, but not deleted.
READ_WRITE_TABLES = (
    "appointment",
    "assessment",
    "break_glass_event",
    "care_case",
    "carrier_finding",
    "case_note",
    "centre",
    "consent",
    "couple",
    "genetic_report",
    "invitation",
    "person",
    "referral",
)
APPEND_ONLY_TABLES = ("audit_log", "event", "pathway_step")
DELETABLE_TABLES = ("authz_outbox", "conversation", "kb_chunk", "message", "values_note")


def _apply_grants() -> None:
    for table in READ_WRITE_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON {table} TO {APP_ROLE}")
    for table in APPEND_ONLY_TABLES:
        op.execute(f"GRANT SELECT, INSERT ON {table} TO {APP_ROLE}")
    for table in DELETABLE_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")


def _protect_audit_log() -> None:
    # Grants already stop the API's role. The triggers also stop the owner's role doing it by accident,
    # so changing history takes a deliberate DISABLE TRIGGER, which is itself visible.
    op.execute(
        """
        CREATE FUNCTION audit_log_is_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_no_change BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_is_append_only()
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON audit_log
        FOR EACH STATEMENT EXECUTE FUNCTION audit_log_is_append_only()
        """
    )


def upgrade() -> None:
    # Created by infra/postgres/init.sql as a superuser. This only confirms it's there.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "audit_log",
        sa.Column("seq", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("seq", name=op.f("pk_audit_log")),
        sa.UniqueConstraint("hash", name=op.f("uq_audit_log_hash")),
    )
    op.create_index("ix_audit_log_resource_seq", "audit_log", ["resource", "seq"], unique=False)
    op.create_table(
        "authz_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(length=8), nullable=False),
        sa.Column("subject", sa.String(length=128), nullable=False),
        sa.Column("relation", sa.String(length=64), nullable=False),
        sa.Column("object", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "operation IN ('write', 'delete')", name=op.f("ck_authz_outbox_operation")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_authz_outbox")),
    )
    op.create_index(
        "ix_authz_outbox_pending",
        "authz_outbox",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("applied_at IS NULL"),
    )
    op.create_table(
        "centre",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pack_code", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("services", sa.String(length=160), nullable=False),
        sa.Column("contact", sa.String(length=160), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.Column("checked_on", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_centre")),
    )
    op.create_index("ix_centre_pack_region", "centre", ["pack_code", "region"], unique=False)
    op.create_table(
        "event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(length=32), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("pack_code", sa.String(length=32), nullable=True),
        sa.Column("lang", sa.String(length=8), nullable=True),
        sa.Column("literacy", sa.String(length=8), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("age_band", sa.String(length=8), nullable=True),
        sa.Column("gender", sa.String(length=16), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column(
            "at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event")),
    )
    op.create_index("ix_event_kind_at", "event", ["kind", "at"], unique=False)
    op.create_index(op.f("ix_event_subject"), "event", ["subject"], unique=False)
    op.create_table(
        "kb_chunk",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pack_code", sa.String(length=32), nullable=True),
        sa.Column("condition_id", sa.String(length=32), nullable=False),
        sa.Column("lang", sa.String(length=8), nullable=False),
        sa.Column("level", sa.String(length=8), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reviewed_by", sa.String(length=64), nullable=True),
        sa.Column("content_version", sa.String(length=16), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "level IN ('simple', 'standard', 'detailed')", name=op.f("ck_kb_chunk_level")
        ),
        sa.CheckConstraint("status IN ('draft', 'reviewed')", name=op.f("ck_kb_chunk_status")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kb_chunk")),
    )
    op.create_index(
        "ix_kb_chunk_lookup",
        "kb_chunk",
        ["pack_code", "lang", "level", "condition_id"],
        unique=False,
    )
    op.create_table(
        "person",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("keycloak_sub", sa.String(length=64), nullable=True),
        sa.Column("national_id_hash", sa.String(length=64), nullable=True),
        sa.Column("pack_code", sa.String(length=32), nullable=False),
        sa.Column("preferred_lang", sa.String(length=8), nullable=False),
        sa.Column("literacy_level", sa.String(length=8), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("age_band", sa.String(length=8), nullable=True),
        sa.Column("gender", sa.String(length=16), nullable=True),
        sa.Column("clinical_enc", sa.LargeBinary(), nullable=True),
        sa.Column("service_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "literacy_level IN ('simple', 'standard', 'detailed')",
            name=op.f("ck_person_literacy_level"),
        ),
        sa.CheckConstraint(
            "keycloak_sub IS NOT NULL OR national_id_hash IS NOT NULL",
            name=op.f("ck_person_has_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_person")),
        sa.UniqueConstraint("keycloak_sub", name=op.f("uq_person_keycloak_sub")),
        sa.UniqueConstraint("national_id_hash", name=op.f("uq_person_national_id_hash")),
    )
    op.create_table(
        "assessment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("instrument", sa.String(length=16), nullable=False),
        sa.Column("phase", sa.String(length=8), nullable=False),
        sa.Column("lang", sa.String(length=8), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "instrument IN ('teach_back', 'mmic_adapted', 'sure', 'gcos')",
            name=op.f("ck_assessment_instrument"),
        ),
        sa.CheckConstraint("phase IN ('pre', 'post')", name=op.f("ck_assessment_phase")),
        sa.ForeignKeyConstraint(
            ["person_id"], ["person.id"], name=op.f("fk_assessment_person_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment")),
    )
    op.create_index(op.f("ix_assessment_person_id"), "assessment", ["person_id"], unique=False)
    op.create_table(
        "conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("lang", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["person_id"], ["person.id"], name=op.f("fk_conversation_person_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation")),
    )
    op.create_index(op.f("ix_conversation_person_id"), "conversation", ["person_id"], unique=False)
    op.create_table(
        "couple",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_a", sa.Uuid(), nullable=False),
        sa.Column("person_b", sa.Uuid(), nullable=True),
        sa.Column("invite_code_hash", sa.String(length=64), nullable=True),
        sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details_enc", sa.LargeBinary(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("person_a <> person_b", name=op.f("ck_couple_distinct_partners")),
        sa.ForeignKeyConstraint(
            ["person_a"], ["person.id"], name=op.f("fk_couple_person_a_person")
        ),
        sa.ForeignKeyConstraint(
            ["person_b"], ["person.id"], name=op.f("fk_couple_person_b_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_couple")),
        sa.UniqueConstraint("invite_code_hash", name=op.f("uq_couple_invite_code_hash")),
    )
    op.create_index(op.f("ix_couple_person_a"), "couple", ["person_a"], unique=False)
    op.create_index(op.f("ix_couple_person_b"), "couple", ["person_b"], unique=False)
    op.create_table(
        "genetic_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("source_lab", sa.String(length=64), nullable=False),
        sa.Column("source_report_id", sa.String(length=128), nullable=False),
        sa.Column("report_version", sa.Integer(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("panel_version", sa.String(length=32), nullable=False),
        sa.Column("bundle_sha256", sa.String(length=64), nullable=False),
        sa.Column("attestation", sa.String(length=16), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "attestation IN ('verified', 'demo', 'unverified')",
            name=op.f("ck_genetic_report_attestation"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"], ["person.id"], name=op.f("fk_genetic_report_person_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_genetic_report")),
        sa.UniqueConstraint(
            "source_lab",
            "source_report_id",
            "report_version",
            name=op.f("uq_genetic_report_source_lab"),
        ),
    )
    op.create_index(
        op.f("ix_genetic_report_person_id"), "genetic_report", ["person_id"], unique=False
    )
    op.create_table(
        "invitation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("relation_enc", sa.LargeBinary(), nullable=False),
        sa.Column("disclose_identity", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"], ["person.id"], name=op.f("fk_invitation_sender_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invitation")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_invitation_token_hash")),
    )
    op.create_index(op.f("ix_invitation_sender_id"), "invitation", ["sender_id"], unique=False)
    op.create_table(
        "care_case",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("couple_id", sa.Uuid(), nullable=True),
        sa.Column("counsellor_id", sa.Uuid(), nullable=True),
        sa.Column("priority", sa.String(length=2), nullable=False),
        sa.Column("reasons_enc", sa.LargeBinary(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("step_due", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stalled", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "priority IN ('P1', 'P2', 'P3', 'P4')", name=op.f("ck_care_case_priority")
        ),
        sa.CheckConstraint(
            "state IN ('RESULT_RELEASED', 'EDUCATION_VIEWED', 'COMPREHENSION_CHECKED', 'COUNSELLING_REQUESTED', 'COUNSELLING_BOOKED', 'COUNSELLING_DONE', 'CONFIRMATORY_TEST_ORDERED', 'CONFIRMED', 'NOT_CONFIRMED', 'REPRO_GENOMICS_REFERRED', 'REFERRAL_ACCEPTED', 'DECLINED_BY_USER', 'LOST_TO_FOLLOW_UP', 'CLOSED')",
            name=op.f("ck_care_case_state"),
        ),
        sa.ForeignKeyConstraint(
            ["counsellor_id"], ["person.id"], name=op.f("fk_care_case_counsellor_id_person")
        ),
        sa.ForeignKeyConstraint(
            ["couple_id"], ["couple.id"], name=op.f("fk_care_case_couple_id_couple")
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["person.id"], name=op.f("fk_care_case_subject_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_care_case")),
    )
    op.create_index(op.f("ix_care_case_couple_id"), "care_case", ["couple_id"], unique=False)
    op.create_index(
        "ix_care_case_queue",
        "care_case",
        ["counsellor_id", "state", "priority", "step_due"],
        unique=False,
    )
    op.create_index(op.f("ix_care_case_step_due"), "care_case", ["step_due"], unique=False)
    op.create_index(op.f("ix_care_case_subject_id"), "care_case", ["subject_id"], unique=False)
    op.create_table(
        "carrier_finding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("payload_enc", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["genetic_report.id"],
            name=op.f("fk_carrier_finding_report_id_genetic_report"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_carrier_finding")),
    )
    op.create_index(
        op.f("ix_carrier_finding_report_id"), "carrier_finding", ["report_id"], unique=False
    )
    op.create_table(
        "consent",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("grantor_id", sa.Uuid(), nullable=False),
        sa.Column("grantee_id", sa.Uuid(), nullable=True),
        sa.Column("couple_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("reveal_level", sa.String(length=8), nullable=True),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("terms_version", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(kind = 'couple_match') = (couple_id IS NOT NULL AND reveal_level IS NOT NULL)",
            name=op.f("ck_consent_couple_match_fields"),
        ),
        sa.CheckConstraint(
            "kind IN ('service', 'couple_match', 'share_summary', 'share_full', 'research')",
            name=op.f("ck_consent_kind"),
        ),
        sa.CheckConstraint(
            "kind NOT IN ('share_summary', 'share_full') OR (grantee_id IS NOT NULL AND expires_at IS NOT NULL)",
            name=op.f("ck_consent_share_needs_grantee_and_expiry"),
        ),
        sa.CheckConstraint(
            "reveal_level IN ('yes_no', 'genes')", name=op.f("ck_consent_reveal_level")
        ),
        sa.ForeignKeyConstraint(
            ["couple_id"], ["couple.id"], name=op.f("fk_consent_couple_id_couple")
        ),
        sa.ForeignKeyConstraint(
            ["grantee_id"], ["person.id"], name=op.f("fk_consent_grantee_id_person")
        ),
        sa.ForeignKeyConstraint(
            ["grantor_id"], ["person.id"], name=op.f("fk_consent_grantor_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_consent")),
    )
    op.create_index(op.f("ix_consent_couple_id"), "consent", ["couple_id"], unique=False)
    op.create_index(op.f("ix_consent_grantee_id"), "consent", ["grantee_id"], unique=False)
    op.create_index(op.f("ix_consent_grantor_id"), "consent", ["grantor_id"], unique=False)
    op.create_index(
        "uq_consent_live_couple_match",
        "consent",
        ["grantor_id", "couple_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'couple_match' AND revoked_at IS NULL"),
    )
    op.create_table(
        "message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content_enc", sa.LargeBinary(), nullable=False),
        sa.Column("boundary", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=True),
        sa.Column("validator_flags", postgresql.ARRAY(sa.String(length=48)), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "boundary IN ('EDUCATION', 'DECISION_SUPPORT', 'CLINICAL_ADVICE', 'DISTRESS', 'COERCION')",
            name=op.f("ck_message_boundary"),
        ),
        sa.CheckConstraint("source IN ('llm', 'template')", name=op.f("ck_message_source")),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
            name=op.f("fk_message_conversation_id_conversation"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message")),
    )
    op.create_index(
        op.f("ix_message_conversation_id"), "message", ["conversation_id"], unique=False
    )
    op.create_table(
        "appointment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("counsellor_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("lang", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("mode IN ('in_person', 'video')", name=op.f("ck_appointment_mode")),
        sa.CheckConstraint(
            "status IN ('open', 'booked', 'cancelled', 'completed')",
            name=op.f("ck_appointment_status"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["care_case.id"], name=op.f("fk_appointment_case_id_care_case")
        ),
        sa.ForeignKeyConstraint(
            ["counsellor_id"], ["person.id"], name=op.f("fk_appointment_counsellor_id_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointment")),
    )
    op.create_index(op.f("ix_appointment_case_id"), "appointment", ["case_id"], unique=False)
    op.create_index(
        "uq_appointment_counsellor_slot",
        "appointment",
        ["counsellor_id", "starts_at"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )
    op.create_table(
        "break_glass_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(reason) >= 10", name=op.f("ck_break_glass_event_reason_given")
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["person.id"], name=op.f("fk_break_glass_event_actor_id_person")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["care_case.id"], name=op.f("fk_break_glass_event_case_id_care_case")
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["person.id"], name=op.f("fk_break_glass_event_reviewed_by_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_break_glass_event")),
    )
    op.create_index(
        op.f("ix_break_glass_event_actor_id"), "break_glass_event", ["actor_id"], unique=False
    )
    op.create_index(
        op.f("ix_break_glass_event_case_id"), "break_glass_event", ["case_id"], unique=False
    )
    op.create_table(
        "case_note",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body_enc", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["person.id"], name=op.f("fk_case_note_author_id_person")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["care_case.id"], name=op.f("fk_case_note_case_id_care_case")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_note")),
    )
    op.create_index(op.f("ix_case_note_case_id"), "case_note", ["case_id"], unique=False)
    op.create_table(
        "pathway_step",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("from_state", sa.String(length=32), nullable=True),
        sa.Column("to_state", sa.String(length=32), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("fhir_ref", sa.String(length=128), nullable=True),
        sa.Column(
            "at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "to_state IN ('RESULT_RELEASED', 'EDUCATION_VIEWED', 'COMPREHENSION_CHECKED', 'COUNSELLING_REQUESTED', 'COUNSELLING_BOOKED', 'COUNSELLING_DONE', 'CONFIRMATORY_TEST_ORDERED', 'CONFIRMED', 'NOT_CONFIRMED', 'REPRO_GENOMICS_REFERRED', 'REFERRAL_ACCEPTED', 'DECLINED_BY_USER', 'LOST_TO_FOLLOW_UP', 'CLOSED')",
            name=op.f("ck_pathway_step_to_state"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["care_case.id"], name=op.f("fk_pathway_step_case_id_care_case")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pathway_step")),
    )
    op.create_index(op.f("ix_pathway_step_case_id"), "pathway_step", ["case_id"], unique=False)
    op.create_table(
        "referral",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("destination", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("fhir_ref", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('confirmatory_lab', 'reproductive_genomics')", name=op.f("ck_referral_kind")
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'accepted', 'declined', 'cancelled')",
            name=op.f("ck_referral_status"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["care_case.id"], name=op.f("fk_referral_case_id_care_case")
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["person.id"], name=op.f("fk_referral_created_by_person")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_referral")),
    )
    op.create_index(op.f("ix_referral_case_id"), "referral", ["case_id"], unique=False)
    op.create_table(
        "values_note",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("answers_enc", sa.LargeBinary(), nullable=False),
        sa.Column("shared_with_case_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["person_id"], ["person.id"], name=op.f("fk_values_note_person_id_person")
        ),
        sa.ForeignKeyConstraint(
            ["shared_with_case_id"],
            ["care_case.id"],
            name=op.f("fk_values_note_shared_with_case_id_care_case"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_values_note")),
    )
    op.create_index(op.f("ix_values_note_person_id"), "values_note", ["person_id"], unique=False)
    _apply_grants()
    _protect_audit_log()


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_log_no_truncate ON audit_log")
    op.execute("DROP TRIGGER audit_log_no_change ON audit_log")
    op.execute("DROP FUNCTION audit_log_is_append_only()")
    op.drop_index(op.f("ix_values_note_person_id"), table_name="values_note")
    op.drop_table("values_note")
    op.drop_index(op.f("ix_referral_case_id"), table_name="referral")
    op.drop_table("referral")
    op.drop_index(op.f("ix_pathway_step_case_id"), table_name="pathway_step")
    op.drop_table("pathway_step")
    op.drop_index(op.f("ix_case_note_case_id"), table_name="case_note")
    op.drop_table("case_note")
    op.drop_index(op.f("ix_break_glass_event_case_id"), table_name="break_glass_event")
    op.drop_index(op.f("ix_break_glass_event_actor_id"), table_name="break_glass_event")
    op.drop_table("break_glass_event")
    op.drop_index(
        "uq_appointment_counsellor_slot",
        table_name="appointment",
        postgresql_where=sa.text("status <> 'cancelled'"),
    )
    op.drop_index(op.f("ix_appointment_case_id"), table_name="appointment")
    op.drop_table("appointment")
    op.drop_index(op.f("ix_message_conversation_id"), table_name="message")
    op.drop_table("message")
    op.drop_index(
        "uq_consent_live_couple_match",
        table_name="consent",
        postgresql_where=sa.text("kind = 'couple_match' AND revoked_at IS NULL"),
    )
    op.drop_index(op.f("ix_consent_grantor_id"), table_name="consent")
    op.drop_index(op.f("ix_consent_grantee_id"), table_name="consent")
    op.drop_index(op.f("ix_consent_couple_id"), table_name="consent")
    op.drop_table("consent")
    op.drop_index(op.f("ix_carrier_finding_report_id"), table_name="carrier_finding")
    op.drop_table("carrier_finding")
    op.drop_index(op.f("ix_care_case_subject_id"), table_name="care_case")
    op.drop_index(op.f("ix_care_case_step_due"), table_name="care_case")
    op.drop_index("ix_care_case_queue", table_name="care_case")
    op.drop_index(op.f("ix_care_case_couple_id"), table_name="care_case")
    op.drop_table("care_case")
    op.drop_index(op.f("ix_invitation_sender_id"), table_name="invitation")
    op.drop_table("invitation")
    op.drop_index(op.f("ix_genetic_report_person_id"), table_name="genetic_report")
    op.drop_table("genetic_report")
    op.drop_index(op.f("ix_couple_person_b"), table_name="couple")
    op.drop_index(op.f("ix_couple_person_a"), table_name="couple")
    op.drop_table("couple")
    op.drop_index(op.f("ix_conversation_person_id"), table_name="conversation")
    op.drop_table("conversation")
    op.drop_index(op.f("ix_assessment_person_id"), table_name="assessment")
    op.drop_table("assessment")
    op.drop_table("person")
    op.drop_index("ix_kb_chunk_lookup", table_name="kb_chunk")
    op.drop_table("kb_chunk")
    op.drop_index(op.f("ix_event_subject"), table_name="event")
    op.drop_index("ix_event_kind_at", table_name="event")
    op.drop_table("event")
    op.drop_index("ix_centre_pack_region", table_name="centre")
    op.drop_table("centre")
    op.drop_index(
        "ix_authz_outbox_pending",
        table_name="authz_outbox",
        postgresql_where=sa.text("applied_at IS NULL"),
    )
    op.drop_table("authz_outbox")
    op.drop_index("ix_audit_log_resource_seq", table_name="audit_log")
    op.drop_table("audit_log")
