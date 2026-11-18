"""Record and replay caching layer for deterministic offline evaluations."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.config import settings

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "evals" / "cache"


def compute_cache_key(
    model_name: str,
    task_name: str,
    schema_name: str,
    messages: list[dict[str, Any]],
) -> str:
    """Compute deterministic SHA-256 hash key from LLM request arguments."""
    payload = {
        "model": model_name,
        "task_name": task_name,
        "schema_name": schema_name,
        "messages": messages,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_response(key: str) -> dict[str, Any] | None:
    """Retrieve cached response if available."""
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def write_cached_response(key: str, data: dict[str, Any]) -> None:
    """Save response to cache file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def execute_with_cache(
    task_name: str,
    schema_name: str,
    messages: list[dict[str, Any]],
    llm_callable,
) -> dict[str, Any]:
    """Execute structured LLM call with respect to LLM_MODE (live, record, replay)."""
    mode = settings.LLM_MODE
    model_name = f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}"
    key = compute_cache_key(model_name, task_name, schema_name, messages)

    if mode == "replay":
        cached = get_cached_response(key)
        if cached is not None:
            return cached
        raise RuntimeError(
            f"No cache entry for this message (task={task_name}, key={key[:8]}); "
            "run with an API key or 'make eval-record'."
        )

    # In record or live mode, invoke the actual callable
    result = await llm_callable()
    # Normalize result to dict
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = result
    else:
        data = {"result": result}

    if mode == "record":
        write_cached_response(key, data)

    return data
