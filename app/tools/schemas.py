"""Pydantic schemas for LLM-facing tool arguments without injected IDs."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import BookingStatus, Service, Subtype


class BookServiceInput(BaseModel):
    """Arguments for booking a doctor consultation or lab test."""

    service: Service = Field(
        ...,
        description="The category of service to book: DOCTOR or LAB.",
    )
    subtype: Subtype = Field(
        ...,
        description="The department or specific test code (e.g., CARDIOLOGY, GENERAL_PHYSICIAN, CBC).",
    )
    scheduled_for: datetime = Field(
        ...,
        description="The desired appointment start datetime on the clinician's slot grid (ISO format).",
    )


class ListServiceRequestsInput(BaseModel):
    """Arguments for listing a patient's existing bookings."""

    status: BookingStatus | None = Field(
        default=None,
        description="Optional status filter: CONFIRMED, CANCELLED, COMPLETED, or NO_SHOW.",
    )


class LogSymptomInput(BaseModel):
    """Arguments for recording a patient-reported symptom."""

    symptom: str = Field(
        ...,
        min_length=2,
        description="Description of the symptom being experienced.",
    )
    severity: int = Field(
        ...,
        ge=1,
        le=5,
        description="Severity level on a scale from 1 (mild) to 5 (severe).",
    )
