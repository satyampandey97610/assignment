"""Scoped data access layer.

This is the ONLY module that reads service_requests or documents/doc_chunks
for patient-facing flows. Every query requires society_id in the WHERE clause.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ServiceRequest


async def list_patient_service_requests(
    session: AsyncSession,
    *,
    society_id: str,
    patient_id: str,
    status: str | None = None,
) -> list[ServiceRequest]:
    """List service requests for a specific patient scoped strictly to their society."""
    conditions = [
        ServiceRequest.society_id == society_id,
        ServiceRequest.patient_id == patient_id,
    ]
    if status is not None:
        conditions.append(ServiceRequest.status == status)

    stmt = select(ServiceRequest).where(and_(*conditions)).order_by(ServiceRequest.scheduled_for.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_service_request_by_id(
    session: AsyncSession,
    *,
    society_id: str,
    booking_id: uuid.UUID,
) -> ServiceRequest | None:
    """Retrieve a single service request by ID scoped to the society."""
    stmt = select(ServiceRequest).where(
        and_(
            ServiceRequest.society_id == society_id,
            ServiceRequest.id == booking_id,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_service_request_by_request_id(
    session: AsyncSession,
    *,
    society_id: str,
    request_id: uuid.UUID,
) -> ServiceRequest | None:
    """Retrieve a service request by its idempotent request_id scoped to the society."""
    stmt = select(ServiceRequest).where(
        and_(
            ServiceRequest.society_id == society_id,
            ServiceRequest.request_id == request_id,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_active_bookings_for_clinician(
    session: AsyncSession,
    *,
    society_id: str,
    clinician_id: str,
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
) -> list[ServiceRequest]:
    """Retrieve confirmed bookings for a clinician within a society and optional time range."""
    conditions = [
        ServiceRequest.society_id == society_id,
        ServiceRequest.clinician_id == clinician_id,
        ServiceRequest.status == "CONFIRMED",
    ]
    if start_dt is not None:
        conditions.append(ServiceRequest.scheduled_for >= start_dt)
    if end_dt is not None:
        conditions.append(ServiceRequest.scheduled_for <= end_dt)

    stmt = select(ServiceRequest).where(and_(*conditions))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_clinic_docs_scoped(
    session: AsyncSession,
    *,
    society_id: str,
    query_embedding: list[float],
    k: int = 6,
) -> list[dict[str, Any]]:
    """Dense vector search on doc_chunks scoped to active documents for society_id and 'all'."""
    vector_literal = f"[{','.join(str(x) for x in query_embedding)}]"
    sql = text(
        """
        SELECT d.doc_id, d.title, d.version, c.heading_path, c.content,
               1 - (c.embedding <=> :q::vector) AS score
        FROM doc_chunks c
        JOIN documents d ON d.doc_id = c.doc_id AND d.version = c.version
        WHERE d.is_current
          AND d.applies_to IN ('all', :society_id)
        ORDER BY c.embedding <=> :q::vector
        LIMIT :k;
        """
    )
    result = await session.execute(
        sql,
        {"q": vector_literal, "society_id": society_id, "k": k},
    )
    rows = result.mappings().all()
    return [
        {
            "doc_id": row["doc_id"],
            "title": row["title"],
            "version": row["version"],
            "heading_path": row["heading_path"],
            "content": row["content"],
            "score": float(row["score"]),
        }
        for row in rows
    ]
