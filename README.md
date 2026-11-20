# Agent Docs

This repository contains design documentation and a local browser-based reference workspace for evidence-grounded, user-controlled research operations. The workspace organizes projects, research sources, notes, corrections, predefined workflows, task state, agent coordination records, and an operations log. The policy, evaluation, and record-keeping framework remains the foundation for its implementation.

## Purpose

The project centers on one idea: an AI assistant should help the user reason and research effectively without superseding user decision authority, hiding uncertainty, or acting on incomplete evidence.

The materials in this repo emphasize:

- evidence-supported claims over overconfident assertion without evidence
- source and artifact verification before citing or acting
- explicit uncertainty and limitations disclosure
- user approval before consequential external or state-changing actions
- privacy and operational boundary controls
- separation between compliance and correctness
- structured records for traceability and auditing

## Repository map

### Core design documents

- [Agent Design: Evidence-Grounded, User-Controlled Research Assistant.md](./Agent%20Design:%20Evidence-Grounded,%20User-Controlled%20Research%20Assistant.md)  
  The primary design document. It defines the operating principles for an assistant that supports research, planning, comparison, and drafting while preserving the user's authority.

- [design.md](./design.md)  
  A formal schema specification for an agent record that captures task framing, evidence, claims, sources, reasoning, approval state, and evaluation.

- [agent-design.schema.json](./agent-design.schema.json)  
  The JSON Schema used to validate agent records.

- [example-agent-record.json](./example-agent-record.json)  
  A sample valid record illustrating the schema in use.

### Supporting principle documents

These documents expand on the design philosophy and cover important failure modes and safeguards:

- [1. Preserving user control.md](./1.%20Preserving%20user%20control.md) — master synthesis covering Principles 1–10 (filename retained for provenance; content is cross-principle)
- [Preserving user control.md](./Preserving%20user%20control.md) — standalone Principle 1 brief
- [Evidence-supported conclusions.md](./Evidence-supported%20conclusions.md)
- [Principle 2: Explicit approval before automated action.md](./Principle%202:%20Explicit%20approval%20before%20automated%20action.md)
- [Principle 3: Verifying that sources and scripts exist.md](./Principle%203:%20Verifying%20that%20sources%20and%20scripts%20exist.md)
- [Principle 4: Supportive partner stance without reframing opinion as fact.md](./Principle%204:%20Supportive%20partner%20stance%20without%20reframing%20opinion%20as%20fact.md)
- [Compliance versus correctness.md](./Compliance%20versus%20correctness.md)
- [Safe knowledge sharing within operational boundaries.md](./Safe%20knowledge%20sharing%20within%20operational%20boundaries.md)
- [Avoiding unrequested interpretation.md](./Avoiding%20unrequested%20interpretation.md)
- [Attribution and credit in AI-assisted work.md](./Attribution%20and%20credit%20in%20AI-assisted%20work.md)
- [Collective learning without damage.md](./Collective%20learning%20without%20damage.md)
- [SKILL.md](./SKILL.md) — deterministic multi-agent orchestration contract (`workflow-composer`), separate from the local Flask/SQLite workspace runtime

### Additional reference material

- [complete-appendix.pdf](./complete-appendix.pdf)  
  Supplemental appendix material referenced by the design set.

## Workspace implementation

Run the local Flask workspace with:

```
python3 app.py
```

Open `http://127.0.0.1:5000/workspace` to create and organize projects. The existing catalog browser remains available at `/`.

The workspace stores application records in `workspace.db`, separate from the semantic catalog database. It includes:

- projects with objectives, linked notes, and collected source records
- a claim ledger labeled evidence, inference, hypothesis, or opinion, with source links, support status, uncertainty, and verification criteria
- pre-output review records with metadata checks and human attestations for safety, privacy, fairness, and technical accuracy
- user-triggered HTTPS retrieval restricted to public IP addresses, with redirects disabled and a 2 MiB text limit
- correction records organized by category A–F
- JSON workflow definitions checked for schema shape, registered modules, dependencies, task configuration, ordering, and agent assignments
- ordered task runs with queued, running, completed, failed, skipped, and human-review states
- registered task operations for source review, note creation, correction organization, and a human-review pause
- agent role definitions, coordination messages, task assignment references, and audit events
- a command-line interface for project listing, workflow validation, and explicitly confirmed local workflow execution

The pre-output review is a deterministic metadata check plus recorded human attestations. It does not assess the meaning or truth of claims, certify source quality, or replace human sign-off. A source marked retrieved has only been fetched; a reviewer must still inspect it and attest that it supports the linked claim.

Workflow execution invokes only the registered local task types; workflow JSON cannot run shell commands. The six correction categories are stored as A–F because this specification does not define category names. The intended integrated sequence remains a design target; the app does not claim a demonstrated end-to-end research workflow.

CLI examples:

```
python3 platform_cli.py projects
python3 platform_cli.py validate-workflow workflow.json
python3 platform_cli.py run-workflow PROJECT_ID workflow.json --confirm
```

This is a local reference implementation, not a production deployment package or hosted multi-user service. Review access control, deployment configuration, and operational requirements before exposing it beyond a trusted local environment.

## How to use this repository

1. Start with [Agent Design: Evidence-Grounded, User-Controlled Research Assistant.md](./Agent%20Design:%20Evidence-Grounded,%20User-Controlled%20Research%20Assistant.md).
2. Read [design.md](./design.md) to understand the structured record model.
3. Review [example-agent-record.json](./example-agent-record.json) as a reference implementation of the schema.
4. Use the principle files to reason about edge cases such as source verification, approval boundaries, privacy, and evidence quality.
5. If you are building an agent or workflow on top of this design, treat the schema as a contract for traceability and safety rather than as a guarantee of factual correctness.

## Operational focus areas

The design set is organized around the following concerns:

- Source and artifact validation
- Uncertainty calibration and clear claim labels
- Causal reasoning discipline
- User-controlled decision authority
- Explicit approval gates before consequential actions
- Privacy minimization and information flow boundaries
- Independent verification for high-risk claims
- Evaluation and testing of agent behavior

## Governance and operations documents

- [docs/SYSTEM_PURPOSE.md](./docs/SYSTEM_PURPOSE.md) — commander-led system purpose, authority boundaries, and factual constraint reporting posture
- [docs/INFORMATION_HIERARCHY.md](./docs/INFORMATION_HIERARCHY.md) — evidence/inference/hypothesis/opinion definitions, labeling rules, and output template
- [docs/PRE_OUTPUT_AUDIT.md](./docs/PRE_OUTPUT_AUDIT.md) — pre-output audit process for safety, privacy, fairness, and technical accuracy
- [docs/pre_output_audit_checklist.template.json](./docs/pre_output_audit_checklist.template.json) — machine-readable pre-output audit checklist template
- [pre_output_audit.py](./pre_output_audit.py) — reference validator/summarizer for pre-output audit checklist records
- [docs/THREAT_MODEL_RED_TEAM_AUDIT_LOGGING.md](./docs/THREAT_MODEL_RED_TEAM_AUDIT_LOGGING.md) — threat modeling plan, red-team testing schedule, and audit logging requirements
- [docs/UNSOURCED_STATEMENT_VERIFICATION_POLICY.md](./docs/UNSOURCED_STATEMENT_VERIFICATION_POLICY.md) — policy/mechanism separating unsourced statements from verified facts
- [docs/VALUE_PROPOSITION_COMPLIANCE_PRIVACY.md](./docs/VALUE_PROPOSITION_COMPLIANCE_PRIVACY.md) — value proposition and compliance/privacy framework
- [docs/EVIDENCE_SOURCING_STANDARDS.md](./docs/EVIDENCE_SOURCING_STANDARDS.md) — evidence-sourcing standards for factual, publicly testable designs (including multi-agent swarm claims)

## Testing and validation status

The repository includes an executable catalog reasoning engine, a browser-based catalog and project workspace, automated tests, and reference governance/audit artifacts. In this environment, `python3 -m pytest -q` passes (`50 passed, 14 subtests passed`).

What is present:

- `catalog_engine.py` — executable semantic reasoning engine over the catalog knowledge graph
- `app.py` — Flask web UI exposing catalog reasoning tools and the project-operations workspace
- `workspace.py` — SQLite-backed project, source, correction, workflow, task, and agent-coordination modules
- `platform_cli.py` — command-line workspace operations
- `pre_output_audit.py` — pre-output audit checklist validator/summarizer
- `test_catalog_engine.py` — unit tests for the catalog engine (14 tests)
- `test_app.py` — UI tests for existing Flask catalog routes (19 tests)
- `test_workspace.py` — unit tests for workspace URL/workflow validation and core store/review lifecycle (10 tests)
- `test_pre_output_audit.py` — unit tests for pre-output audit validation/CLI (7 tests)
- `docs/` — governance, audit, threat/red-team, verification, compliance/privacy, and evidence-sourcing documents
- `requirements.txt` — package manifest (jsonschema, flask)
- `catalog.db` — SQLite persistence store
- `.github/workflows/ci.yml` — CI pipeline (test, validate, selftest, compile)

Automated validation includes:

- Unit tests for catalog validation, JsonLogic evaluation, and reasoning engine behavior
- Flask route tests for catalog browsing, traversal, evaluation, validation, and related API endpoints
- Workspace unit tests for URL validation, workflow validation, core record handling, manual-review pause/resume, and audit events
- Pre-output audit checklist validation tests and template validation
- Catalog schema validation against the meta-model
- Engine self-test exercising all four reasoning tools
- Python compilation checks

Current gaps:

- Automated feature/security tests for workspace/project, retrieval, correction, workflow, human-review, and agent-coordination UI/CLI flows remain limited beyond current unit coverage
- No production deployment artifacts, authentication, access control, or hosted multi-user isolation
- Correction categories are stored as A–F because category names/definitions are not specified by the current schema
- Pre-output audit, threat modeling, and red-team materials are documented/reference mechanisms; full runtime enforcement and independent adversarial validation require further implementation and review

Run the validation suite:

```
python3 -m pytest -q
python3 pre_output_audit.py validate docs/pre_output_audit_checklist.template.json
python3 catalog_engine.py --tool validate
python3 catalog_engine.py --tool selftest --database :memory:
python3 -m py_compile catalog_engine.py workspace.py platform_cli.py app.py pre_output_audit.py test_catalog_engine.py test_app.py test_workspace.py test_pre_output_audit.py
```
python3 -m pytest -q
python3 catalog_engine.py --tool validate
python3 catalog_engine.py --tool selftest --database :memory:
python3 -m py_compile catalog_engine.py workspace.py platform_cli.py app.py test_catalog_engine.py test_app.py test_workspace.py
```

## Code and implementation status

This repository includes an executable reference implementation of the catalog reasoning engine and a local research workspace alongside its design documentation. The catalog engine implements four reasoning tools over a SQLite-backed catalog store. The Flask UI exposes those tools and the project-operations workspace.

In practical terms:

- the repository is a design and governance package with local reference implementations
- production deployment work would need to extend and review these reference implementations against the principles in these documents
- any code built from this design should still be validated against security, privacy, and evidence-quality requirements before deployment

## Safe web-sourced references

The design set aligns with official public guidance from trusted institutions. Below are safe, authoritative references used to ground the approach:

- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI RMF 1.0: https://doi.org/10.6028/NIST.AI.100-1
- NIST Generative AI Profile: https://doi.org/10.6028/NIST.AI.600-1

These materials emphasize trustworthy AI design, risk management, and governance. They are consistent with the repository's emphasis on evidence quality, user control, clear uncertainty, and risk-aware deployment.

## Summary

In short, this repository defines a practical framework for building AI research assistants that are transparent, cautious, and accountable. It is most useful for teams designing agent workflows where evidence quality, user control, and operational safety matter more than raw conversational fluency.

The repository is documentation-forward and includes an executable reference implementation with automated tests, but does not include production deployment artifacts. It combines design language, schema, and evidence-grounded safety principles with runnable examples to guide implementation elsewhere.
