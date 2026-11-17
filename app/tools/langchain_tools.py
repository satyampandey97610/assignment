"""LangChain @tool wrappers with state injection, error mapping, and validation."""

import json
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import ValidationError

from app.enums import BookingStatus, Service, Subtype
from app.logging import logger
from app.tools import api
from app.tools.schemas import BookServiceInput, ListServiceRequestsInput, LogSymptomInput


@tool(args_schema=BookServiceInput)
async def book_service(
    service: Service,
    subtype: Subtype,
    scheduled_for: datetime,
    patient_id: Annotated[str, InjectedState("patient_id")],
    request_id: Annotated[str, InjectedState("request_id")],
) -> str:
    """Book a doctor consultation or lab test against a clinician and slot."""
    try:
        res = await api.book_service(
            patient_id=patient_id,
            service=str(service),
            subtype=str(subtype),
            scheduled_for=scheduled_for,
            request_id=request_id,
        )
        return json.dumps(res, ensure_ascii=False)
    except ValidationError as val_err:
        return f"Invalid argument: {val_err}"
    except Exception as exc:
        logger.exception(f"Unexpected error in book_service tool: {exc}")
        return "I apologize, but an unexpected error occurred while booking. Please try again."


@tool(args_schema=ListServiceRequestsInput)
async def list_service_requests(
    status: BookingStatus | None = None,
    patient_id: Annotated[str, InjectedState("patient_id")] = "",
) -> str:
    """List existing doctor consultations and lab tests for the authenticated patient."""
    try:
        status_str = str(status) if status else None
        res = await api.list_service_requests(patient_id=patient_id, status=status_str)
        return json.dumps(res, ensure_ascii=False)
    except ValidationError as val_err:
        return f"Invalid argument: {val_err}"
    except Exception as exc:
        logger.exception(f"Unexpected error in list_service_requests tool: {exc}")
        return "I apologize, but an unexpected error occurred while listing your bookings."


@tool(args_schema=LogSymptomInput)
async def log_symptom(
    symptom: str,
    severity: int,
    patient_id: Annotated[str, InjectedState("patient_id")],
    request_id: Annotated[str, InjectedState("request_id")],
) -> str:
    """Log a symptom with severity 1-5 for clinical tracking."""
    try:
        res = await api.log_symptom(
            patient_id=patient_id,
            symptom=symptom,
            severity=severity,
            request_id=request_id,
        )
        return json.dumps(res, ensure_ascii=False)
    except ValidationError as val_err:
        return f"Invalid argument: {val_err}"
    except Exception as exc:
        logger.exception(f"Unexpected error in log_symptom tool: {exc}")
        return "I apologize, but an unexpected error occurred while logging your symptom."


TOOLS = [book_service, list_service_requests, log_symptom]
