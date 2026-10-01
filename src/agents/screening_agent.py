"""Screening specialist entry point and scoped tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.agents.specialist import run_specialist


def run_screening_agent(
    prompt: str,
    human_role: str,
    correlation_id: str,
    on_event: Callable[[dict[str, Any]], None],
) -> str:
    """Run the Screening Agent, which receives only screening and funds tools."""
    return run_specialist("Screening Agent", prompt, human_role, correlation_id, on_event)
