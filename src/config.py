"""Load project configuration once and expose typed settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _path_setting(name: str, default: str) -> Path:
    """Resolve a configured path relative to the project root when needed."""
    value = os.getenv(name, default).strip() or default
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed application configuration; blank AWS values remain valid at startup."""

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str
    aws_region: str
    bedrock_model_id: str
    bedrock_invoke_resource_arn: str
    iam_role_arn_document_agent: str
    iam_role_arn_screening_agent: str
    iam_role_arn_registration_agent: str
    restricted_action_lambda_arn: str
    data_dir: Path
    log_dir: Path
    audit_log_path: Path
    human_role: str

    def require(self, attribute: str, env_name: str) -> str:
        """Return a configured value or raise an actionable configuration error."""
        value = getattr(self, attribute)
        if not value:
            raise ConfigurationError(f"{env_name} is not set in .env")
        return value


class ConfigurationError(ValueError):
    """Raised when a feature is used before its required configuration is set."""


settings = Settings(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "").strip(),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "").strip(),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN", "").strip(),
    aws_region=os.getenv("AWS_REGION", "us-east-1").strip() or "us-east-1",
    bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "").strip(),
    bedrock_invoke_resource_arn=os.getenv("BEDROCK_INVOKE_RESOURCE_ARN", "").strip(),
    iam_role_arn_document_agent=os.getenv("IAM_ROLE_ARN_DOCUMENT_AGENT", "").strip(),
    iam_role_arn_screening_agent=os.getenv("IAM_ROLE_ARN_SCREENING_AGENT", "").strip(),
    iam_role_arn_registration_agent=os.getenv("IAM_ROLE_ARN_REGISTRATION_AGENT", "").strip(),
    restricted_action_lambda_arn=os.getenv("RESTRICTED_ACTION_LAMBDA_ARN", "").strip(),
    data_dir=_path_setting("DATA_DIR", "data"),
    log_dir=_path_setting("LOG_DIR", "logs"),
    audit_log_path=_path_setting("AUDIT_LOG_PATH", "logs/audit.jsonl"),
    human_role=os.getenv("HUMAN_ROLE", "Compliance Officer").strip() or "Compliance Officer",
)