"""Append-only JSONL audit records for tool calls."""

from __future__ import annotations

import fcntl
import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)
_WRITE_LOCK = threading.Lock()
_SENSITIVE_KEYS = {"document_text", "document_content", "secret", "token", "password", "api_key"}


def _sanitize(value: Any, key: str = "") -> Any:
    """Redact secrets and large/free-text document values before persistence."""
    normalized_key = key.casefold()
    if any(marker in normalized_key for marker in _SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): _sanitize(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def append_tool_event(
    *,
    human_role: str,
    agent_name: str,
    tool_name: str,
    arguments: dict[str, Any],
    outcome: str,
    correlation_id: str,
    detail: str = "",
    iam_role_arn: str = "",
    aws_error_code: str = "",
    aws_request_id: str = "",
) -> dict[str, Any]:
    """Append one sanitized tool-call event and return the UI-safe event record."""
    if outcome not in {"allowed", "denied", "error", "not_configured"}:
        raise ValueError("outcome must be allowed, denied, error, or not_configured")
    record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "human_role": human_role,
        "agent_name": agent_name,
        "tool": tool_name,
        "arguments": _sanitize(arguments),
        "outcome": outcome,
        "correlation_id": correlation_id,
        "detail": detail[:500],
        "iam_role_arn": iam_role_arn[:256],
        "aws_error_code": aws_error_code[:100],
        "aws_request_id": aws_request_id[:100],
    }
    path: Path = settings.audit_log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with _WRITE_LOCK, path.open("a", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    logger.info(
        "tool_call_audited",
        extra={"agent_name": agent_name, "tool": tool_name, "outcome": outcome, "correlation_id": correlation_id},
    )
    return record
