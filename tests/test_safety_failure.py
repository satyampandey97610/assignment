"""Test 4: Safety classifier failure policy, timeout, regex fallback, and logging."""

import asyncio
import logging
from unittest.mock import AsyncMock, patch
import pytest

from app.enums import SafetyVerdict
from app.safety.classifier import classify_safety
from app.safety.templates import get_blocked_reply, get_emergency_reply


@pytest.mark.asyncio
async def test_classifier_provider_error_non_emergency_fails_closed(caplog):
    """When classifier provider fails on benign text, fail closed: log failure and block."""
    caplog.set_level(logging.WARNING)
    with patch("app.safety.classifier.execute_with_cache", side_effect=RuntimeError("Provider 500 error")):
        verdict, lang, safety_failed = await classify_safety(
            message="Can you book me a doctor for tomorrow?",
            patient_id="pat_001",
            request_id="req-12345",
        )

    assert safety_failed is True
    assert verdict == SafetyVerdict.SAFE

    # Assert structured failure log event
    failure_logs = [r for r in caplog.records if getattr(r, "event", None) == "safety_classifier_failure"]
    assert len(failure_logs) == 1
    assert "Provider 500 error" in failure_logs[0].extra_data["reason"]
    assert failure_logs[0].extra_data["patient_id"] == "pat_001"

    # User sees blocked template with 112
    blocked_reply = get_blocked_reply(lang, "+91 124 4000 1100")
    assert "112" in blocked_reply
    assert "can't process this right now" in blocked_reply.lower()


@pytest.mark.asyncio
async def test_classifier_timeout_with_emergency_regex_fallback(caplog):
    """When classifier times out on life-threatening emergency, regex fallback treats as EMERGENCY."""
    caplog.set_level(logging.WARNING)
    with patch("app.safety.classifier.execute_with_cache", side_effect=asyncio.TimeoutError()):
        verdict, lang, safety_failed = await classify_safety(
            message="My father collapsed on the floor and is unresponsive!",
            patient_id="pat_001",
            request_id="req-67890",
        )

    assert safety_failed is False
    assert verdict == SafetyVerdict.EMERGENCY

    # Assert failure was logged
    failure_logs = [r for r in caplog.records if getattr(r, "event", None) == "safety_classifier_failure"]
    assert len(failure_logs) == 1
    assert failure_logs[0].extra_data["reason"] == "timeout"

    # User sees emergency template
    emergency_reply = get_emergency_reply(lang, "+91 124 4000 1100")
    assert "112" in emergency_reply
    assert "5 minutes" in emergency_reply


@pytest.mark.asyncio
async def test_safety_regex_union_elevates_false_safe_verdict():
    """If classifier incorrectly says SAFE, regex match elevates verdict to EMERGENCY."""
    # Mock LLM returning SAFE for an acute chest pain message
    mock_llm_output = {"verdict": "SAFE", "language": "hinglish"}
    with patch("app.safety.classifier.execute_with_cache", new=AsyncMock(return_value=mock_llm_output)):
        verdict, lang, safety_failed = await classify_safety(
            message="Bhaiya seene mein bahut tez dard ho raha hai saans nahi aa rahi",
            patient_id="pat_001",
            request_id="req-union-test",
        )

    assert safety_failed is False
    assert verdict == SafetyVerdict.EMERGENCY
    assert lang == "hinglish"
