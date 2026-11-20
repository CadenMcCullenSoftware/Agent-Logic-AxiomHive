# Value Proposition and Compliance/Privacy Framework

**Status:** Governance documentation (draft)  
**Scope:** Agent Docs system design and local reference implementation.

## Value proposition

The system replaces opaque automation with a **predictable, privacy-focused, and compliant-oriented framework** for commander-led research and project operations.

| Attribute | Meaning in this system | Supporting mechanisms |
|---|---|---|
| **Predictable** | Behavior follows defined workflows, registered task types, explicit approvals, and traceable state transitions rather than hidden autonomous action. | JSON workflow validation, registered local task handlers, `--confirm`/UI confirmation gates, human-review pauses, audit events, deterministic catalog validation/tests. |
| **Privacy-focused** | Data handling is limited to authorized task needs; sensitive information is minimized, bounded, and subject to disclosure controls. | Data minimization rules, pre-output privacy gate, controlled source retrieval/storage, no secrets in issues/logs by policy, deployment access-control requirements. |
| **Compliant-oriented** | Design artifacts support evidence, accountability, review, and risk management aligned to recognized governance practices; compliance is assessed per deployment and jurisdiction. | Structured records/schemas, traceable sources/claims, audit logging requirements, threat/red-team planning, approval and review controls, documented limitations. |

> Compliance is context-specific. This repository provides reference controls and documentation; it does not by itself certify compliance with any law, regulation, contract, or standard.

## Privacy framework

### Principles
- **Minimization:** collect, process, store, and display only data necessary for the authorized task.
- **Purpose limitation:** use project/source/workflow data for stated commander-directed objectives; do not repurpose without authorization.
- **Access control:** restrict access based on role/need-to-know in deployed environments (reference implementation has no production multi-user authz).
- **Transparency and traceability:** record material actions, retrievals, approvals, and audit outcomes.
- **Security safeguards:** protect confidentiality/integrity/availability appropriate to data sensitivity and deployment risk.
- **Retention and disposal:** define retention periods, archival, redaction, and secure deletion procedures for deployments.

### Data handling controls (reference)
| Data class | Examples | Controls |
|---|---|---|
| Project/operational records | objectives, notes, corrections, tasks, messages | scoped storage in workspace DB, audit logging, access restrictions in deployment, review before export/sharing |
| Retrieved source content | fetched pages/text, URLs, status/errors | user-triggered retrieval, URL validation and fetch bounds, provenance/status tracking, content-size/type limits, risk review for untrusted content |
| Audit/security records | audit events, pre-output audit checklists, test findings | integrity/retention controls, least-privilege access, avoid sensitive payloads/secrets |
| Credentials/secrets | API keys, tokens, passwords | never committed to repo/issues/logs; environment/deployment secret management required |

### Privacy review checklist (pre-output/deployment)
- Is each data element necessary for the authorized purpose?
- Are sensitive fields redacted/minimized in outputs, logs, and shared artifacts?
- Is external transfer or disclosure explicitly authorized and documented?
- Are retention, backup, and deletion expectations defined for the environment?
- Are access controls, encryption, and monitoring appropriate for deployment risk?

## Compliance-oriented framework

### Control areas
| Area | Documentation/mechanisms |
|---|---|
| Governance and accountability | `SYSTEM_PURPOSE.md`, attribution/authority rules, approval gates, human-review states |
| Evidence integrity | information hierarchy, source verification policy, claim/source/artifact records, evaluation limits |
| Risk management | threat model plan, red-team schedule, pre-output audit, workflow validation |
| Security and resilience | SSRF/network controls, bounded execution inputs, dependency/test/compile checks, deployment hardening requirements |
| Logging and auditability | `audit_events` baseline, audit logging requirements, pre-output audit records |
| Privacy | minimization, access boundaries, retention/disposal expectations, privacy gate in pre-output audit |

### Deployment notes
- Reference implementation status: local, limited automated feature coverage for newer workspace flows, no production authn/authz/multi-user isolation, no certified compliance posture.
- Before production or regulated use: perform legal/compliance assessment, security/privacy reviews, access-control implementation, logging/monitoring hardening, and documented validation appropriate to applicable requirements.
