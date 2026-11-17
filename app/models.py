"""SQLAlchemy 2.x declarative models matching the exact schema requirements."""

import uuid
from datetime import date, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Society(Base):
    __tablename__ = "societies"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="Asia/Kolkata")
    annex_doc_id: Mapped[str] = mapped_column(Text, nullable=False)
    hospital_name: Mapped[str] = mapped_column(Text, nullable=False)
    hospital_address: Mapped[str] = mapped_column(Text, nullable=False)
    hospital_front_desk_phone: Mapped[str] = mapped_column(Text, nullable=False)
    hospital_emergency_phone: Mapped[str] = mapped_column(Text, nullable=False)

    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="society")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    society_id: Mapped[str] = mapped_column(Text, ForeignKey("societies.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)
    flat: Mapped[str | None] = mapped_column(Text, nullable=True)

    society: Mapped["Society"] = relationship("Society", back_populates="patients")

    __table_args__ = (
        CheckConstraint("language IN ('en', 'hi', 'hinglish')", name="ck_patients_language"),
    )


class Clinician(Base):
    __tablename__ = "clinicians"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    service: Mapped[str] = mapped_column(Text, nullable=False)
    subtypes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    hospital: Mapped[str] = mapped_column(Text, nullable=False)
    slot_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    availability: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint("service IN ('DOCTOR', 'LAB')", name="ck_clinicians_service"),
    )


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    patient_id: Mapped[str] = mapped_column(Text, ForeignKey("patients.id"), nullable=False)
    society_id: Mapped[str] = mapped_column(Text, ForeignKey("societies.id"), nullable=False)
    clinician_id: Mapped[str] = mapped_column(Text, ForeignKey("clinicians.id"), nullable=False)
    service: Mapped[str] = mapped_column(Text, nullable=False)
    subtype: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="CONFIRMED",
        server_default=text("'CONFIRMED'"),
    )
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint("service IN ('DOCTOR', 'LAB')", name="ck_service_requests_service"),
        CheckConstraint(
            "status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW')",
            name="ck_service_requests_status",
        ),
        UniqueConstraint("request_id", name="uq_service_requests_request_id"),
        Index(
            "uq_active_slot",
            "clinician_id",
            "scheduled_for",
            unique=True,
            postgresql_where=text("status = 'CONFIRMED'"),
        ),
        Index("ix_service_requests_patient_scheduled", "patient_id", "scheduled_for"),
    )


class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    patient_id: Mapped[str] = mapped_column(Text, ForeignKey("patients.id"), nullable=False)
    society_id: Mapped[str] = mapped_column(Text, ForeignKey("societies.id"), nullable=False)
    symptom: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint("severity BETWEEN 1 AND 5", name="ck_severity_1_5"),
        UniqueConstraint("request_id", name="uq_symptom_logs_request_id"),
    )


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    patient_id: Mapped[str] = mapped_column(Text, ForeignKey("patients.id"), nullable=False)
    society_id: Mapped[str] = mapped_column(Text, ForeignKey("societies.id"), nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    raised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    response_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("level IN (1, 2, 3)", name="ck_escalations_level"),
        CheckConstraint("status IN ('OPEN', 'ACKNOWLEDGED', 'CLOSED')", name="ck_escalations_status"),
        UniqueConstraint("request_id", name="uq_escalations_request_id"),
    )


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    applies_to: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["DocChunk"]] = relationship(
        "DocChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocChunk(Base):
    __tablename__ = "doc_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    heading_path: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(384), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    __table_args__ = (
        ForeignKeyConstraint(
            ["doc_id", "version"],
            ["documents.doc_id", "documents.version"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_doc_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
