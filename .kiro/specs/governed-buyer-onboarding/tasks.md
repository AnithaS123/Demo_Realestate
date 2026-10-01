# Implementation tasks: Governed Buyer Onboarding Agents

The checklist tracks implementation and live AWS verification separately. Local app/agent code is present; live AWS tasks remain unverified until the operator rotates exposed credentials, deploys the demo Lambda, and attaches reviewed least-privilege policies.

## Stage 1 — Read-only MCP tools ✅

- [x] Create typed, centralized `.env` config that tolerates blank AWS settings.
- [x] Implement MCP SDK v2 server with `MCPServer` and typed buyer/document/screening/funds/restricted-action tools.
- [x] Add five fictional buyer JSON profiles, synthetic watchlist, and fictional document text fixtures.
- [x] Add aliases, typo near-match, and transliteration-aware normalization.
- [x] Verify read-only tools and MCP catalog with an in-process MCP client and MCP Inspector.
- [x] Manually verify the read-only MCP tool catalog, profile lookup, watchlist hit, typo near-match, and transliteration variant.

## Stage 2 — Bedrock supervisor and tool-using agents

- [ ] Decide/configure the target Bedrock model and Region; add user-safe errors for missing `BEDROCK_MODEL_ID` and credentials.
- [x] Implement Bedrock Converse runtime creation from central config/AWS credential chain.
- [x] Implement tool-less supervisor and Bedrock tool-use loops with specialist-scoped tool schemas.
- [x] Add synthetic-ID/document-type validation and cap returned document context.
- [ ] Run live Bedrock prompt/tool calls with rotated credentials and verified model access.
- [ ] Manually smoke-check success, missing-config, model error, and malformed tool input paths; never present a mock as IAM proof.

## Stage 3 — IAM roles, STS, and a real denial (AWS)

- [ ] **Resolve design decisions first:** choose a real IAM-protected AWS boundary for restricted calls and a trusted identity source for compliance credentials.
- [ ] Write least-privilege trust/permission policy JSON after the concrete resources, ARNs, principal, account, and Region are known.
- [ ] Create Document, Screening, and Registration roles with distinct trust and permissions.
- [x] Implement STS role assumption with separate role-scoped AWS clients and a demo `HumanRole` session tag.
- [x] Add a demo Lambda handler and ARN-scoped policy templates for the actual Lambda Invoke boundary.
- [ ] Call the actual restricted service as an unauthorized test identity and capture a genuine AWS `AccessDenied` response.
- [ ] Verify the authorized test identity reaches only the intended restricted operation.
- [ ] Record an opt-in AWS integration test and teardown/credential-rotation instructions.

## Stage 4 — Supervisor and three specialists (CLI)

- [x] Implement a tool-less Supervisor that classifies/routs but cannot execute tools.
- [x] Implement Document Agent with `extract_document_fields` and `get_buyer_profile` only.
- [x] Implement Screening Agent with `screen_sanctions` and `assess_source_of_funds` only.
- [x] Implement Registration Agent with `approve_buyer` and `submit_oqood_registration` only; restricted calls use the AWS-protected action boundary.
- [x] Implement document extraction and source-of-funds evidence narration; neither produces final legal/approval decisions.
- [ ] Manually verify each specialist's offered tool list and cross-specialist AWS denials at the intended boundary.
- [ ] Demonstrate missing/partial AWS config without crashing the process.

## Stage 5 — Streamlit experience

- [x] Add a projector-readable single-page chat interface and role/persona selector.
- [x] Label selector as a local demo persona unless integrated with trusted authentication.
- [x] Add synthetic-buyer selection/status and clear non-production messaging.
- [x] Add clear empty/missing AWS configuration messages and AWS failure handling.
- [x] Smoke-test local UI startup without issuing AWS calls.

## Stage 6 — Append-only audit and governance trace

- [x] Add correlation IDs for each chat turn and propagate them to agent/tool calls.
- [x] Append structured tool events to JSONL with timestamp, human persona/role, agent, tool, sanitized arguments, outcome, and correlation ID.
- [x] Redact secrets and avoid storing raw identity/bank document contents.
- [x] Catch AWS authorization exceptions and preserve safe provider code/request ID details.
- [x] Render an expandable governance trace below every assistant response with ordered calls and explicit text/icons for `ALLOWED` and `DENIED`.
- [ ] Validate append-only behavior, concurrency assumptions, and projector legibility.

## Stage 7 — Prompt injection demonstration

- [x] Keep the poisoned statement marked fictional and untrusted.
- [x] Add prompt instructions as model guidance only (not authorization); clearly delimit document content as untrusted evidence.
- [x] Implement the attack button/orchestration through Document, Supervisor, and Registration Agent.
- [ ] Verify the non-authorized test identity receives a real AWS `AccessDenied`, not a locally generated denial.
- [ ] Confirm audit event and governance panel show both the attempted step and infrastructure-denied outcome.
- [ ] Run the complete attack scenario repeatedly from a clean local state before conference use.

## Stage 8 — Documentation and release readiness

- [x] Document local setup/run steps, optional AWS credential setup, Bedrock model access, and Kiro spec location.
- [x] Document IAM/role limitations honestly and explain that local JSON access is outside IAM enforcement.
- [x] Update README status and include exact prompt sequence ending with the poisoned-document attempt.
- [ ] Add manual verification instructions, AWS cost/cleanup steps, least-privilege policy documents, and a preflight checklist.
- [ ] Verify the full install/run path on a clean macOS account/project clone with blank AWS settings.
- [ ] Perform final security and projector presentation review; never use real buyer data.
