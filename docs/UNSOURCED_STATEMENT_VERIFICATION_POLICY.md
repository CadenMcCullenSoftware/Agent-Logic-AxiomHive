# Policy and Mechanism: Unsourced Statements vs Verified Facts

**Status:** Governance policy (draft)  
**Purpose:** Prevent misinformation and speculation by separating unsourced generated statements from verified, publicly available (or otherwise verifiably sourced) facts.

## Policy

1. **Default classification:** Any generated statement without traceable verification is **not** a verified fact. It must be labeled as **Inference**, **Hypothesis**, **Opinion**, or explicitly marked **Unverified** (see [INFORMATION_HIERARCHY.md](./INFORMATION_HIERARCHY.md)).
2. **Verified fact criteria:** A statement may be presented as verified Evidence only when supported by:
   - a publicly available source that was accessed/reviewed (or an authorized non-public source with recorded access status), with citation/URL/identifier, date/context, and relevant excerpt/result; or
   - a directly observed artifact/record/log/test output produced or inspected in the current authorized scope, with reproducible reference.
3. **No fabrication or implication:** Do not invent citations, URLs, quotes, data, test results, benchmarks, execution outcomes, or source contents. Do not imply a source was opened, a script was run, or a claim was independently verified unless evidence exists.
4. **Provenance and limits required:** Verified statements must include access/verification status and material limitations (scope, date, conflicts, incompleteness, applicability).
5. **Conflict handling:** When credible sources conflict, report the conflict as Evidence/Inference with citations; do not resolve by speculation.
6. **Inaccessible or unavailable sources:** Mark as `inaccessible`/`not_checked` and exclude from verified-fact claims. An inaccessible source is not evidence for or against a claim unless independently corroborated.
7. **Generated code and technical outputs:** Code, commands, configurations, and technical conclusions are verified only to the extent tested/reviewed (compile, tests, lint, static checks, execution logs, documented constraints). Untested behavior must be labeled as Hypothesis/Inference with verification steps.
8. **Pre-output enforcement:** The pre-output audit must confirm separation of unsourced statements from verified facts before release ([PRE_OUTPUT_AUDIT.md](./PRE_OUTPUT_AUDIT.md)).

## Mechanism

### Output controls
- Use the standard template in [INFORMATION_HIERARCHY.md](./INFORMATION_HIERARCHY.md) with separate sections for Evidence, Inferences, Hypotheses, and Opinions.
- Attach identifiers (`[E1]`, `[I1]`, `[H1]`, `[O1]`) and link inferences/hypotheses/opinions to evidence where applicable.
- For each Evidence item record: source/artifact, locator (URL/path/record ID), access/verification status, date/context, and limitations.

### Verification workflow
1. **Collect:** identify candidate sources/artifacts and capture locators.
2. **Access/inspect:** open/read/execute only within authorized scope; record status and relevant observations.
3. **Correlate:** map specific claim text to specific supporting passages/results/records.
4. **Label:** assign hierarchy label and support status; downgrade unverifiable claims.
5. **Audit:** complete pre-output checklist (`unsourced_statements_separated=true` only when verified).

### Record integration
- `agent-design.schema.json` supports claim/source/artifact traceability (`claims`, `sources`, `artifacts`, support/access/execution statuses, `pre_response_checks.claim_support_reviewed`, `evidence_inference_separated`).
- Workspace source records (`workspace.py`) store URL, retrieval status, content/type, and errors; retrieval success indicates content was fetched/stored under implemented controls, not that extracted claims are true.
- Corrections and human-review tasks should be used to resolve disputed or unverified material before dependent workflow steps proceed.

## Prohibited patterns

- “Verified/proven/tested/benchmarked” without identified object, method, result, and evidence reference.
- Presenting consensus, popularity, or fluent model output as verification.
- Citing inaccessible sources as support.
- Reusing prior outputs as independent confirmation without a distinct evidence path.
