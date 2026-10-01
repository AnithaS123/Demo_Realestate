"""Document specialist entry point and scoped tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.agents.specialist import run_specialist


def run_document_agent(
    prompt: str,
    human_role: str,
    correlation_id: str,
    on_event: Callable[[dict[str, Any]], None],
) -> str:
    """Run the Document Agent, which receives only profile and extraction tools."""
    return run_specialist("Document Agent", prompt, human_role, correlation_id, on_event)
