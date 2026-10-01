#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Checking AWS CLI..."
command -v aws >/dev/null || { echo "FAIL: aws CLI not installed"; exit 1; }

echo "Checking credentials..."
CALLER=$(aws sts get-caller-identity --query Arn --output text)
echo "  $CALLER"
case "$CALLER" in
  *:root) echo "FAIL: using root account. Create an IAM user."; exit 1;;
esac

BEDROCK_MODEL_ID_VALUE="$(python3 -c 'from dotenv import dotenv_values; print((dotenv_values(".env").get("BEDROCK_MODEL_ID") or "").strip())')"
if [[ -z "$BEDROCK_MODEL_ID_VALUE" ]]; then
  echo "INFO: BEDROCK_MODEL_ID is blank in .env; skipping Bedrock smoke test."
  exit 0
fi

echo "Checking Bedrock model access..."
aws bedrock-runtime converse \
  --model-id "$BEDROCK_MODEL_ID_VALUE" \
  --messages '[{"role":"user","content":[{"text":"hi"}]}]' \
  --query 'output.message.content[0].text' --output text >/dev/null \
  || { echo "FAIL: Bedrock not reachable with configured model. Check Region, model access, and IAM."; exit 1; }

echo "All prerequisites OK"