"""Idempotent seed data loader for societies, clinicians, and patients."""

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert

from app.db import get_db_session
from app.logging import logger
from app.models import Clinician, Patient, Society

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def load_json_file(filename: str) -> list[dict[str, Any]]:
    path = SEED_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_societies() -> int:
    societies_data = load_json_file("societies.json")
    rows = []
    for item in societies_data:
        h = item.get("hospital", {})
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "city": item["city"],
                "address": item["address"],
                "timezone": item.get("timezone", "Asia/Kolkata"),
                "annex_doc_id": item["annex_doc_id"],
                "hospital_name": h.get("name", ""),
                "hospital_address": h.get("address", ""),
                "hospital_front_desk_phone": h.get("front_desk_phone", ""),
                "hospital_emergency_phone": h.get("emergency_phone", ""),
            }
        )

    async with get_db_session() as session:
        for r in rows:
            stmt = insert(Society).values(**r)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Society.id],
                set_={
                    "name": stmt.excluded.name,
                    "city": stmt.excluded.city,
                    "address": stmt.excluded.address,
                    "timezone": stmt.excluded.timezone,
                    "annex_doc_id": stmt.excluded.annex_doc_id,
                    "hospital_name": stmt.excluded.hospital_name,
                    "hospital_address": stmt.excluded.hospital_address,
                    "hospital_front_desk_phone": stmt.excluded.hospital_front_desk_phone,
                    "hospital_emergency_phone": stmt.excluded.hospital_emergency_phone,
                },
            )
            await session.execute(stmt)
    logger.info(f"Seeded {len(rows)} societies.")
    return len(rows)


async def seed_clinicians() -> int:
    clinicians_data = load_json_file("clinicians.json")
    rows = []
    for item in clinicians_data:
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "title": item["title"],
                "service": item["service"],
                "subtypes": item["subtypes"],
                "hospital": item["hospital"],
                "slot_minutes": item["slot_minutes"],
                "availability": item["availability"],
            }
        )

    async with get_db_session() as session:
        for r in rows:
            stmt = insert(Clinician).values(**r)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Clinician.id],
                set_={
                    "name": stmt.excluded.name,
                    "title": stmt.excluded.title,
                    "service": stmt.excluded.service,
                    "subtypes": stmt.excluded.subtypes,
                    "hospital": stmt.excluded.hospital,
                    "slot_minutes": stmt.excluded.slot_minutes,
                    "availability": stmt.excluded.availability,
                },
            )
            await session.execute(stmt)
    logger.info(f"Seeded {len(rows)} clinicians.")
    return len(rows)


async def seed_patients() -> int:
    patients_data = load_json_file("patients.json")
    rows = []
    for item in patients_data:
        dob_raw = item.get("date_of_birth")
        dob = date.fromisoformat(dob_raw) if dob_raw else None
        rows.append(
            {
                "id": item["id"],
                "society_id": item["society_id"],
                "name": item["name"],
                "phone": item["phone"],
                "language": item["language"],
                "date_of_birth": dob,
                "gender": item.get("gender"),
                "flat": item.get("flat"),
            }
        )

    async with get_db_session() as session:
        for r in rows:
            stmt = insert(Patient).values(**r)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Patient.id],
                set_={
                    "society_id": stmt.excluded.society_id,
                    "name": stmt.excluded.name,
                    "phone": stmt.excluded.phone,
                    "language": stmt.excluded.language,
                    "date_of_birth": stmt.excluded.date_of_birth,
                    "gender": stmt.excluded.gender,
                    "flat": stmt.excluded.flat,
                },
            )
            await session.execute(stmt)
    logger.info(f"Seeded {len(rows)} patients.")
    return len(rows)


async def seed_all() -> None:
    """Idempotently seed societies, clinicians, and patients."""
    await seed_societies()
    await seed_clinicians()
    await seed_patients()


if __name__ == "__main__":
    asyncio.run(seed_all())
