# Pre-Output Audit Process

**Status:** Governance/process document with reference checklist mechanism (draft)  
**Purpose:** Audit all content prior to output for **safety, privacy, fairness, and technical accuracy** before generating text, code, or other requested support artifacts.

## Scope

Applies to:
- User-facing responses and reports
- Generated or modified code, scripts, configuration, and commands
- Workflow definitions, task outputs, and agent-coordination messages
- Summaries of sources, artifacts, test results, or system state

## Mandatory audit gates

Each output must pass all applicable gates before release. A gate is `pass`, `fail`, or `n/a` (with justification).

| Gate | Required checks | Evidence/examples | Fail condition |
|---|---|---|---|
| **Safety** | No instructions enabling unauthorized harm; state-changing/external actions identified; approvals and reversibility documented; risky commands/artifacts flagged; refusal or safe alternative provided when required. | Action scope, approval status, risk review, sandbox/dry-run status, rollback notes. | Unsafe action proposed/executed without required controls or factual risk disclosure. |
| **Privacy** | Data minimization applied; sensitive data (credentials, secrets, PII, private records) not exposed or unnecessarily propagated; sharing/retention boundaries respected; redaction applied where needed. | Data fields used, redactions, storage/logging impact, authorization for disclosure. | Unnecessary sensitive-data inclusion, leakage risk, or unauthorized disclosure path. |
| **Fairness** | Output avoids unrequested discriminatory, exclusionary, or stereotyped assumptions; relevant stakeholder impacts and limitations considered for recommendations/automation; evaluation criteria applied consistently. | Affected parties/contexts, criteria used, known limitations/bias risks, uncertainty where evidence is limited. | Unjustified differential treatment, biased assumption presented as fact, or unexamined material impact. |
| **Technical accuracy** | Claims labeled per information hierarchy; sources/artifacts/tests verified or marked unverified; code/config/commands checked for stated purpose and known constraints; no fabricated citations, results, or capabilities. | Citations/IDs, access status, test/compile/lint results, command/script inspection, environment constraints. | Fabricated/misleading claim, unlabeled speculation presented as fact, or unverified technical assertion stated as confirmed. |

## Process

1. **Define output scope:** requested deliverable, audience, authorized actions, and exclusions.
2. **Classify statements:** label material content as Evidence/Inference/Hypothesis/Opinion ([INFORMATION_HIERARCHY.md](./INFORMATION_HIERARCHY.md)).
3. **Verify or qualify:** confirm sources/artifacts/tests where feasible; mark inaccessible/unverified items explicitly; separate unsourced statements from verified facts ([UNSOURCED_STATEMENT_VERIFICATION_POLICY.md](./UNSOURCED_STATEMENT_VERIFICATION_POLICY.md)).
4. **Run gate checks:** complete safety, privacy, fairness, and technical-accuracy checks; record evidence and unresolved issues.
5. **Apply disposition:**
   - **Release:** all applicable gates pass; unresolved items disclosed.
   - **Revise:** any gate fails or required evidence missing; correct, remove, relabel, or narrow scope.
   - **Block/escalate:** required approval, verification, or safe condition unavailable; report factual blocking condition and authorized next step.
6. **Log audit record:** store checklist result, reviewer/actor, timestamp, output identifier/context, and key evidence references.

## Checklist record format

Use `docs/pre_output_audit_checklist.template.json` for machine-readable records. Required top-level fields:

- `audit_id`, `timestamp_utc`, `actor`, `commander_or_requestor`, `output_type`, `output_scope`
- `gates.safety`, `gates.privacy`, `gates.fairness`, `gates.technical_accuracy` each with `status` (`pass|fail|na`), `checks`, `evidence`, `issues`
- `information_hierarchy_applied` (boolean), `unsourced_statements_separated` (boolean)
- `disposition` (`release|revise|block`), `notes`

A reference validator is provided: `python3 pre_output_audit.py validate docs/pre_output_audit_checklist.template.json`

## Implementation notes (reference workspace)

- The project workspace captures the checklist fields in this document and validates them with `pre_output_audit.py` before storing an audit record.
- The workspace also checks claim-ledger metadata (labels, support status, linked source retrieval/review, uncertainty, hypothesis test criteria, and opinion attribution). A release disposition is blocked while claim-ledger blockers remain.
- These checks are structural and metadata-based. They do not assess claim truth, source quality, safety, privacy, or fairness; the four gate results remain recorded human judgments.
- Workflow/task states, human-review pauses, and `audit_events` in `workspace.db` provide additional traceability, but do not by themselves establish correct audit judgments.
- `pre_response_checks` in `agent-design.schema.json` provide structural pre-response gates for agent records; they do not by themselves prove safety, privacy, fairness, or technical accuracy.
- Before consequential execution, use existing confirmation/review controls (`platform_cli.py --confirm`, UI workflow confirmation, manual review tasks) and record outcomes in audit logs.
