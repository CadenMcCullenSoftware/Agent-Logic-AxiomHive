# Agent Docs

This repository contains design documentation and schema artifacts for an evidence-grounded, user-controlled research assistant. It is a specification-heavy documentation project rather than an application codebase: the core value is the policy, evaluation, and record-keeping framework for safely building AI-assisted research and action workflows.

## Purpose

The project centers on one idea: an AI assistant should help the user reason and research effectively without usurping the user's judgment, hiding uncertainty, or acting on incomplete evidence.

The materials in this repo emphasize:

- evidence-supported claims over confident guessing
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

- [Preserving user control.md](./Preserving%20user%20control.md)
- [Evidence-supported conclusions.md](./Evidence-supported%20conclusions.md)
- [Principle 2: Explicit approval before automated action.md](./Principle%202:%20Explicit%20approval%20before%20automated%20action.md)
- [Principle 3: Verifying that sources and scripts exist.md](./Principle%203:%20Verifying%20that%20sources%20and%20scripts%20exist.md)
- [Principle 4: Supportive partner stance without reframing opinion as fact.md](./Principle%204:%20Supportive%20partner%20stance%20without%20reframing%20opinion%20as%20fact.md)
- [Compliance versus correctness.md](./Compliance%20versus%20correctness.md)
- [Safe knowledge sharing within operational boundaries.md](./Safe%20knowledge%20sharing%20within%20operational%20boundaries.md)
- [Avoiding unrequested interpretation.md](./Avoiding%20unrequested%20interpretation.md)
- [Attribution and credit in AI-assisted work.md](./Attribution%20and%20credit%20in%20AI-assisted%20work.md)
- [Collective learning without damage.md](./Collective%20learning%20without%20damage.md)
- [SKILL.md](./SKILL.md)

### Additional reference material

- [complete-appendix.pdf](./complete-appendix.pdf)  
  Supplemental appendix material referenced by the design set.

## What the project is not

This repo does not contain a deployable application, package, or service implementation. It is best understood as a policy and specification package for AI safety and research assistant design.

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

## Testing and validation status

This repository does not contain an application codebase or an automated test suite.

What is present:

- structured specification documents
- a JSON Schema file for record validation: [agent-design.schema.json](./agent-design.schema.json)
- an example instance file: [example-agent-record.json](./example-agent-record.json)
- design and policy documentation intended for review, governance, and implementation planning

What is not present:

- application source code in languages such as Python, JavaScript, TypeScript, Go, or Rust
- package manifests such as `package.json`, `requirements.txt`, `pyproject.toml`, or `Cargo.toml`
- automated unit, integration, or end-to-end tests
- runtime build or CI pipeline files

This means the repository's validation is primarily document and schema review rather than executable software verification. The schema and example record can be checked structurally, but there is no application behavior to exercise in this repo itself.

## Code and implementation status

At the moment, this repository is a policy-and-specification project rather than a code implementation. It documents the design of an evidence-grounded, user-controlled reasoning assistant, but it does not include the production code for a deployed assistant, tool layer, or user interface.

In practical terms:

- the repository is best treated as a design reference and governance package
- implementation work would need to be built separately against the principles in these documents
- any code built from this design should still be validated against security, privacy, and evidence-quality requirements before deployment

## Safe web-sourced references

The design set aligns with official public guidance from trusted institutions. Below are safe, authoritative references used to ground the approach:

- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI RMF 1.0: https://doi.org/10.6028/NIST.AI.100-1
- NIST Generative AI Profile: https://doi.org/10.6028/NIST.AI.600-1

These materials emphasize trustworthy AI design, risk management, and governance. They are consistent with the repository's emphasis on evidence quality, user control, clear uncertainty, and risk-aware deployment.

## Summary

In short, this repository defines a practical framework for building AI research assistants that are transparent, cautious, and accountable. It is most useful for teams designing agent workflows where evidence quality, user control, and operational safety matter more than raw conversational fluency.

The repository itself is documentation-forward and intentionally lightweight: there is no production code or automated test suite here, only the design language, schema, and evidence-grounded safety principles needed to guide implementation elsewhere.
