# Evidence-Grounded, User-Controlled Agent Record — Design Documentation

**Schema version:** `1.0.0`  
**Schema ID:** `https://example.invalid/agent-design.schema.json`  
**Status:** Draft specification

## Purpose

This schema validates the structure of an assistant research or reasoning record. It enforces an **evidence-grounded, user-controlled** design: every claim must be traceable to sources, every action must carry explicit approval metadata, and every output must disclose uncertainty and limitations.

> **Important:** Schema conformance does **not** prove factual truth, source quality, independent verification, or safe execution. It validates structure only.

## Top-Level Structure

A valid record is a JSON object with these required top-level keys:

| Key | Type | Description |
| ----- | ------ | ------------- |
| `schema_version` | `string` (const `"1.0.0"`) | Locks the record to this schema version |
| `task` | `object` | What was asked, intended use, audience, scope, and constraints |
| `claims` | `array[claim]` | Every factual or inferential assertion made |
| `sources` | `array[source]` | Every source consulted, with access and category metadata |
| `artifacts` | `array[artifact]` | Scripts, files, commands, packages, datasets referenced or executed |
| `reasoning` | `object` | Summary, assumptions, unknowns, causal assessment, independent check |
| `actions` | `array[action]` | Drafted or executed actions with approval and reversibility metadata |
| `evaluation` | `object` | Evaluation status, benchmark details, limitations |
| `attribution` | `object` | Human author, attribution basis, AI role (const `"supporting_tool"`) |
| `pre_response_checks` | `object` | Eleven boolean pre-flight checks that must all be true before response |

No additional properties are allowed at any level (`additionalProperties: false`).

---

## 1. Task

Defines the boundaries of the work.

- `question` (string, required, minLength 1) — The user's question or request.
- `intended_use` (string \| null) — How the output is intended to be used.
- `audience` (string \| null) — Who the output is for.
- `scope` (object, required) — `included`, `excluded` (string arrays), `depth`, `format` (strings or null).
- `constraints` (object, refs `#/$defs/optimization`) — Optimization-style constraints (objective, decision variables, hard/soft constraints, affected parties, tradeoffs, feasibility, sensitivity).

## 2. Claims

Each claim is a single assertion with full epistemic metadata.

| Field | Type | Notes |
| ------- | ------ | ------- |
| `claim_id` | string, required, minLength 1 | Stable identifier |
| `text` | string, required, minLength 1 | The claim itself |
| `epistemic_status` | enum | `source_reported_fact`, `direct_observation`, `calculation`, `inference`, `causal_hypothesis`, `opinion_or_recommendation`, `unknown` |
| `support_status` | enum | `supported`, `partly_supported`, `unsupported`, `conflicting_evidence`, `unverified`, `not_applicable` |
| `source_ids` | string[] (uniqueItems) | References into `sources` array |
| `uncertainty` | string | Human-readable uncertainty statement |
| `verification_criterion` | string \| null | How the claim could be verified |
| `limitations` | string[] | Known limitations of the claim |

## 3. Sources

Describes every external or user-provided source.

| Field | Type | Notes |
| ------- | ------ | ------- |
| `source_id` | string, required, minLength 1 | Stable identifier |
| `title` | string, required, minLength 1 | Source title |
| `author_or_publisher` | string \| null | |
| `url` | string \| null (format: uri) | |
| `publication_date` | string \| null | |
| `accessed_date` | string \| null | |
| `access_status` | enum | `opened_and_reviewed`, `metadata_only`, `inaccessible`, `not_checked` |
| `source_category` | enum | `peer_reviewed_research`, `preprint`, `legal_authority`, `government_publication`, `technical_standard`, `recognized_institutional_research`, `primary_data`, `news_or_commentary`, `user_provided`, `other` |
| `claims_supported` | string[] (uniqueItems) | References into `claims` array |
| `support_summary` | string | Summary of what this source supports |
| `relevant_passage_or_result` | string \| null | Excerpt or result |
| `units_and_baseline_checked` | boolean | Whether units/baselines were verified |
| `limitations` | string[] | |

## 4. Artifacts

Tracks scripts, files, commands, packages, datasets.

| Field | Type | Notes |
| ------- | ------ | ------- |
| `artifact_id` | string | Stable identifier |
| `kind` | enum | `script`, `file`, `command`, `package`, `dataset`, `other` |
| `identifier` | string | Path, command, package name, etc. |
| `existence_status` | enum | `confirmed`, `absent`, `inaccessible`, `not_checked` |
| `inspection_status` | enum | `inspected`, `not_inspected`, `not_applicable` |
| `execution_status` | enum | `ran_successfully`, `ran_with_error`, `not_run`, `not_applicable` |
| `purpose` | string \| null | |
| `inputs_outputs_dependencies` | string[] | |
| `risk_review` | string | Required risk assessment text |
| `dry_run_or_sandbox_used` | boolean | |
| `result_summary` | string \| null | |

## 5. Reasoning

Captures the internal reasoning trace.

| Field | Type | Notes |
| ------- | ------ | ------- |
| `summary` | string | High-level reasoning summary |
| `assumptions` | string[] | |
| `unknowns` | string[] | Things not known |
| `causal_assessment` | object | Refs `#/$defs/causal_assessment` |
| `independent_check` | object | Refs `#/$defs/independent_check` |
| `alternatives_considered` | string[] | |
| `corrections` | object[] | `previous_claim`, `reason`, `new_evidence_or_error` |

### Causal Assessment

| Field | Type | Notes |
| ------- | ------ | ------- |
| `status` | enum | `not_assessed`, `association_only`, `causal_evidence_limited`, `causal_support_in_stated_scope`, `causal_claim_not_supported` |
| `proposed_mechanism` | string \| null | |
| `population_and_context` | string \| null | |
| `time_order` | string \| null | |
| `confounders` | string[] | |
| `alternative_explanations` | string[] | |
| `evidence_design` | string \| null | |
| `claim_limit` | string | Required bound on causal claims |

### Independent Check

| Field | Type | Notes |
| ------- | ------ | ------- |
| `performed` | boolean | |
| `method` | enum | `primary_source_review`, `separate_calculation`, `held_out_data`, `independent_test`, `independent_reviewer`, `same_model_repass`, `none` |
| `independent_of_generator` | boolean | `same_model_repass` forces `false` |
| `result` | string \| null | |
| `evidence_ids` | string[] | |
| `limitations` | string[] | |

## 6. Actions

Tracks external or state-changing operations with explicit approval.

| Field | Type | Notes |
| ------- | ------ | ------- |
| `action_id` | string | Stable identifier |
| `action_type` | enum | `draft_only`, `read_only`, `external_message`, `publish`, `purchase`, `delete`, `submit`, `access_change`, `data_disclosure`, `other` |
| `external_or_state_changing` | boolean | |
| `status` | enum | `not_started`, `drafted`, `awaiting_approval`, `approved`, `declined`, `completed`, `blocked` |
| `approval` | object | `required`, `explicit`, `prior_to_execution` (booleans), `approver`, `approved_scope`, `approval_timestamp` (strings/null) |
| `action_summary` | string | |
| `target` | string \| null | |
| `inputs` | string[] | |
| `permissions` | string[] | |
| `effects` | string[] | |
| `side_effects` | string[] | |
| `reversibility` | enum | `reversible`, `partly_reversible`, `irreversible`, `unknown` |

**Conditional rule:** If `external_or_state_changing` is `true` and `status` is `approved` or `completed`, then `approval.required`, `approval.explicit`, and `approval.prior_to_execution` must all be `true`.

## 7. Evaluation

| Field | Type | Notes |
| ------- | ------ | ------- |
| `status` | enum | `not_evaluated`, `proposed_test`, `tested`, `independently_reviewed` |
| `benchmark_claim` | string | |
| `benchmark_details` | object | Refs `#/$defs/benchmark` |
| `limitations` | string[] | |

**Conditional rule:** If `status` is `tested` or `independently_reviewed`, then `benchmark_details.status` must be `"completed"`.

### Benchmark

| Field | Type | Notes |
| ------- | ------ | ------- |
| `status` | enum | `not_run`, `proposed`, `completed` |
| `model_names_and_versions` | string[] | |
| `test_set` | string \| null | |
| `sample_size` | integer \| null (min 0) | |
| `scoring_method` | string \| null | |
| `results` | string[] | |
| `date` | string \| null | |
| `reproducibility_details` | string \| null | |
| `known_limitations` | string[] | |

## 8. Attribution

| Field | Type | Notes |
| ------- | ------ | ------- |
| `human_author` | string \| null | |
| `attribution_basis` | enum | `user_provided`, `independently_verified`, `not_specified` |
| `ai_role` | string | Const `"supporting_tool"` |
| `notes` | string \| null | |

## 9. Pre-Response Checks

Eleven required boolean gates:

1. `scope_adherence`
2. `claim_support_reviewed`
3. `evidence_inference_separated`
4. `uncertainty_disclosed`
5. `causal_wording_reviewed`
6. `independence_reviewed`
7. `constraints_explicit`
8. `approval_boundary_respected`
9. `privacy_minimized`
10. `attribution_accurate`
11. `capability_claims_accurate`

Plus optional `notes` (string[]).

## 10. Optimization (referenced by task.constraints and $defs)

| Field | Type | Notes |
| ------- | ------ | ------- |
| `objective` | string \| null | |
| `decision_variables` | string[] | |
| `hard_constraints` | string[] | |
| `soft_preferences` | string[] | |
| `affected_parties` | string[] | |
| `tradeoffs` | string[] | |
| `feasibility_status` | enum | `not_applicable`, `feasible`, `infeasible`, `uncertain` |
| `sensitivity_review` | string | |
| `unresolved_constraints` | string[] | |

## Design Principles

1. **Evidence-grounded:** Every claim carries `source_ids` and `support_status`; every source carries `access_status` and `limitations`.
2. **User-controlled:** `attribution.ai_role` is fixed to `"supporting_tool"`; `human_author` and `attribution_basis` make human responsibility explicit.
3. **Approval-gated:** State-changing actions require explicit, prior approval before `approved`/`completed` status.
4. **Uncertainty-disclosed:** Every claim has an `uncertainty` field; reasoning has `unknowns`; evaluation has `limitations`.
5. **No additional properties:** Strict `additionalProperties: false` at every level prevents schema drift.

## Validation Notes

- Schema conformance indicates structural validity only. It does not verify factual accuracy, source quality, or safe execution.
- Conditional (`if`/`then`) rules govern approval requirements for actions and benchmark completion for tested evaluations.
- `same_model_repass` independent checks are explicitly marked `independent_of_generator: false`.
