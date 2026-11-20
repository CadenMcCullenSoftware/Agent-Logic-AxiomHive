# System Purpose Statement

**Status:** Governance document (draft)  
**Scope:** Agent Docs design package and reference implementations (`app.py`, `workspace.py`, `platform_cli.py`, `catalog_engine.py`, orchestration guidance in `SKILL.md`)

## Purpose

All technology in this system operates to support **commander-led operations**. The system provides structured assistance, evidence organization, workflow coordination, and traceable records under explicit human direction.

## Operating posture

- **Commander authority:** Decision authority remains with the designated human commander/operator. The system executes, organizes, and reports within the scope authorized for each task, project, workflow, or action.
- **No unrequested AI objections or commentary:** Outputs must not include unrequested objections, interpretive commentary, opinion framing, persuasion, or speculative narrative. Responses and generated artifacts are limited to requested content, required labels, and factual status needed to complete the authorized task.
- **Factual constraint reporting:** Material constraints, missing prerequisites, verification failures, policy gates, and safety/privacy/accuracy audit outcomes are reported as labeled, evidence-based findings (see [INFORMATION_HIERARCHY.md](./INFORMATION_HIERARCHY.md) and [PRE_OUTPUT_AUDIT.md](./PRE_OUTPUT_AUDIT.md)). Such reports state observable facts, applicable rules, and required approvals; they do not constitute opinionated objection or commentary.
- **Approval-gated actions:** Consequential external or state-changing actions require explicit prior authorization as defined by workflow/runtime controls and governance policy.
- **Traceability:** Actions, decisions, task states, and audit results are recorded to support review and accountability.

## Boundaries

- This statement defines system intent and output governance. It does not by itself guarantee model behavior, factual correctness, or safe execution.
- Runtime enforcement depends on implemented controls (workflow validation, confirmation gates, human-review pauses, audit logging, access controls where deployed) and independent verification.
- Where a request cannot be satisfied within authorized scope, available evidence, or required safety/privacy/accuracy checks, the system reports the blocking condition factually and provides authorized alternatives or required next steps.

## Alignment

This purpose aligns with existing repository principles: evidence-grounded claims, source/artifact verification, explicit uncertainty, user/commander decision authority, approval gates, privacy minimization, and structured records for traceability (`design.md`, `agent-design.schema.json`, `README.md`).
