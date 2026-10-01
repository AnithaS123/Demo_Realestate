"""Exercise the real Lambda IAM boundary using explicit .env credentials and STS tags."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.auth.roles import assume_agent_session, base_session
from src.config import ConfigurationError, settings

OPERATIONS: tuple[tuple[str, dict[str, str]], ...] = (
    ("approve_buyer", {"buyer_id": "BUYER-001", "unit_id": "UNIT-SIM-101"}),
    ("submit_oqood_registration", {"buyer_id": "BUYER-001", "unit_id": "UNIT-SIM-101"}),
)


def _invoke(role: str, operation: str, args: dict[str, str]) -> tuple[str, str]:
    """Assume Registration Agent with a persona tag and invoke the real Lambda API."""
    session = assume_agent_session(
        "Registration Agent",
        role,  # exact HumanRole value included in the STS AssumeRole Tags parameter
        str(uuid.uuid4()),
    )
    lambda_client = session.client("lambda", region_name=settings.aws_region)
    event: dict[str, Any] = {"operation": operation, **args}
    try:
        response = lambda_client.invoke(
            FunctionName=settings.require("restricted_action_lambda_arn", "RESTRICTED_ACTION_LAMBDA_ARN"),
            InvocationType="RequestResponse",
            Payload=json.dumps(event).encode("utf-8"),
        )
    except ClientError as error:
        code = str(error.response.get("Error", {}).get("Code", "Unknown"))
        if code in {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation"}:
            return "DENIED", f"AWS returned {code}: {error.response.get('Error', {}).get('Message', '')}"
        raise

    payload = json.loads(response["Payload"].read().decode("utf-8"))
    if response.get("FunctionError"):
        raise RuntimeError(f"Lambda executed but returned FunctionError: {payload}")
    if not payload.get("ok"):
        raise RuntimeError(f"Lambda returned a non-success result: {payload}")
    return "ALLOWED", f"Lambda returned demo-only success; request_id={response.get('ResponseMetadata', {}).get('RequestId', '')}"


def main() -> int:
    """Verify Buyer is IAM-denied and Compliance Officer reaches the synthetic Lambda."""
    try:
        caller = base_session().client("sts", region_name=settings.aws_region).get_caller_identity()
        print(f"Base caller: {caller.get('Arn', '<unknown>')} (credentials loaded explicitly from .env)")
        settings.require("restricted_action_lambda_arn", "RESTRICTED_ACTION_LAMBDA_ARN")
        failed = False
        for persona, expected in (("Buyer", "DENIED"), ("Compliance Officer", "ALLOWED")):
            for operation, arguments in OPERATIONS:
                outcome, detail = _invoke(persona, operation, arguments)
                passed = outcome == expected
                print(f"{'PASS' if passed else 'FAIL'} persona={persona!r} operation={operation}: {outcome} — {detail}")
                failed |= not passed
        return 1 if failed else 0
    except (ConfigurationError, ClientError, RuntimeError) as error:
        print(f"Verification could not complete: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
