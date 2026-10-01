"""Registration specialist entry point and restricted action tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.agents.specialist import run_specialist


def run_registration_agent(
    prompt: str,
    human_role: str,
    correlation_id: str,
    on_event: Callable[[dict[str, Any]], None],
) -> str:
    """Run the Registration Agent with only AWS-IAM-protected action tools."""
    return run_specialist("Registration Agent", prompt, human_role, correlation_id, on_event)
