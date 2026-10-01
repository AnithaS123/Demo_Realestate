"""Local deployment source for a synthetic IAM-protected action-gate Lambda."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_ALLOWED_OPERATIONS = {"approve_buyer", "submit_oqood_registration"}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Validate a synthetic request and return a non-persistent demo response.

    AWS IAM authorizes invocation before this handler runs. This function does
    not authorize callers, persist approval state, or contact DLD/Oqood.
    """
    operation = event.get("operation")
    buyer_id = event.get("buyer_id")
    unit_id = event.get("unit_id")
    if operation not in _ALLOWED_OPERATIONS:
        return {"ok": False, "demo_only": True, "message": "Unsupported demo operation."}
    if not isinstance(buyer_id, str) or re.fullmatch(r"BUYER-[0-9]{3}", buyer_id) is None:
        return {"ok": False, "demo_only": True, "message": "Invalid synthetic buyer_id."}
    if operation == "submit_oqood_registration" and (
        not isinstance(unit_id, str) or re.fullmatch(r"UNIT-SIM-[0-9]{3}", unit_id) is None
    ):
        return {"ok": False, "demo_only": True, "message": "Invalid synthetic unit_id."}
    logger.info("Synthetic action gate accepted operation=%s buyer_id=%s", operation, buyer_id)
    return {
        "ok": True,
        "demo_only": True,
        "operation": operation,
        "buyer_id": buyer_id,
        "unit_id": unit_id,
        "message": "Synthetic action gate returned success; no approval was recorded and no DLD/Oqood request was sent.",
        "request_id": getattr(context, "aws_request_id", "local-test"),
    }
