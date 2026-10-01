#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v aws >/dev/null || { echo "ERROR: AWS CLI v2 is required." >&2; exit 1; }
: "${IAM_USER_NAME:?Export IAM_USER_NAME to the existing demo IAM user name. Do not use root.}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
CALLER_ARN="$(aws sts get-caller-identity --query Arn --output text)"
case "$CALLER_ARN" in *:root) echo "ERROR: Refusing to configure roles while authenticated as root." >&2; exit 1;; esac

mkdir -p iam
cat > iam/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::${ACCOUNT_ID}:user/${IAM_USER_NAME}"},
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {
      "ForAllValues:StringEquals": {"aws:TagKeys": ["HumanRole"]},
      "StringEquals": {"aws:RequestTag/HumanRole": ["Buyer", "Sales Agent", "Compliance Officer"]}
    }
  }]
}
EOF

cat > iam/assume-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {
      "ForAllValues:StringEquals": {"aws:TagKeys": ["HumanRole"]},
      "StringEquals": {"aws:RequestTag/HumanRole": ["Buyer", "Sales Agent", "Compliance Officer"]}
    },
    "Resource": [
      "arn:aws:iam::${ACCOUNT_ID}:role/demo-document-agent",
      "arn:aws:iam::${ACCOUNT_ID}:role/demo-screening-agent",
      "arn:aws:iam::${ACCOUNT_ID}:role/demo-registration-agent"
    ]
  }]
}
EOF

for role in demo-document-agent demo-screening-agent demo-registration-agent; do
  if aws iam get-role --role-name "$role" >/dev/null 2>&1; then
    echo "Updating trust for $role"
    aws iam update-assume-role-policy --role-name "$role" --policy-document file://iam/trust-policy.json >/dev/null
  else
    echo "Creating $role"
    aws iam create-role \
      --role-name "$role" \
      --assume-role-policy-document file://iam/trust-policy.json \
      --description "Buyer onboarding demo specialist role; attach only ARN-scoped policies" \
      --max-session-duration 3600 >/dev/null
  fi
done

aws iam put-user-policy \
  --user-name "$IAM_USER_NAME" \
  --policy-name AssumeBuyerOnboardingRoles \
  --policy-document file://iam/assume-policy.json

cat <<EOF

Created/updated three specialist roles. No service permissions were granted.
Account: ${ACCOUNT_ID}
Role ARNs:
  arn:aws:iam::${ACCOUNT_ID}:role/demo-document-agent
  arn:aws:iam::${ACCOUNT_ID}:role/demo-screening-agent
  arn:aws:iam::${ACCOUNT_ID}:role/demo-registration-agent

Next: review iam/README.md, add exact Bedrock resource permissions, and attach
registration invoke permission only to the Registration role. Session tags are
for this local presentation only; the persona dropdown is not authentication.
EOF
