"""Test scoping: proof that cross-society bookings and documents are unreachable."""

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app import clock
from app.db import get_db_session
from app.repo import scoped
from app.tools.api import book_service, list_service_requests

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_patient_cannot_read_another_societys_bookings():
    """Verify that bookings belonging to soc_lotus are invisible to soc_shivalik residents."""
    # Book a consultation for pat_010 (Lotus Tower, soc_lotus)
    now = clock.now(KOLKATA_TZ)
    # Dr. Prakash Nair (cln_08) is at Lotus Tower on Wednesday 10:00-11:00
    days_ahead = (2 - now.weekday() + 7) % 7
    if days_ahead < 2:
        days_ahead += 7
    wednesday = now.date() + timedelta(days=days_ahead)
    slot_time = datetime(wednesday.year, wednesday.month, wednesday.day, 10, 0, tzinfo=KOLKATA_TZ)

    lotus_patient = "pat_010"
    lotus_req_id = uuid.uuid4()

    booking = await book_service(
        patient_id=lotus_patient,
        service="DOCTOR",
        subtype="GENERAL_PHYSICIAN",
        scheduled_for=slot_time,
        request_id=lotus_req_id,
    )
    assert booking["ok"] is True
    booking_id = uuid.UUID(booking["booking_id"])

    # 1. Scoped repo function: querying with soc_shivalik returns None
    async with get_db_session() as session:
        # Cross-society read by ID
        cross_read = await scoped.get_service_request_by_id(
            session,
            society_id="soc_shivalik",
            booking_id=booking_id,
        )
        assert cross_read is None, "Cross-society read by booking ID must return None"

        # Cross-society read by patient list
        cross_list = await scoped.list_patient_service_requests(
            session,
            society_id="soc_shivalik",
            patient_id=lotus_patient,
        )
        assert len(cross_list) == 0, "Querying Lotus patient under Shivalik society must return empty"

    # 2. Tool API: Shivalik patient (pat_001) listing bookings only sees their own
    shivalik_patient_bookings = await list_service_requests(patient_id="pat_001")
    for b in shivalik_patient_bookings:
        assert b["booking_id"] != str(booking_id)
        assert b["society_id"] == "soc_shivalik"


@pytest.mark.asyncio
async def test_document_scoping_query_isolation():
    """Verify that scoped document search strictly excludes other societies' annexes."""
    # A dummy embedding with 384 dimensions
    dummy_embedding = [0.0] * 384
    dummy_embedding[0] = 1.0

    async with get_db_session() as session:
        # Search scoped to soc_shivalik
        results = await scoped.search_clinic_docs_scoped(
            session,
            society_id="soc_shivalik",
            query_embedding=dummy_embedding,
            k=20,
        )
        for r in results:
            # Must not return lotus or royal annex docs
            assert r["doc_id"] not in {"annex-lotus-tower", "annex-royal-palms"}
