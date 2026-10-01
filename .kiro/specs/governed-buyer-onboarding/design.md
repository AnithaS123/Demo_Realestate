# Design: Governed Buyer Onboarding Agents

## 1. Design goals

- Make the access-control point visible during a live conference walkthrough.
- Keep the UI and synthetic fixture processing local; use AWS only for Bedrock reasoning, STS, and the explicitly IAM-enforced restricted-operation boundary.
- Use separate least-privilege AWS roles per specialist, typed MCP tools, and an append-only local JSONL event log.
- Fail safely and explainably when optional AWS configuration is missing or AWS denies an operation.
- Be candid about which portions are simulated/local and which permissions AWS actually enforced.

## 2. Current implementation checkpoint

Implemented now:

- `src/config.py` loads the project-root `.env` once and exposes a frozen typed `Settings` object.
- `src/mcp_server/server.py` registers `get_buyer_profile` and `screen_sanctions` on an MCP SDK v2 `MCPServer`.
- `data/buyers/`, `data/documents/`, and `data/watchlist.json` contain synthetic fixture data.
- MCP Inspector and the in-process MCP client have verified the two current tools.

Not yet implemented: Streamlit UI, Bedrock calls, STS assumption, per-agent authorization, restricted tools, audit log, or an IAM-protected action service. Do not infer that role isolation or a denied Oqood operation currently works.

## 3. Target topology

```text
Human operator / demo persona
            │
            ▼
Streamlit single-page chat ── correlation ID + governance timeline
            │
            ▼
Tool-less Supervisor (Bedrock; intent routing only)
     ┌──────┼─────────────────────┐
     ▼      ▼                     ▼
Document  Screening            Registration
Agent    Agent                 Agent
Role A   Role B                Role C
     │       │                    │
     └───────┴── STS sessions ────┤
                                  ▼
                  IAM-protected registration action API
                  (actual AWS authorization decision)

Local JSON/text fixture files → local read-only case and document tools
Local audit JSONL → append-only demonstration event history
```

The supervisor chooses which specialist handles the request; it does not grant permission. Agent tool registration should be statically scoped to each specialist and backed by separate role credentials. Tool lists alone are not a security boundary: actions against AWS resources must also be denied by AWS IAM when a role is unauthorized.

## 4. Important security boundary and architecture decision

### Why local JSON alone cannot produce IAM denial

AWS IAM authorizes signed AWS API requests. It does not intercept a Python function call, a local filesystem read/write, or an MCP tool invocation that performs no AWS request. STS-assuming a role and then reading a local JSON file does not cause that file operation to be checked against the role's IAM policy. Consequently, implementing `approve_buyer()` as a local JSON write and showing a Python-generated "AccessDenied" would be a false security demonstration.

### Required design for true `AccessDenied`

Before implementing restricted `approve_buyer` / `submit_oqood_registration`, select and provision an actual IAM-authorized AWS service boundary. Candidate for this demo: a narrow, dedicated AWS API/Lambda action endpoint invoked with the specialist's assumed-role credentials. The registration role may receive only the exact invoke permission for that endpoint; the other specialist roles receive no such permission. The endpoint can accept the synthetic buyer/unit IDs and return a demo result without a database if persistence is not needed. An unauthorized call must be sent to AWS and its genuine `AccessDenied` returned. Keep ordinary profiles/documents and watchlist local JSON as required.

Decision is **pending implementation/provisioning**, not an assumed capability. If the requirement forbids every AWS service beyond Bedrock/STS, a real IAM denial for local-only registration cannot be achieved; revise the demo claim or permit an IAM-protected AWS action endpoint. Do not replace this with a local conditional, simulated exception, policy simulator result, or prompt refusal.

### Human role selector caveat

A public Streamlit dropdown cannot authenticate a human or safely grant Compliance privileges. For an isolated conference demo it may change a display persona and choose among test identities, but it must not be presented as production-grade authorization. A real system must bind the human to a trusted principal/claim (for example, authenticated AWS IAM Identity Center/federation) and let policy-controlled credentials establish which role can be assumed. Do not give the local app broad privilege and rely on the selector's value to constrain it.

## 5. Components and responsibilities

### `src/config.py`

- Loads `.env` from project root once via `python-dotenv`.
- Exposes typed values and a `require` method that names unset configuration variables.
- AWS settings remain optional at process startup; AWS-dependent call sites validate only the settings they use.
- No other module reads process environment directly.

### MCP server and tools

- Retain Stage-1 profile lookup and screening.
- Add document extraction and source-of-funds analysis as non-decision support; Bedrock output must be treated as untrusted and cite the supplied fictional evidence.
- Tool docstrings are the model-facing contract: state purpose, inputs, limits, output meaning, human-review expectations, and forbidden implications.
- Register per-agent tool subsets in the host/agent layer. The Supervisor receives no tools.
- Restricted tool handlers send a signed AWS request to the IAM-protected action endpoint; catch only known AWS authorization exceptions as clear denial results and log the event.

### Agent flow

1. Streamlit creates a random correlation ID for each user turn.
2. The Supervisor classifies the intent and returns a specialist route; no direct tools.
3. The assigned specialist receives only its tool definitions and its own STS role credentials.
4. MCP calls emit governance events with agent/tool/argument metadata and outcome.
5. Registration operations cross the protected AWS boundary. The source of an `AccessDenied` is AWS response metadata/error code, not a local rule.
6. The assistant summarizes evidence and uncertainty; only authorized human actions can trigger approval/registration.

The identity passed as `human_role` must be derived from a trusted auth context in real deployment. In the presentation-only local UI it is explicitly a demo persona and must not be used to grant privileged credentials.

### Append-only audit

- Store each event as one JSON object per line at `AUDIT_LOG_PATH`; create parent directories safely.
- Event fields: UTC ISO-8601 timestamp, role/persona, agent, tool, sanitized arguments, outcome, correlation ID, and AWS error code/request ID when available.
- Redact key/token values and avoid full document bodies. Use a file lock if concurrent Streamlit sessions could append at once.
- Append; never rewrite previous event records. Explain that a local file is tamperable by the machine owner and is not equivalent to a centrally protected production audit service.

### Streamlit UI

- One-page chat with a compact sidebar persona selector and synthetic buyer context.
- Each response contains a prominent expandable **Governance trace** with ordered agent/tool calls and text plus icon/badge `ALLOWED`/`DENIED`; status must remain understandable without color.
- Use readable conference-scale font, strong contrast, concise result summaries, and restrained tables.
- Configuration and AWS authorization errors appear as informational/status messages, not Python stack traces.

## 6. IAM / STS policy model

The eventual deployment documents these trust and permission relationships:

- Local caller: permission to assume only the necessary named demo roles. Do not give general `sts:*`.
- Each role trust policy: trust only the intended caller; optionally constrain `sts:ExternalId`, session tags, and role session duration where applicable.
- Document role: only required Bedrock inference and any AWS document service actions; no screening/registration invoke permission.
- Screening role: only required Bedrock inference and any screening service action; no document/registration permission.
- Registration role: only the registration API/Lambda invoke action and any narrowly required inference action; no unrelated roles/actions.
- Supervisor: no tool-execution role or side-effect permission.
- Human identity authorization: Compliance credentials must not be obtainable merely by changing a UI control.

Policy resources and AWS CLI commands depend on the actual endpoint ARN, model ID/ARN, account/region, role names, and trust principal. Generate least-privilege policies from the chosen AWS resource before documenting runnable policy JSON; never use wildcard resources as a shortcut.

## 7. Poisoned-document attack scenario

- The poisoned synthetic bank statement contains an instruction to treat the buyer as pre-cleared and submit registration.
- Document Agent extracts it only as document text/possible prompt injection; it cannot invoke registration tools.
- The Supervisor's route is explicit and tool-less. For the attack demonstration, an attempted escalated registration request is routed/forwarded as an attempted specialist operation, not accepted as authorization.
- Registration Agent issues the real protected API call under its own role. When the trusted caller is not authorized for registration, AWS returns `AccessDenied`; log and display `DENIED — AWS IAM` with the correlation ID.
- State in the final narrative that prompt manipulation did not grant permissions; it did not itself perform a real DLD/Oqood submission.

Tests must verify the tool boundary and actual AWS denial; an ordinary unit test that asserts a hand-raised exception is insufficient proof of IAM enforcement.

## 8. Error handling

- Missing setting: e.g. `BEDROCK_MODEL_ID is not set in .env`.
- AWS authorization denial: display concise `AccessDenied` information, preserve provider error code/request ID for audit where safe, do not show stack trace or credentials.
- Bedrock throttling/network/model errors: user-safe error and structured application log; do not silently substitute fabricated model output.
- Malformed/missing fixture: actionable fixture ID/path error with no path traversal.
- Screening uncertainty: report potential-match score and state human review required; no binary legal verdict.

## 9. Test and verification strategy

- Unit tests for path validation, fixture reads, normalization, exact screening hit, typo near-match, Unicode/transliteration, and empty result.
- MCP client tests for currently registered tools and their structured schemas/results.
- Config tests for blank AWS startup and exact missing-variable errors.
- Agent tests for tool ownership: Supervisor none; each specialist only its specified subset.
- Audit tests for append-only lines, required fields, correlation IDs, and secret/document redaction.
- AWS integration test in a dedicated test account: assume each role; call the protected operation as unauthorized roles and observe AWS `AccessDenied`; verify authorized test role permission is limited to the intended action. Keep integration tests opt-in and never require AWS for fixture-only local tests.
- Streamlit smoke test and a projector-size manual review before conference use.

## 10. Open decisions before AWS role-policy implementation

1. Choose and provision the real IAM-protected restricted action resource (API Gateway/Lambda or another IAM-authorized service). Confirm local-only operation restrictions permit this AWS endpoint.
2. Decide how demo personas map to test identities without implying that the dropdown authenticates users. Keep privileged credentials out of an untrusted client-controlled path.
3. Confirm model ID/Region and precise Bedrock actions.
4. Decide the policy and retention boundary for local audit JSONL and how arguments are sanitized.
