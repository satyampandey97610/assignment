"""Tests for tool failure handling: unexpected exceptions, malformed arguments, and database checks."""

import uuid
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.enums import Service, Subtype
from app.tools import api, langchain_tools
from app.tools.schemas import BookServiceInput, LogSymptomInput

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_log_symptom_invalid_severity_rejected_by_db():
    """Severity outside 1-5 is rejected with INVALID_SEVERITY error code."""
    res = await api.log_symptom(
        patient_id="pat_001",
        symptom="Severe migraine",
        severity=9,
        request_id=uuid.uuid4(),
    )
    assert res["ok"] is False
    assert res["error_code"] == "INVALID_SEVERITY"
    assert "Severity must be an integer between 1 and 5" in res["message"]


def test_pydantic_schema_validation_catches_malformed_args():
    """Pydantic schemas reject out-of-range or missing fields before execution."""
    # Symptom too short
    with pytest.raises(ValidationError):
        LogSymptomInput(symptom="a", severity=3)

    # Severity out of range (> 5)
    with pytest.raises(ValidationError):
        LogSymptomInput(symptom="Fever", severity=10)

    # Missing required scheduled_for in booking
    with pytest.raises(ValidationError):
        BookServiceInput(service=Service.DOCTOR, subtype=Subtype.CARDIOLOGY)  # type: ignore


@pytest.mark.asyncio
async def test_tool_unexpected_exception_returns_clean_apology():
    """An unexpected internal exception is caught, logged, and returns a clean user message."""
    with patch("app.tools.api.book_service", side_effect=RuntimeError("Simulated unexpected disk failure")):
        result_msg = await langchain_tools.book_service.ainvoke(
            {
                "service": Service.DOCTOR,
                "subtype": Subtype.GENERAL_PHYSICIAN,
                "scheduled_for": datetime(2027, 1, 12, 10, 0, tzinfo=KOLKATA_TZ),
                "patient_id": "pat_001",
                "request_id": str(uuid.uuid4()),
            }
        )
        assert "Simulated unexpected disk failure" not in result_msg
        assert "unexpected error occurred" in result_msg.lower()
