"""Create isolated AWS SDK sessions by assuming specialist roles."""

from __future__ import annotations

import re
from typing import Literal

import boto3

from src.config import ConfigurationError, settings

AgentName = Literal["Document Agent", "Screening Agent", "Registration Agent"]

_ROLE_SETTINGS: dict[str, tuple[str, str]] = {
    "Document Agent": ("iam_role_arn_document_agent", "IAM_ROLE_ARN_DOCUMENT_AGENT"),
    "Screening Agent": ("iam_role_arn_screening_agent", "IAM_ROLE_ARN_SCREENING_AGENT"),
    "Registration Agent": ("iam_role_arn_registration_agent", "IAM_ROLE_ARN_REGISTRATION_AGENT"),
}


def base_session() -> boto3.Session:
    """Create a boto3 session from configured explicit keys or the AWS provider chain."""
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        return boto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token or None,
            region_name=settings.aws_region,
        )
    return boto3.Session(region_name=settings.aws_region)


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
    sts = base_session().client("sts", region_name=settings.aws_region)
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=f"buyer-demo-{agent_name.split()[0].lower()}-{correlation_id[:8]}",
        Tags=[{"Key": "HumanRole", "Value": human_role}],
        TransitiveTagKeys=["HumanRole"],
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
