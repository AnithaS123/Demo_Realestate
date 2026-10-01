"""Create isolated AWS SDK sessions by assuming specialist roles."""

from __future__ import annotations

import re
import json
import logging
from typing import Literal

import boto3

from src.config import ConfigurationError, settings

AgentName = Literal["Document Agent", "Screening Agent", "Registration Agent"]
HUMAN_ROLE_TAG_KEY = "HumanRole"
logger = logging.getLogger(__name__)

_ROLE_SETTINGS: dict[str, tuple[str, str]] = {
    "Document Agent": ("iam_role_arn_document_agent", "IAM_ROLE_ARN_DOCUMENT_AGENT"),
    "Screening Agent": ("iam_role_arn_screening_agent", "IAM_ROLE_ARN_SCREENING_AGENT"),
    "Registration Agent": ("iam_role_arn_registration_agent", "IAM_ROLE_ARN_REGISTRATION_AGENT"),
}


def base_session() -> boto3.Session:
    """Create a boto3 session using only the explicit credentials loaded from `.env`."""
    access_key = settings.aws_access_key_id
    secret_key = settings.aws_secret_access_key
    if not access_key:
        raise ConfigurationError("AWS_ACCESS_KEY_ID is not set in .env")
    if not secret_key:
        raise ConfigurationError("AWS_SECRET_ACCESS_KEY is not set in .env")
    return boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=settings.aws_session_token or None,
        region_name=settings.aws_region,
    )


def get_caller_identity() -> dict[str, str]:
    """Return the AWS caller identity for the explicit `.env` credential session."""
    response = base_session().client("sts", region_name=settings.aws_region).get_caller_identity()
    identity = {
        "account": str(response.get("Account", "")),
        "arn": str(response.get("Arn", "")),
        "user_id": str(response.get("UserId", "")),
        "credential_source": ".env explicit credentials",
    }
    logger.info(
        "AWS caller identity resolved: account=%s arn=%s user_id=%s source=%s",
        identity["account"], identity["arn"], identity["user_id"], identity["credential_source"],
    )
    return identity


def assume_agent_session(
    agent_name: AgentName,
    human_role: str,
    correlation_id: str,
) -> boto3.Session:
    """Assume exactly one specialist role, passing a demo persona as an IAM session tag.

    The session tag lets IAM condition the Lambda invoke permission. In this local
    conference app the persona selector is operator-controlled, not authenticated;
    never treat this mechanism as production human authorization.
    """
    setting_attribute, env_name = _ROLE_SETTINGS[agent_name]
    role_arn = settings.require(setting_attribute, env_name)
    allowed_personas = {"Buyer", "Sales Agent", "Compliance Officer"}
    if human_role not in allowed_personas:
        raise ValueError("Human role must be Buyer, Sales Agent, or Compliance Officer")
    role_session_name = f"buyer-demo-{agent_name.split()[0].lower()}-{correlation_id[:8]}"
    tags = [{"Key": HUMAN_ROLE_TAG_KEY, "Value": human_role}]
    transitive_tag_keys = [HUMAN_ROLE_TAG_KEY]
    assume_parameters = {
        "RoleArn": role_arn,
        "RoleSessionName": role_session_name,
        "Tags": tags,
        "TransitiveTagKeys": transitive_tag_keys,
        "Policy": None,
        "PolicyArns": None,
    }
    logger.info("STS AssumeRole request parameters: %s", json.dumps(assume_parameters, sort_keys=True))
    sts = base_session().client("sts", region_name=settings.aws_region)
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=role_session_name,
        Tags=tags,
        TransitiveTagKeys=transitive_tag_keys,
    )
    credentials = response["Credentials"]
    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=settings.aws_region,
    )


def bedrock_text(session: boto3.Session, system_prompt: str, user_prompt: str) -> str:
    """Call Bedrock Converse and return concatenated text blocks."""
    model_id = settings.require("bedrock_model_id", "BEDROCK_MODEL_ID")
    client = session.client("bedrock-runtime", region_name=settings.aws_region)
    response = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 900, "temperature": 0.1},
    )
    content = response.get("output", {}).get("message", {}).get("content", [])
    return "\n".join(block["text"] for block in content if "text" in block).strip()
