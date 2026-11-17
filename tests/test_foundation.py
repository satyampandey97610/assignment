"""Tests for foundation phase: schema, constraints, seed data, and slot calculation."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text

from app.db import get_db_session
from app.enums import Weekday
from app.repo.slots import (
    compute_window_slots,
    get_weekday,
    is_on_slot_grid,
)

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_eight_tables_exist():
    expected_tables = {
        "societies",
        "patients",
        "clinicians",
        "service_requests",
        "symptom_logs",
        "escalations",
        "documents",
        "doc_chunks",
    }
    async with get_db_session() as session:
        res = await session.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
        )
        existing = {r[0] for r in res.fetchall()}
        assert expected_tables.issubset(existing), f"Missing tables: {expected_tables - existing}"


@pytest.mark.asyncio
async def test_seed_counts():
    async with get_db_session() as session:
        soc_cnt = (await session.execute(text("SELECT count(*) FROM societies"))).scalar()
        cln_cnt = (await session.execute(text("SELECT count(*) FROM clinicians"))).scalar()
        pat_cnt = (await session.execute(text("SELECT count(*) FROM patients"))).scalar()

        assert soc_cnt == 3
        assert cln_cnt == 12
        assert pat_cnt == 20


def test_slot_computation_dr_khanna_example():
    """Verify Dr. Khanna (30 min) Tuesday 10:00-11:00 has exactly 10:00 and 10:30."""
    tuesday = date(2027, 1, 12)  # Tuesday
    assert get_weekday(tuesday) == Weekday.TUE

    slots = compute_window_slots(
        d=tuesday,
        start_time_str="10:00",
        end_time_str="11:00",
        slot_minutes=30,
        tz=KOLKATA_TZ,
    )
    assert len(slots) == 2
    assert slots[0] == datetime(2027, 1, 12, 10, 0, tzinfo=KOLKATA_TZ)
    assert slots[1] == datetime(2027, 1, 12, 10, 30, tzinfo=KOLKATA_TZ)


def test_is_on_slot_grid():
    availability = [
        {
            "society_id": "soc_shivalik",
            "weekday": "TUE",
            "start": "10:00",
            "end": "11:00",
        }
    ]
    # Valid slot start
    dt_valid = datetime(2027, 1, 12, 10, 30, tzinfo=KOLKATA_TZ)
    assert is_on_slot_grid(dt_valid, availability, 30, "soc_shivalik", KOLKATA_TZ) is True

    # Invalid slot start (10:15 is not on 30-min grid)
    dt_invalid_time = datetime(2027, 1, 12, 10, 15, tzinfo=KOLKATA_TZ)
    assert is_on_slot_grid(dt_invalid_time, availability, 30, "soc_shivalik", KOLKATA_TZ) is False

    # Invalid society
    assert is_on_slot_grid(dt_valid, availability, 30, "soc_lotus", KOLKATA_TZ) is False
