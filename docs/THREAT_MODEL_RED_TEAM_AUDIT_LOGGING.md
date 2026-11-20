# Threat Modeling Plan, Red-Team Testing Schedule, and Audit Logging Requirements

**Status:** Governance/operations plan (draft)  
**Scope:** Local reference implementation and documented workflows (`app.py`, `workspace.py`, `platform_cli.py`, `catalog_engine.py`, SQLite stores, templates, workflow JSON, agent/orchestration guidance).

## 1. Threat modeling plan

### Objectives
- Identify assets, trust boundaries, entry points, threats, and mitigations for commander-led, evidence-grounded operations.
- Prioritize controls that protect integrity of records, confidentiality/privacy, availability, and correctness of reported status.
- Maintain a living threat model updated on material design/code/workflow changes.

### Assets
| Asset | Examples | Security/privacy properties |
|---|---|---|
| Project records | projects, notes, corrections, workflow definitions/runs/tasks, agent messages | Integrity, availability, access control, auditability |
| Source artifacts | user-supplied URLs, retrieved content, metadata, access/error status | Integrity, provenance, confidentiality where sensitive, safe handling |
| Audit evidence | `audit_events`, pre-output audit records, test/validation outputs | Integrity, completeness, non-repudiation support, retention |
| Secrets/config | environment variables, deployment config, tokens/credentials if introduced | Confidentiality, least privilege |
| Execution surfaces | CLI commands, Flask routes, workflow engine, local task handlers | Authorization, input validation, predictable behavior |

### Trust boundaries and entry points
- **User/operator boundary:** browser UI and CLI inputs (project data, URLs, workflow JSON, review decisions, confirmations).
- **Network boundary:** outbound HTTPS retrieval from user-supplied sources (`validate_https_source_url`, `retrieve_https_source`).
- **Data boundary:** SQLite persistence (`catalog.db`, `workspace.db`), file-based docs/artifacts, logs.
- **Workflow boundary:** JSON-defined steps mapped to registered local task types; human-review pause/resume.
- **Agent/orchestration boundary:** agent definitions/messages and external orchestration guidance (`SKILL.md`) where used.

### Method and cadence
- **Method:** scenario-driven threat modeling per component (STRIDE/data-flow oriented as applicable) plus abuse-case review for LLM/agent misuse (prompt injection via retrieved content, fabricated verification, unauthorized action, data exfiltration, over-trust).
- **Cadence:** initial baseline, then on every material change to network retrieval, workflow execution, auth/access control, data schema/storage, or agent/tool integration; quarterly review at minimum.
- **Outputs:** threat register (ID, component, threat, impact, likelihood, mitigations, residual risk, owner, status), required tests/controls, and audit-log requirements.

### Baseline threat themes (reference)
| Theme | Representative risks | Existing/required controls |
|---|---|---|
| SSRF and network abuse | access to local/private services, metadata endpoints, redirect pivot, oversized/unsafe payloads | HTTPS-only, host/IP validation, non-global resolved IP checks, no redirects, content-type/size limits, egress restrictions in deployment; add stronger connect-time pinning/egress isolation for production |
| Input/workflow integrity | malformed workflow JSON, dependency confusion, unauthorized task behavior, schema drift | strict workflow validation, registered task types only, no shell-from-workflow, confirmation gates, schema validation/tests |
| Data/privacy leakage | sensitive data in notes/sources/logs, over-broad retrieval/storage, missing access controls | data minimization, redaction rules, access control/authn for non-local use, log review/retention controls |
| Misinformation/integrity | unsourced statements treated as facts, unverified claims, stale/conflicting evidence | information hierarchy labels, source verification policy, pre-output audit, explicit uncertainty/conflict records |
| Accountability gaps | missing/insufficient logs, unattributed actions, unclear review decisions | detailed audit logging requirements, human-review records, immutable/tamper-evident log handling in production |
| Availability/resource abuse | large inputs, expensive workflows, retrieval timeouts/failures | bounded fetch size/timeouts, workflow/run limits, failure handling, operational monitoring in deployment |

## 2. Red-team testing schedule

### Goals
- Exercise controls against realistic misuse and adversarial inputs.
- Validate detection, blocking, escalation, and auditability—not only nominal success paths.

### Test tiers and schedule
| Tier | Frequency | Focus | Example scenarios |
|---|---|---|---|
| **Tier 0 – smoke/security regression** | Every PR/change touching scoped components | Known controls remain effective | URL validator bypass cases, redirect refusal, workflow validation rejects invalid deps/unknown modules/agents, confirmation required for run, manual-review pause/resume |
| **Tier 1 – targeted adversarial tests** | Monthly and before release milestones | Component abuse cases | SSRF encoding/redirect/DNS-rebinding simulations (where testable), prompt-injection content in retrieved sources, oversized payloads, malformed/hostile workflow JSON, audit-log completeness for critical actions |
| **Tier 2 – integrated red-team exercise** | Quarterly | End-to-end operational misuse | attempt to induce unverified factual claims, bypass approval/human review, exfiltrate sensitive project data, poison source/correction records, confuse agent coordination/messages |
| **Tier 3 – external/independent review** | Prior to production or major deployment | Independent assessment | penetration/security review, privacy review, threat-model validation, audit-log integrity and incident-response readiness |

### Red-team scenario requirements
- Predefine objectives, rules of engagement, allowed targets/environments, and stop conditions.
- Use representative but non-sensitive test data; never use real secrets/PII.
- Record expected vs observed behavior, evidence (logs, screenshots, artifacts), severity, reproducibility, and remediation owner/date.
- Re-test after remediation and add regressions to automated suites where feasible.

## 3. Audit logging requirements

### Required event coverage
| Domain | Events to log |
|---|---|
| Identity/context | actor/user/service, role/authority context (when available), project/run/task IDs, source IP/session metadata in deployed environments |
| Data lifecycle | create/read/export/update/delete of projects, notes, sources, corrections, workflows, agents, messages (as applicable to interface) |
| Source retrieval | URL requested (sanitized as needed), validation outcome, fetch start/end, status code/class, content type/size, storage decision, errors/redactions |
| Workflow/task | definition validation results, save/start/stop, task state transitions, confirmations/approvals, human-review requests/decisions, failures/retries/skips |
| Pre-output audits | audit ID, scope/output reference, gate statuses, disposition, unresolved issues, reviewer/actor |
| Security/privacy controls | access denials, policy violations, redactions, sensitive-data handling decisions, configuration/security-relevant changes |

### Log field requirements
Each event should include: unique event ID, UTC timestamp, actor, action, entity type/ID, project/workflow/run/task correlation IDs when applicable, outcome (`success|failure|blocked|denied`), reason/error code, and structured detail/evidence references. Avoid logging secrets, credentials, or unnecessary sensitive payloads.

### Integrity, retention, and review
- **Integrity:** append-oriented storage with access controls; production deployments should use tamper-evident/centralized logging and time synchronization.
- **Retention:** define retention period by data sensitivity and compliance needs; support secure deletion/anonymization where required.
- **Review:** routine review of failures/denials/approval events; alerting for anomalous retrievals, repeated validation failures, or unauthorized-action attempts in deployed environments.
- **Current reference state:** `workspace.py` records core lifecycle events in `audit_events` (SQLite). This is a local traceability baseline, not a complete production security logging solution.

## Verification and maintenance
- Track threat-model items, red-team findings, and logging gaps in a managed register.
- Require evidence of test execution and log review for material releases/changes.
- Update this plan when architecture, dependencies, deployment model, or regulatory context changes.
