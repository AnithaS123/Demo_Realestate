# Requirements: Governed Buyer Onboarding Agents

## Purpose and scope

Create a conference demo of fictional Dubai off-plan buyer onboarding. Show how a supervisor routes identity/document review, sanctions screening, source-of-funds assessment, and Oqood registration work, while permissions are enforced outside the LLM. The app and fixture files run locally; AWS Bedrock, STS, and any IAM-protected action endpoint are remote services used by the demonstration.

**Current status:** Stage 1 only is implemented. The requirements below are the target specification; unimplemented requirements must not be represented as working behavior.

## Actors

- **Buyer:** may view their own fictional profile, documents, and status.
- **Sales Agent:** may view assigned fictional deals, submit documents, and check status.
- **Compliance Officer:** may review all synthetic cases and invoke authorized approval/registration operations.
- **Supervisor:** a tool-less routing agent, not a human identity and not an authorization authority.
- **Specialist agents:** Document, Screening, and Registration, each using a separate AWS role/session.
- **Presenter/operator:** runs the local application and switches demo persona; this is a presentation control, not production authentication.

## Requirements

### R1 — Local startup and configuration

- **R1.1** The application shall run locally from a single-page Streamlit UI and load fictional case data from JSON/text files, without a database.
- **R1.2** The MCP server shall use Python MCP SDK v2 `MCPServer` and expose typed tool contracts.
- **R1.3** The application shall load `.env` once through `src/config.py`; application modules shall consume typed config and shall not read `os.environ` directly.
- **R1.4** Blank AWS variables shall not prevent local read-only server startup. When a feature actually requires a missing setting, it shall report the exact variable name in a readable error.
- **R1.5** Secrets shall be excluded from version control; `.env.example` shall document every supported setting with placeholders.

### R2 — Synthetic case data

- **R2.1** The demo shall provide five fictional buyers: one clean case, one deliberate screening hit, and three ambiguous cases.
- **R2.2** It shall provide fictional passport, Emirates ID, bank statement, and salary certificate text for each buyer.
- **R2.3** It shall provide a synthetic watchlist with transliteration aliases and at least one deliberate near-match.
- **R2.4** Every fixture shall be explicitly marked synthetic and shall contain no real personal, financial, or identity information.
- **R2.5** One document shall contain a clearly identifiable malicious embedded instruction to test prompt injection; its contents are untrusted data, never trusted authorization.

### R3 — MCP tools and specialist ownership

- **R3.1** The Document Agent shall have only `extract_document_fields` and `get_buyer_profile`.
- **R3.2** The Screening Agent shall have only `screen_sanctions` and `assess_source_of_funds`.
- **R3.3** The Registration Agent shall have only `approve_buyer` and `submit_oqood_registration`.
- **R3.4** `screen_sanctions` shall report possible matches for human review and shall not issue a legal determination or make an automated approval.
- **R3.5** `assess_source_of_funds` shall return a narrative and calibrated confidence signal, never an approve/reject decision.
- **R3.6** Every MCP tool shall have a precise model-facing docstring, typed arguments/results, and explicit errors.

### R4 — IAM and identity boundaries

- **R4.1** Each specialist AWS operation shall use credentials from its own STS-assumed role; one specialist role shall not receive another specialist's AWS permissions.
- **R4.2** The Supervisor shall have no tools and no AWS role that can execute specialist actions.
- **R4.3** Restricted actions shall be authorized by a real AWS service-side IAM policy evaluation. A local Python conditional, UI toggle, prompt instruction, mock response, or IAM policy simulator shall not be described as an AWS-enforced denial.
- **R4.4** A denied restricted request shall surface an actual AWS `AccessDenied`/`AccessDeniedException`, caught and rendered as a readable denial with no stack trace.
- **R4.5** Only a Compliance Officer's trusted identity shall be able to reach the registration-authorized credentials. A freely editable sidebar dropdown is not a security boundary and must not grant privileged credentials on its own.
- **R4.6** The local demo shall clearly distinguish the presentation persona selector from authenticated identity. Any deployment that treats a selected role as authorization shall be considered non-production and insecure.
- **R4.7** The design shall identify an IAM-enforced AWS API boundary for approval/registration (for example, a separately protected API/Lambda invocation). Because local filesystem access does not invoke AWS IAM, the demo shall not claim that IAM denied a local-only function call.

### R5 — Multi-agent flow and prompt-injection demonstration

- **R5.1** The Supervisor shall route intent to the relevant specialist without tools.
- **R5.2** The poisoned document shall be treated as untrusted; Document analysis must not execute its embedded instruction.
- **R5.3** The attack script shall deliberately demonstrate the attempted escalation to the Registration Agent and the real infrastructure denial for an unauthorized identity.
- **R5.4** A successful Compliance Officer registration action shall only be shown when the caller identity is independently authorized by the protected AWS boundary.

### R6 — Audit and operator visibility

- **R6.1** Each tool invocation shall append a JSONL event with timestamp, human role/persona, agent, tool, arguments (redacted as appropriate), outcome (`allowed`/`denied`), and correlation ID.
- **R6.2** Audit output shall be append-only in the application; the implementation shall document local file limitations and avoid recording secrets or unnecessary identity-document contents.
- **R6.3** Under every assistant response, an expandable governance panel shall show agent steps, tool names, results, and a high-contrast `ALLOWED` or `DENIED` state for every call.
- **R6.4** The governance panel shall be legible at projector scale, keyboard-operable, and not rely on color alone to communicate status.

### R7 — Streamlit experience

- **R7.1** The UI shall be a single-page conversational interface with a human-role/persona selector in the sidebar.
- **R7.2** The UI shall provide clear fictional-data, non-production, and configuration notices.
- **R7.3** The UI shall present partial-configuration errors inline and shall not crash because AWS settings are blank.
- **R7.4** The demo shall be usable on a projected screen at typical conference viewing distance, with restrained dense text and readable contrast.

### R8 — Documentation and testability

- **R8.1** The README shall explain the security claim in two sentences, prerequisites, Bedrock access, setup, run instructions, IAM policy creation, and a prompt-by-prompt attack demonstration script.
- **R8.2** The README shall include a repeatable manual smoke checklist for fixture lookup, screening hit/near-miss/transliteration, missing configuration, tool ownership, audit records, and AWS denial handling; a test framework is optional for this conference demo.
- **R8.3** A policy test or live integration test shall prove an actual unauthorized AWS request is denied and the authorized principal can execute only the intended restricted action.
- **R8.4** Kiro requirements, design, and task artifacts shall be kept in `.kiro/specs/governed-buyer-onboarding/` and reflect implementation status honestly.

## Security and product constraints

- Prompt text is never permission enforcement.
- Local Python/file access is not governed by an assumed AWS role. Only AWS API calls undergo AWS IAM authorization.
- A Streamlit role selector is a demo control only unless bound to a trusted, authenticated identity claim that drives role assumption outside user control.
- Do not use real buyer records, real watchlist data, or real government identifiers.
- Do not claim production Oqood/DLD connectivity unless a real, authorized integration exists and is separately reviewed.
