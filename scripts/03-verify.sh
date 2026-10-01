#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

for r in demo-document-agent demo-screening-agent demo-registration-agent; do
  printf "Assuming %s ... " "$r"
  aws sts assume-role \
    --role-arn "arn:aws:iam::${ACCOUNT_ID}:role/${r}" \
    --role-session-name "verify-${r}" \
    --tags Key=HumanRole,Value="Sales Agent" \
    --query 'Credentials.Expiration' --output text
done
echo "All roles assumable"