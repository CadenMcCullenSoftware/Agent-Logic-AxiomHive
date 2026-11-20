# Evidence-Sourcing Standards (Axiom Hive Technology Principles Alignment)

**Status:** Governance/quality standard (draft)  
**Purpose:** Ensure advancements and system outputs are factual, non-opinion-driven, and grounded in evidence-sourced, publicly tested designs for the multi-agent swarm system design.

## Core principles

1. **Factual, non-opinion framing:** Material claims are presented as labeled Evidence, Inference, Hypothesis, or Opinion. Opinions/recommendations are attributed and never presented as verified facts.
2. **Evidence-sourced:** Every verified claim is traceable to identified sources, artifacts, records, or reproducible tests/calculations with access and verification status.
3. **Publicly tested where claimed:** Claims of public testing, benchmarking, validation, or conformance require publicly accessible evidence (or explicitly cited authorized evidence) describing object, method, conditions, results, date/version, and limitations.
4. **No unsourced authority:** AI outputs, fluent explanations, consensus impressions, or institutional prestige are not substitutes for evidence.
5. **Reproducibility and provenance:** Prefer sources and tests with sufficient detail for independent review (versions, inputs, methods, metrics, environments, artifacts).

## Source tiers and use

| Tier | Examples | Use | Minimum record fields |
|---|---|---|---|
| **Primary/public evidence** | peer-reviewed papers, standards/specs, official docs, datasets, public test reports, reproducible experiment artifacts, source code + executed results | Preferred basis for verified technical/factual claims | locator (URL/DOI/path), author/publisher, date/version, accessed date, relevant result, limitations |
| **Institutional/public reporting** | government/institution publications, recognized lab/vendor technical reports with method details | Supporting evidence; assess method transparency and bias | locator, publisher, date, scope/method, access status, limitations |
| **Secondary summaries** | reviews, analyses, reputable journalism/commentary | Context/discovery only unless corroborated; not sole basis for critical technical claims | locator, date, what it summarizes, corroboration status |
| **User-provided/internal artifacts** | project notes, logs, configs, workflow outputs, local test runs | Evidence within authorized scope when verified/inspected | artifact ID/path, verification/execution status, provenance, limitations |
| **Unsourced/generated** | model recall, uncited synthesis, speculative statements | Not verified fact; must be labeled Inference/Hypothesis/Opinion or removed | label, rationale, verification needed |

## Standards for multi-agent swarm system design claims

Claims about swarm/multi-agent architecture, coordination, safety, performance, reliability, or ethics must specify:

- **System boundary:** agents/roles, tools, data flows, orchestration/control plane, human oversight points.
- **Design basis:** cited standards, research, or documented engineering rationale; distinguish adopted controls from proposed ideas.
- **Test evidence:** what was tested (simulation, unit/integration/system, red-team, load/failure), environment/configuration, datasets/scenarios, metrics, baselines, results, and limitations.
- **Public testability:** if described as “publicly tested,” provide accessible references/artifacts; if not publicly available, do not claim public testing.
- **Operational status:** distinguish design intent, reference implementation, tested behavior, and untested assumptions.

## Verification workflow

1. Identify claim type (factual, performance, security, compliance, design).
2. Select appropriate source/test evidence tier.
3. Access and inspect source/artifact; record status and relevant excerpt/result.
4. Correlate evidence to the exact claim; label per information hierarchy.
5. Run pre-output audit (safety, privacy, fairness, technical accuracy).
6. Document unresolved gaps, conflicts, and required follow-up tests/reviews.

## Quality gates

- **Traceability:** every verified claim links to evidence.
- **Separation:** evidence vs inference vs hypothesis vs opinion is explicit.
- **Proportionality:** claim strength does not exceed evidence strength.
- **Currency:** dates/versions and staleness risks are noted.
- **Reviewability:** sufficient detail exists for commander/operator or independent reviewer assessment.
