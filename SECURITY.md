# Security Policy

## Supported Versions

This repository is primarily a design-and-specification package with local reference implementations, not a production deployment package. There are no versioned releases with security support.

| Version | Supported |
| ------- | --------- |
| main    | ✅        |

## Reporting a Vulnerability

If you discover a security concern in the design documents, schema, or reference implementation modules, please open a private security advisory if available; otherwise open an issue describing the impact without including exploit details, secrets, credentials, or personally identifiable information. Do not disclose potential vulnerabilities publicly before they have been assessed.

Please do not submit secrets, keys, credentials, or personally identifiable information through issues or pull requests.

## Scope

- **In scope (design/specification):** `agent-design.schema.json`, design and policy documents (`*.md`).
- **In scope (reference implementation):** `catalog_engine.py`, `app.py`, `workspace.py`, `platform_cli.py`, and repository test scripts. These modules include network retrieval, SQLite persistence, workflow validation/execution, and web/CLI interfaces and should be reviewed for security issues.
- **Out of scope:** third-party dependencies listed in `requirements.txt` (e.g. `jsonschema`, `flask`) except for repository-specific misuse or insecure integration.
- **Deployment boundary:** the local workspace is a reference implementation without production authentication, authorization, or multi-user isolation guarantees. Independent security, privacy, and deployment review is required before exposing it beyond a trusted local environment.

## Safe references

The design documents cite public guidance from trusted institutions (e.g. NIST AI Risk Management Framework). Those references are safe to consult and are not a substitute for independent security review of any implementation built from this design.