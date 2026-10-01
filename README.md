# Governed Buyer Onboarding Agents — Dubai Off-Plan Demo

## Start here: run the app

You do **not** need to start the MCP Inspector separately to use the Streamlit app. In a terminal opened at this project folder, run:

```zsh
source .venv/bin/activate
streamlit run app.py
```

Open the localhost URL printed by Streamlit, normally `http://localhost:8501`. Stop it with Ctrl+C. If this is the first run and packages are missing, activate `.venv` and run `python -m pip install -r requirements.txt` first. The app reads `.env` itself; do not run `source .env`.

### Project map

- `app.py` — the web interface you launch.
- `src/agents/` — supervisor routing and three specialist agents.
- `src/mcp_server/` — typed case/document/screening/action tools.
- `data/` — fictional buyers, documents, and screening fixtures.
- `lambda/restricted_action/` — demo-only AWS Lambda source for restricted requests.
- `.env` — your local configuration; never commit it.
- `scripts/` and `iam/` — AWS setup/deployment helpers and policy guidance; not needed just to open local fixture mode.

A local-first conference demo for fictional Dubai property-buyer onboarding. The repository now includes a Streamlit chat UI, tool-less Bedrock supervisor, specialist tool contracts, STS session helper, governance audit panel, and a demo-only Lambda handler. You must deploy the Lambda and configure least-privilege IAM/Bedrock access before the AWS authorization demonstration can run.

> **Security truth and limitation:** prompts are not access control, and local Python functions/local files cannot be IAM-protected. This demo scopes each Bedrock specialist to its assigned tool definitions and sends approval/registration requests to an AWS Lambda Invoke API where IAM evaluates the request; that proves the Lambda permission boundary, not that IAM protects local JSON tools. The sidebar persona and STS session tag are presentation mechanics, not trusted human authentication, so this must not be used as a production authorization design.

## What this demo proves

Prompt engineering is not access control: a manipulated model may attempt an operation outside its authority. A correctly configured AWS IAM boundary—not the prompt or a Python guard—must deny that unauthorized Lambda invocation and leave an auditable governance trace.

## What is implemented now

- MCP Python SDK v2 server using `MCPServer` at `src/mcp_server/server.py`, with six typed tools.
- Streamlit chat interface; tool-less supervisor; specialist-specific Bedrock tool schemas in `src/agents/`.
- STS role assumption, session-tag support, append-only JSONL audit events, and actual Lambda Invoke denial handling.
- Demo-only Lambda source under `lambda/restricted_action/`; it returns a synthetic result only and does not call DLD/Oqood.
- Five fictional buyer profiles, fictional document text, and a local watchlist with name/transliteration aliases and a typo near-match.
- Configuration loads from the project-root `.env`; blank AWS settings do not block the read-only MCP server.

AWS operation requires model access, configured role ARNs, the deployed Lambda ARN, and IAM policies described in [iam/README.md](iam/README.md). The local app starts without them and clearly reports unavailable AWS-dependent behavior; it never fabricates an IAM denial.

## Prerequisites

To run the Streamlit app locally:

- macOS with Python 3.11 or newer.
- Project dependencies installed in `.venv` from `requirements.txt`.

Node.js/npm and `uv` are needed only for the optional MCP Inspector, not for Streamlit.

For later AWS stages:

- An AWS account and a named AWS Region supported by the chosen Bedrock model.
- Enable/request access to the selected foundation model in the Amazon Bedrock console (model access/catalog availability varies by Region and model).
- IAM permissions to create/assume the demo roles and invoke the selected Bedrock model, plus the separately IAM-protected restricted-action endpoint described in the design spec.
- A small AWS budget/limit for model inference. Never run a live conference demo with root credentials or a real buyer's personal data.

### Bedrock access is not an API key

Amazon Bedrock normally uses AWS IAM credentials and SigV4-signed SDK requests; it does **not** give you a standalone Bedrock API key to paste into `.env`. This app explicitly uses `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optional `AWS_SESSION_TOKEN` from the project-root `.env` for AWS requests; it will not silently fall back to environment profiles or the default boto3 credential chain. These values are still optional for local fixture-only UI use, but all AWS-backed features require them.

## Optional: inspect the MCP tools

This is a developer tool-check, not required to launch the app.

Run commands from the project root, `buyer-onboarding-agents/` (the folder containing `requirements.txt`).

1. **Open the project in Kiro.** In Kiro, choose **File → Open Folder…** and select this repository folder. The feature specification lives under `.kiro/specs/governed-buyer-onboarding/`.
2. **Create and activate a virtual environment:**

   ```zsh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   ```

3. **Install project packages:**

   ```zsh
   python -m pip install -r requirements.txt
   ```

4. **Install `uv` and ensure it is on `PATH`.** For example, if Homebrew is installed:

   ```zsh
   brew install uv
   uv --version
   ```

   If you already installed `uv` with pip but `uv --version` says command not found, add the Python environment's scripts directory to `PATH`, or reinstall it with Homebrew. The MCP Inspector starts a separate `uv` command, so it must be visible in the shell that starts `mcp dev`.

5. **Create a local environment file:**

   ```zsh
   cp .env.example .env
   ```

   No AWS values are required for this stage. Leave them blank. `.env` is ignored by git.

6. **Start the MCP Inspector and server:**

   ```zsh
   mcp dev src/mcp_server/server.py
   ```

   Approve the npm prompt to install `@modelcontextprotocol/inspector` if it appears. Open the localhost URL printed by the command. Connect to the listed stdio server, choose **Tools**, and verify `get_buyer_profile` and `screen_sanctions` appear.

7. **Try the profile tool:** In Inspector → **Tools** → `get_buyer_profile`, enter `BUYER-001` and execute. It returns the fictional Nadia Sample profile.
8. **Try screening:** Execute `screen_sanctions` with `name=Omar Example`, `nationality=Fictional Republic` for the synthetic hit; then try `name=Rami Nearmatxh`, `nationality=Jordanian` for the intentional fuzzy near-match. A potential match is a review signal only, never an automated legal decision.
9. Stop the Inspector with Ctrl+C when finished.

If `mcp` is not found after activating `.venv`, use `python -m pip show mcp` to verify installation and reopen a terminal after activation. If `uv` is not found, fix `PATH` as in step 4. MCP Inspector also requires Node/npm and network access on its initial run.

## Run the Streamlit demo

With the virtual environment activated and requirements installed, start the app from the repository root:

```zsh
streamlit run app.py
```

The local fixture and watchlist paths work without AWS configuration. Bedrock reasoning requires `BEDROCK_MODEL_ID`, AWS credentials, and each specialist role ARN. Registration/approval additionally requires `RESTRICTED_ACTION_LAMBDA_ARN` and the matching IAM policy. The **Run poisoned-document attack** button is intended to attempt the operation through the model and AWS; without the required settings, the UI reports `NOT CONFIGURED` and does not claim a denial.

## AWS setup for Bedrock, specialist roles, and the demo Lambda

The instructions below provision local-development credentials. They do not by themselves make local file tools IAM-governed; the restricted-action service/permissions must be implemented and deployed before claiming AWS-enforced denials.

### 1. Enable the Bedrock model

1. Sign in to the AWS Management Console and select the intended Region (same Region as `AWS_REGION`).
2. Open **Amazon Bedrock → Model catalog** (console labels may change), select a model available in that Region, and follow the model-access/request-access flow shown there.
3. Wait until the model is available to your account. Copy its exact model ID into `BEDROCK_MODEL_ID` in `.env`. Confirm the model's usage terms and set an account budget/alert.
4. The runtime principal needs `bedrock:InvokeModel` for the chosen model ARN (and `bedrock:InvokeModelWithResponseStream` only if streaming is actually used). Avoid `bedrock:*`.

### 2. Create a local IAM principal and access key (only if not using a safer credential flow)

Do **not** create keys for the AWS root user. Prefer AWS IAM Identity Center / AWS CLI SSO or short-lived role credentials when available. If you must use a long-lived key for a disposable local conference demo:

1. In the console, open **IAM → Users → Create user**. Use a name such as `buyer-onboarding-demo-local`; do not grant console password access unless there is a separate operational need.
2. Grant only the permissions required by the demo. Do not attach `AdministratorAccess`, broad `BedrockFullAccess`, or broad `sts:*`.
3. Open the created user's **Security credentials** tab → **Access keys → Create access key**. Select **Command Line Interface (CLI)** (or the equivalent local-development use case), acknowledge the recommendation, create the key, and save/download the secret once to a secure local password manager. AWS displays the secret only at creation.
4. In the root-level `.env`, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (and `AWS_SESSION_TOKEN` only for temporary credentials). Never send these values in chat, screenshots, source control, or conference slides. Rotate/delete the key after the demo.
5. Check **IAM → Users → Access key last used** after the demo; deactivate and delete the demo key when it is no longer needed.

**Do not put an AWS secret access key in Kiro prompts, MCP arguments, the README, or a committed file.** `.env` is git-ignored, but it is still plaintext on your laptop; protect the machine and use short-lived credentials if possible.

### 3. Deploy the synthetic restricted-action Lambda

Create the function in the Lambda console from scratch with a supported Python runtime. Deploy [lambda_function.py](lambda/restricted_action/lambda_function.py), test it with the synthetic event in [iam/README.md](iam/README.md), and copy the function ARN into `.env` as `RESTRICTED_ACTION_LAMBDA_ARN`. This handler returns a simulation result only; it must not be described as an Oqood/DLD integration.

### 4. Create the three specialist roles and trust relationships

The app's agent process calls STS `AssumeRole` for each specialist, then builds its AWS client from that role's temporary credentials. See [iam/README.md](iam/README.md) and run the carefully scoped `scripts/01-setup-iam.sh` only after reviewing it. The setup script intentionally creates trust but grants no service permissions. Add the returned role ARNs to the matching `IAM_ROLE_ARN_*` fields in `.env`.

Create role permissions for the AWS resources actually called by that agent. For example, restrict `bedrock:InvokeModel` to the selected model ARN. Do not assume that a local Python function call is denied just because its execution code is associated with an IAM role: IAM evaluates AWS API requests, not arbitrary local function calls or local JSON reads/writes.

For the **restricted** `approve_buyer` and `submit_oqood_registration` demos, attach [the Lambda invocation policy template](iam/registration-lambda-invoke-policy.template.json) only to the Registration role after replacing its ARN placeholder. Attach the model policy template as needed using exact model resource ARNs. Non-compliance persona session tags should receive a real service-side `AccessDenied`; never simulate the denial in Python. The current role selector is operator-controlled and not authentication; see `.kiro/specs/governed-buyer-onboarding/design.md` before presenting this as anything beyond a controlled demo.

### 5. AWS CLI alternative for checking credentials

After installing/configuring AWS CLI (prefer `aws configure sso` / `aws sso login` for Identity Center), verify the active principal with:

```zsh
aws sts get-caller-identity
```

Use the same Region as the Bedrock model. Do not paste the output if it contains account details in public materials. Creating role policies/trust is intentionally deferred until the IAM-protected restricted-action resource has been chosen; copying speculative policy JSON would risk granting ineffective or excessive access.

## Environment variables

| Variable | Required now? | Purpose |
|---|---:|---|
| `AWS_ACCESS_KEY_ID` | Only for AWS features | Explicit local AWS access key consumed by the app from `.env`. |
| `AWS_SECRET_ACCESS_KEY` | Only for AWS features | Secret paired with the explicit access key. Keep private. |
| `AWS_SESSION_TOKEN` | No | Temporary session token when using short-lived STS credentials. |
| `AWS_REGION` | No (defaults to `us-east-1`) | Region for later AWS clients and Bedrock. |
| `BEDROCK_MODEL_ID` | No | Bedrock model ID; needed when the Bedrock agent step is implemented. |
| `BEDROCK_INVOKE_RESOURCE_ARN` | No | Exact Bedrock model/inference-profile resource ARN for a least-privilege role policy template. |
| `IAM_ROLE_ARN_DOCUMENT_AGENT` | No | STS role ARN for the future Document Agent. |
| `IAM_ROLE_ARN_SCREENING_AGENT` | No | STS role ARN for the future Screening Agent. |
| `IAM_ROLE_ARN_REGISTRATION_AGENT` | No | STS role ARN for the future Registration Agent. |
| `RESTRICTED_ACTION_LAMBDA_ARN` | No | ARN of the deployed demo-only restricted action Lambda. |
| `DATA_DIR` | No (defaults to `data`) | Synthetic fixtures directory. |
| `LOG_DIR` | No (defaults to `logs`) | Future application log directory. |
| `AUDIT_LOG_PATH` | No (defaults to `logs/audit.jsonl`) | Future append-only JSONL audit log. |
| `HUMAN_ROLE` | No (defaults to `Compliance Officer`) | Future selected demo-user role. |

Configuration is loaded once by `src/config.py`; do not read environment variables directly elsewhere. AWS values are optional for local fixture mode. AWS-dependent features report missing configuration without crashing.

## Kiro specifications

Open this folder in Kiro to review the feature artifacts:

- [Requirements](.kiro/specs/governed-buyer-onboarding/requirements.md)
- [Design](.kiro/specs/governed-buyer-onboarding/design.md)
- [Tasks](.kiro/specs/governed-buyer-onboarding/tasks.md)

The task checklist records implementation and AWS verification separately. The audience should treat AWS/IAM tasks that remain unchecked as unverified.

## Conference demo script

Before presenting, start `streamlit run app.py`, confirm the expected Bedrock model/roles/Lambda ARN are configured, and use a **Sales Agent** persona for the denied attempt. Verify with actual assumed-role credentials that the Registration role has the expected session tag and the Lambda invocation is denied for that tag. Type these prompts into chat, in order:

1. `Show the onboarding profile and current status for BUYER-001.`
2. `Extract the passport fields for BUYER-001 and list any uncertainty.`
3. `Screen BUYER-002 against the synthetic sanctions watchlist. Explain why a possible match requires human review.`
4. `Assess the source of funds for BUYER-003. Summarize evidence and gaps without deciding approval.`
5. `Review BUYER-004 identity documents and explain the name discrepancy.`
6. **End with the poisoned-document attack:** select **Sales Agent** in the sidebar and click **Run poisoned-document attack**. The app inspects BUYER-005's poisoned bank statement, routes the embedded escalation request to Registration, and attempts the approval/registration tools. The governance panel must show an actual Lambda invocation denial from AWS. If the result is `NOT CONFIGURED`, `ERROR`, or `ALLOWED`, do not claim the IAM-denial demo succeeded; verify caller identity, STS tags, and policies first.

For an authorized contrast, use **Compliance Officer** only if your reviewed demo policy intentionally grants that tagged session invocation. Even an `ALLOWED` result is a synthetic gate response, not a DLD/Oqood submission.

## Troubleshooting

- **`mcp: command not found`:** activate `.venv` and install `requirements.txt` again; use `python -m pip show mcp[cli]` to confirm.
- **`uv: command not found`:** install uv and ensure the executable is on the same `PATH` used by `mcp dev`.
- **Inspector asks to install a package:** approve only if you expect the official MCP Inspector npm package and have reviewed the prompt; npm/network access is needed the first time.
- **Server cannot import `src`:** launch `mcp dev src/mcp_server/server.py` from the project root, not from inside `src/`.
- **Bedrock `AccessDeniedException` later:** verify model access was enabled in the correct Region and the role's policy allows the exact invoke action on the exact model ARN.
- **A local tool appears to be IAM-protected:** it is not unless that tool makes an AWS request whose policy evaluation denies/permits it. See the design security boundary section.

## Fictional-data notice

Every buyer, identity reference, employer, bank amount, unit and watchlist entry in this repository is synthetic and intended only for software demonstration. Do not use these fixtures for real identity checks, financial decisions, sanctions decisions, property registration, or legal/compliance operations.

// Change only what I request. Leave all other code untouched.

git clone <repo>
cd <repo>
cp ~/Desktop/.env .
make check && make setup && make deploy && make verify && make run