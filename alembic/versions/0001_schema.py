"""Initial schema migration: 8 tables, constraints, indexes, and vector extension.

Revision ID: 0001_schema
Revises:
Create Date: 2026-11-17 12:00:00.000000

"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1. societies
    op.create_table(
        "societies",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("annex_doc_id", sa.Text(), nullable=False),
        sa.Column("hospital_name", sa.Text(), nullable=False),
        sa.Column("hospital_address", sa.Text(), nullable=False),
        sa.Column("hospital_front_desk_phone", sa.Text(), nullable=False),
        sa.Column("hospital_emergency_phone", sa.Text(), nullable=False),
    )

    # 2. patients
    op.create_table(
        "patients",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("society_id", sa.Text(), sa.ForeignKey("societies.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.Text(), nullable=True),
        sa.Column("flat", sa.Text(), nullable=True),
        sa.CheckConstraint("language IN ('en', 'hi', 'hinglish')", name="ck_patients_language"),
    )

    # 3. clinicians
    op.create_table(
        "clinicians",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("service", sa.Text(), nullable=False),
        sa.Column("subtypes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("hospital", sa.Text(), nullable=False),
        sa.Column("slot_minutes", sa.Integer(), nullable=False),
        sa.Column("availability", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint("service IN ('DOCTOR', 'LAB')", name="ck_clinicians_service"),
    )

    # 4. service_requests
    op.create_table(
        "service_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", sa.Text(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("society_id", sa.Text(), sa.ForeignKey("societies.id"), nullable=False),
        sa.Column("clinician_id", sa.Text(), sa.ForeignKey("clinicians.id"), nullable=False),
        sa.Column("service", sa.Text(), nullable=False),
        sa.Column("subtype", sa.Text(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="CONFIRMED"),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("service IN ('DOCTOR', 'LAB')", name="ck_service_requests_service"),
        sa.CheckConstraint("status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW')", name="ck_service_requests_status"),
        sa.UniqueConstraint("request_id", name="uq_service_requests_request_id"),
    )
    # Rule 1: partial unique index uq_active_slot
    op.create_index(
        "uq_active_slot",
        "service_requests",
        ["clinician_id", "scheduled_for"],
        unique=True,
        postgresql_where=sa.text("status = 'CONFIRMED'"),
    )
    op.create_index(
        "ix_service_requests_patient_scheduled",
        "service_requests",
        ["patient_id", "scheduled_for"],
    )

    # 5. symptom_logs
    op.create_table(
        "symptom_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", sa.Text(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("society_id", sa.Text(), sa.ForeignKey("societies.id"), nullable=False),
        sa.Column("symptom", sa.Text(), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("severity BETWEEN 1 AND 5", name="ck_severity_1_5"),
        sa.UniqueConstraint("request_id", name="uq_symptom_logs_request_id"),
    )

    # 6. escalations
    op.create_table(
        "escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", sa.Text(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("society_id", sa.Text(), sa.ForeignKey("societies.id"), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="OPEN"),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raised_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("response_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_by", sa.Text(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("level IN (1, 2, 3)", name="ck_escalations_level"),
        sa.CheckConstraint("status IN ('OPEN', 'ACKNOWLEDGED', 'CLOSED')", name="ck_escalations_status"),
        sa.UniqueConstraint("request_id", name="uq_escalations_request_id"),
    )

    # 7. documents
    op.create_table(
        "documents",
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("applies_to", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("superseded_by", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("doc_id", "version", name="pk_documents"),
    )

    # 8. doc_chunks
    op.create_table(
        "doc_chunks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("heading_path", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.ForeignKeyConstraint(
            ["doc_id", "version"],
            ["documents.doc_id", "documents.version"],
            name="fk_doc_chunks_document",
            ondelete="CASCADE",
        ),
    )
    # HNSW cosine index on embedding
    op.execute(
        "CREATE INDEX ix_doc_chunks_embedding_hnsw ON doc_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("doc_chunks")
    op.drop_table("documents")
    op.drop_table("escalations")
    op.drop_table("symptom_logs")
    op.drop_table("service_requests")
    op.drop_table("clinicians")
    op.drop_table("patients")
    op.drop_table("societies")
    op.execute("DROP EXTENSION IF EXISTS vector")
