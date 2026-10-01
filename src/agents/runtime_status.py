"""Best-effort per-session status for AWS calls shown in the Streamlit sidebar."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _streamlit_session_state() -> Any | None:
    """Return Streamlit session state when running under the app, otherwise None."""
    try:
        import streamlit as st

        return st.session_state
    except Exception:
        return None


def mark_bedrock_success(model_id: str) -> None:
    """Remember that a Bedrock inference request succeeded in this UI session."""
    state = _streamlit_session_state()
    if state is not None:
        state["bedrock_verified_model_id"] = model_id
        state["bedrock_verified"] = True
    logger.info("Bedrock invocation verified for configured model %s", model_id)


def mark_lambda_attempt(outcome: str, message: str = "") -> None:
    """Remember the result of an actual Lambda Invoke API attempt."""
    state = _streamlit_session_state()
    if state is not None:
        state["lambda_invoke_attempted"] = True
        state["lambda_invoke_outcome"] = outcome
        state["lambda_invoke_message"] = message[:300]
    logger.info("Restricted Lambda invocation attempted; outcome=%s", outcome)