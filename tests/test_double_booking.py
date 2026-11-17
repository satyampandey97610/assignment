"""Test 1: Concurrent double-booking prevention enforced strictly by PostgreSQL."""

import asyncio
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from app import clock
from app.db import get_db_session
from app.models import ServiceRequest
from app.tools.api import book_service

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_concurrent_double_booking_ten_slots():
    """Two patients attempt to book the exact same slot concurrently across 10 rounds.

    Asserts the database rule:
    - Exactly one booking succeeds.
    - Exactly one booking is rejected with SLOT_TAKEN and nearest free slots.
    - Exactly one row exists in the database for that (clinician_id, scheduled_for).
    """
    # Find next upcoming Monday at least 2 weeks ahead
    now = clock.now(KOLKATA_TZ)
    days_ahead = (0 - now.weekday() + 7) % 7
    if days_ahead < 2:
        days_ahead += 7
    monday_1 = now.date() + timedelta(days=days_ahead)
    monday_2 = monday_1 + timedelta(days=7)

    # Dr. Meera Iyer (cln_01) on Mondays at Shivalik Greens: 09:00 - 11:00 (20 min slots)
    # Generate 10 distinct slots (5 on Monday 1, 5 on Monday 2)
    slot_times = [
        datetime(monday_1.year, monday_1.month, monday_1.day, 9, 0, tzinfo=KOLKATA_TZ),
        datetime(monday_1.year, monday_1.month, monday_1.day, 9, 20, tzinfo=KOLKATA_TZ),
        datetime(monday_1.year, monday_1.month, monday_1.day, 9, 40, tzinfo=KOLKATA_TZ),
        datetime(monday_1.year, monday_1.month, monday_1.day, 10, 0, tzinfo=KOLKATA_TZ),
        datetime(monday_1.year, monday_1.month, monday_1.day, 10, 20, tzinfo=KOLKATA_TZ),
        datetime(monday_2.year, monday_2.month, monday_2.day, 9, 0, tzinfo=KOLKATA_TZ),
        datetime(monday_2.year, monday_2.month, monday_2.day, 9, 20, tzinfo=KOLKATA_TZ),
        datetime(monday_2.year, monday_2.month, monday_2.day, 9, 40, tzinfo=KOLKATA_TZ),
        datetime(monday_2.year, monday_2.month, monday_2.day, 10, 0, tzinfo=KOLKATA_TZ),
        datetime(monday_2.year, monday_2.month, monday_2.day, 10, 20, tzinfo=KOLKATA_TZ),
    ]

    patient_a = "pat_001"  # Shivalik Greens resident
    patient_b = "pat_002"  # Shivalik Greens resident

    for round_idx, slot in enumerate(slot_times, start=1):
        barrier = asyncio.Barrier(2)

        async def book_attempt(patient_id: str, b=barrier, s=slot):
            await b.wait()
            return await book_service(
                patient_id=patient_id,
                service="DOCTOR",
                subtype="GENERAL_PHYSICIAN",
                scheduled_for=s,
                request_id=uuid.uuid4(),
            )

        res_a, res_b = await asyncio.gather(
            book_attempt(patient_a),
            book_attempt(patient_b),
        )

        results = [res_a, res_b]
        successes = [r for r in results if r.get("ok") is True]
        failures = [r for r in results if r.get("ok") is False]

        assert len(successes) == 1, f"Round {round_idx}: expected 1 success, got {len(successes)}"
        assert len(failures) == 1, f"Round {round_idx}: expected 1 failure, got {len(failures)}"

        loser = failures[0]
        assert loser.get("error_code") == "SLOT_TAKEN"
        assert "nearest_free_slots" in loser
        assert len(loser["nearest_free_slots"]) > 0

        # Verify DB row count for this clinician and slot
        async with get_db_session() as session:
            stmt = select(ServiceRequest).where(
                ServiceRequest.clinician_id == "cln_01",
                ServiceRequest.scheduled_for == slot,
                ServiceRequest.status == "CONFIRMED",
            )
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 1, f"Round {round_idx}: expected 1 active DB row, found {len(rows)}"
