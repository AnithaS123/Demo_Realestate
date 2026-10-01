#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Read only non-secret deploy settings from dotenv; never source .env as shell code.
AWS_REGION="$(python3 -c 'from dotenv import dotenv_values; print((dotenv_values(".env").get("AWS_REGION") or "us-east-1").strip())')"
BEDROCK_INVOKE_RESOURCE_ARN="$(python3 -c 'from dotenv import dotenv_values; print((dotenv_values(".env").get("BEDROCK_INVOKE_RESOURCE_ARN") or "").strip())')"
: "${BEDROCK_INVOKE_RESOURCE_ARN:?Set BEDROCK_INVOKE_RESOURCE_ARN in .env before deploying scoped Bedrock policies.}"
export AWS_REGION AWS_DEFAULT_REGION="$AWS_REGION"

FN="demo-oqood-registration-gate"
EXEC_ROLE="demo-lambda-exec-role"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${FN}"
AGENT_ROLES="demo-document-agent demo-screening-agent demo-registration-agent"

mkdir -p iam

# --- Lambda execution role ---
if ! aws iam get-role --role-name "$EXEC_ROLE" >/dev/null 2>&1; then
  echo "Creating Lambda execution role"
  aws iam create-role --role-name "$EXEC_ROLE" \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]
    }' >/dev/null
  aws iam attach-role-policy --role-name "$EXEC_ROLE" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  echo "Waiting for role propagation..."
  sleep 10
fi

# --- Deploy the Lambda with the handler at the ZIP root ---
rm -f function.zip
(cd lambda/restricted_action && zip -q -j ../../function.zip lambda_function.py)

if aws lambda get-function --function-name "$FN" >/dev/null 2>&1; then
  echo "Updating $FN"
  aws lambda update-function-code --function-name "$FN" \
    --zip-file fileb://function.zip --query 'FunctionArn' --output text
  aws lambda wait function-updated-v2 --function-name "$FN"
else
  echo "Creating $FN"
  aws lambda create-function --function-name "$FN" \
    --runtime python3.12 \
    --role "arn:aws:iam::${ACCOUNT_ID}:role/${EXEC_ROLE}" \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --query 'FunctionArn' --output text
  aws lambda wait function-active-v2 --function-name "$FN"
fi
rm -f function.zip

# --- Remove the over-broad policy ---
for r in $AGENT_ROLES; do
  aws iam detach-role-policy --role-name "$r" \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess 2>/dev/null || true
done

# --- Scoped Bedrock access for all three agent roles ---
cat > iam/bedrock-invoke.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "bedrock:InvokeModel",
    "Resource": [
      "${BEDROCK_INVOKE_RESOURCE_ARN}",
      "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
      "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
      "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0"
    ]
  }]
}
EOF

for r in $AGENT_ROLES; do
  aws iam put-role-policy --role-name "$r" \
    --policy-name BedrockInvoke \
    --policy-document file://iam/bedrock-invoke.json
done

# --- Lambda invoke: REGISTRATION ROLE ONLY. This absence is the demo. ---
cat > iam/lambda-invoke.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyIfPersonaTagIsNotComplianceOfficer",
    "Effect": "Deny",
    "Action": "lambda:InvokeFunction",
    "Resource": "${LAMBDA_ARN}",
    "Condition": {
      "StringNotEquals": {"aws:PrincipalTag/HumanRole": "Compliance Officer"}
    }
  }, {
    "Sid": "DenyIfPersonaTagIsMissing",
    "Effect": "Deny",
    "Action": "lambda:InvokeFunction",
    "Resource": "${LAMBDA_ARN}",
    "Condition": {
      "Null": {"aws:PrincipalTag/HumanRole": "true"}
    }
  }, {
    "Sid": "AllowCompliancePersonaToInvokeDemoGate",
    "Effect": "Allow",
    "Action": "lambda:InvokeFunction",
    "Resource": "${LAMBDA_ARN}",
    "Condition": {
      "StringEquals": {"aws:PrincipalTag/HumanRole": "Compliance Officer"}
    }
  }]
}
EOF

aws iam put-role-policy --role-name demo-registration-agent \
  --policy-name InvokeRestrictedAction \
  --policy-document file://iam/lambda-invoke.json

echo ""
echo "Paste into .env:"
echo "RESTRICTED_ACTION_LAMBDA_ARN=\"${LAMBDA_ARN}\""