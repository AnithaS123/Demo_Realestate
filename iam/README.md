# IAM policy and Lambda setup

These are policy templates, not deploy-ready policies until the placeholder ARNs are replaced and reviewed. Do not attach broad administrator or full Bedrock policies to the agent roles. `scripts/01-setup-iam.sh` creates/upgrades trust and assume-role setup but intentionally grants no AWS service permissions.

## Demo-only identity caveat

The local Streamlit persona is not authentication. This sample passes a `HumanRole` STS session tag, and IAM evaluates the tag before permitting Lambda invocation. Because the local operator controls the caller credentials and persona selector, they can request any permitted tag; this demonstrates AWS-side policy evaluation for those tagged sessions, but does not prove the human is authorized. Do not use this pattern as real authorization. A real deployment must derive trusted identity claims outside the UI and prevent callers from minting privileged session tags.

## Set up the Lambda function

1. In the Lambda console, create `demo-oqood-registration-gate` from scratch with a current Python runtime and a basic CloudWatch logging execution role.
2. Deploy the handler in `lambda/restricted_action/lambda_function.py`. This function validates fictional identifiers and returns a demo response; it does not persist approval or call DLD/Oqood.
3. Create a console test event such as `{"operation":"submit_oqood_registration","buyer_id":"BUYER-005","unit_id":"UNIT-SIM-518"}` and verify the synthetic response.
4. Copy the exact function ARN into `.env` as `RESTRICTED_ACTION_LAMBDA_ARN`.
5. Add no public function URL and no unauthenticated resource-based permission. For same-account calls, use caller-role identity policies.

## Grant the invoker permissions

The request goes through the Lambda `Invoke` API, which requires `lambda:InvokeFunction`. Attach `registration-lambda-invoke-policy.template.json` as an inline policy **only on `demo-registration-agent`** after replacing every `REPLACE_WITH_RESTRICTED_ACTION_LAMBDA_ARN` with the actual function ARN. The template has an explicit deny when the assumed-role session tag `HumanRole` is absent or is not `Compliance Officer`, then an allow when it matches. The Document and Screening roles must not receive Lambda invoke permission; remove any unrelated policies that would grant it.

This condition works only when the STS `AssumeRole` request contains the `HumanRole` tag, **both** the role trust policy and caller identity policy permit `sts:TagSession`, and the app passes `HumanRole=...`. `scripts/01-setup-iam.sh` configures these caller/trust permissions for all three roles. Confirm the policy in your own account; SCPs, permission boundaries, session policies, and resource policies can also affect evaluation. A Lambda console test executes as the console's identity and does **not** test this role boundary.

## Allow Bedrock narrowly

For each role that actually calls Bedrock, create a customer-managed/inline policy based on `bedrock-invoke-policy.template.json`. Replace the resource placeholder with the exact foundation-model or inference-profile ARN(s) required for the selected model and Region. Cross-Region inference profiles may require permissions for both the inference-profile ARN and its possible destination foundation models; follow the model's AWS documentation. Do not use `AmazonBedrockFullAccess` or `Resource: "*"` to make a failed policy work.

The Bedrock Converse runtime API uses the `bedrock:InvokeModel` IAM permission. Add streaming permission only if you later implement the streaming API.

## Run IAM setup and verification

From the repository root, configure AWS CLI with a non-root principal that can create/update IAM roles and user inline policy for this demo. Export the existing user name in your shell (not chat and not source code), then run:

```zsh
export IAM_USER_NAME=your-demo-iam-user
bash scripts/01-setup-iam.sh
bash scripts/03-verify.sh
```

Review every planned change before applying it in a shared AWS account. The setup script updates trust policies and an inline role-assumption policy. It deliberately does not attach Bedrock or Lambda permissions.

After policy attachment and Lambda deployment, run the focused end-to-end check from the repository root:

```zsh
python scripts/04-verify-registration-boundary.py
```

It assumes `demo-registration-agent` twice using the app's shared STS helper and sends the exact `HumanRole` tag. For both `approve_buyer` and `submit_oqood_registration`, Buyer must get AWS `AccessDenied` and Compliance Officer must get a real Lambda response. Do not use an IAM policy simulator as proof of a real request denial. Verify the actual Lambda Invoke API result and request/error ID.

The app and tools catch service-side `AccessDenied` from the Lambda Invoke API and show the denial in the governance panel. A local conditional, a tool list, a prompt refusal, or an exception manually raised by application code is not equivalent.

The app and tools catch service-side `AccessDenied` from the Lambda Invoke API and show the denial in the governance panel. A local conditional, a tool list, a prompt refusal, or an exception manually raised by application code is not equivalent.
