# Information Hierarchy and Labeling Rules

**Status:** Governance/template document (draft)  
**Purpose:** Maintain clarity by categorizing content as **evidence**, **inference**, **hypothesis**, or **opinion** in outputs, records, and reviews.

## Categories

| Label | Definition | Allowed basis | Required qualifiers |
|---|---|---|---|
| **Evidence** | Directly observed, source-reported, measured, or computed information traceable to an identified source, artifact, record, or reproducible calculation. | Opened/reviewed source, verified artifact, logged observation, dataset/result, deterministic calculation with stated inputs. | Source/artifact ID or citation, access/verification status, date/context as applicable, material limitations. |
| **Inference** | A conclusion derived from cited evidence through stated reasoning. Not directly stated by a source or directly observed as a final fact. | One or more evidence items plus explicit reasoning steps/assumptions. | Cited evidence IDs, reasoning basis, assumptions, uncertainty/confidence limits, alternative explanations where material. |
| **Hypothesis** | A provisional, testable explanation or predicted outcome not yet established by sufficient evidence. | Evidence gaps, preliminary patterns, proposed mechanisms, or planned tests. | Test/verification criterion, required evidence, scope/conditions, current support status (`unverified`/limited), what would confirm or falsify. |
| **Opinion** | A preference, recommendation, judgment, or value-based position not fully determined by evidence. | Stated objectives, constraints, trade-offs, or user/author preferences. | Attribution (who holds it), basis, affected assumptions/trade-offs, separation from evidence/inference; do not present as verified fact. |

## Labeling rules

1. **Label every material statement** in research outputs, analyses, summaries, code rationale, and decision records. Trivial formatting/navigation text may be unlabeled if it carries no factual or evaluative claim.
2. **Do not upgrade labels.** Unsourced generated text, model recall, or fluent explanation is not Evidence. Correlation, pattern matching, or analogy is not Evidence of causation.
3. **Evidence requires traceability.** Each Evidence statement must identify its source/artifact (URL, document, record ID, file path, command output, dataset, calculation input) and access/verification state (`verified/opened`, `metadata_only`, `inaccessible`, `not_checked`, `not_run` as applicable).
4. **Separate mixed statements.** If a sentence contains multiple categories, split or tag components explicitly (e.g. `Evidence: ... Inference: ...`).
5. **State uncertainty adjacent to the claim.** Material uncertainty, conflicts, incompleteness, or stale data must appear next to affected Evidence/Inference/Hypothesis statements.
6. **Distinguish source existence/support/truth.** A source resolving does not prove claim truth; a verified artifact existing does not prove correctness of its contents or suitability.
7. **No unsourced-as-verified.** Statements without traceable verification must be labeled Inference, Hypothesis, or Opinion and treated as unverified until supported (see [UNSOURCED_STATEMENT_VERIFICATION_POLICY.md](./UNSOURCED_STATEMENT_VERIFICATION_POLICY.md)).
8. **Code and technical claims:** runtime behavior, test results, benchmarks, security properties, and compliance claims are Evidence only when backed by executed checks, logs, reviewed artifacts, or authoritative public documentation cited with access details; otherwise label as Hypothesis/Inference with verification steps.

## Output template

```text
## Request / Scope
- Requested output:
- Scope and exclusions:
- Authorized actions/approvals:

## Evidence
- [E1] <statement>
  - Source/Artifact: <id, title, URL/path/record>
  - Access/Verification: <opened_and_reviewed|metadata_only|inaccessible|not_checked|confirmed|ran_successfully|not_run|...>
  - Date/Context: <value or n/a>
  - Limitations: <value or none identified>

## Inferences
- [I1] <statement>
  - Based on: [E#,...]
  - Reasoning/Assumptions: <text>
  - Uncertainty/Alternatives: <text>

## Hypotheses
- [H1] <statement>
  - Basis: [E#]/[I#]/gap
  - Test/Verification criterion: <how to confirm or falsify>
  - Current status: <unverified|partly supported|...>

## Opinions / Recommendations
- [O1] <statement>
  - Attributed to: <commander/user/author/system recommendation>
  - Basis: [E#]/[I#]/objective/trade-off
  - Not presented as verified fact

## Audit status
- Pre-output audit: <pass|fail|not_run> (see PRE_OUTPUT_AUDIT.md)
- Unresolved items / required approvals: <list or none>
```

## Mapping to existing schema

`agent-design.schema.json` (`claims[].epistemic_status`) can be mapped for record compatibility:

| Hierarchy label | Typical schema epistemic_status | Notes |
|---|---|---|
| Evidence | `source_reported_fact`, `direct_observation`, `calculation` | Requires traceable source/artifact/inputs and support metadata. |
| Inference | `inference` | Must cite evidence and state reasoning/assumptions. |
| Hypothesis | `causal_hypothesis`, or `unknown` used as provisional testable gap | Prefer explicit test criterion in claim/limitations fields. |
| Opinion | `opinion_or_recommendation` | Must be attributed and separated from evidence. |

Schema conformance validates structure only; it does not establish factual correctness or verification quality.
