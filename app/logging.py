"""Structured JSON logging configuration and domain event loggers."""

import json
import logging
import sys
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            log_obj["event"] = record.event
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj.update(record.extra_data)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure care_concierge logger with JSON output to stdout."""
    app_logger = logging.getLogger("care_concierge")
    app_logger.setLevel(level.upper())
    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        app_logger.addHandler(handler)
    return app_logger


logger = setup_logging()


def log_safety_classifier_failure(reason: str, patient_id: str, request_id: str) -> None:
    """Log a structured safety_classifier_failure event."""
    extra = {
        "event": "safety_classifier_failure",
        "extra_data": {
            "reason": reason,
            "patient_id": patient_id,
            "request_id": str(request_id),
        },
    }
    logger.warning(
        f"Safety classifier failure for patient={patient_id} request={request_id}: {reason}",
        extra=extra,
    )


def log_suspected_prompt_injection(doc_id: str, heading_path: str, snippet: str) -> None:
    """Log a suspected prompt injection warning during ingestion."""
    extra = {
        "event": "suspected_prompt_injection",
        "extra_data": {
            "doc_id": doc_id,
            "heading_path": heading_path,
            "snippet": snippet[:100],
        },
    }
    logger.warning(
        f"Suspected prompt injection in doc={doc_id} heading={heading_path}",
        extra=extra,
    )
