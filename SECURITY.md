# Security Policy

## Supported Versions

This repository is a design-and-specification package rather than a deployable application, so there are no versioned releases with security support.

| Version | Supported |
| ------- | --------- |
| main    | ✅        |

## Reporting a Vulnerability

If you discover a security concern in the design documents, schema, or the `catalog_engine.py` reference implementation, please open an issue describing the issue and its impact. Do not disclose potential vulnerabilities publicly before they have been addressed.

Please do not submit secrets, keys, credentials, or personally identifiable information through issues or pull requests.

## Scope

- In scope: `catalog_engine.py`, `agent-design.schema.json`, design documents (`*.md`).
- Out of scope: third-party dependencies listed in `requirements.txt` (e.g. `jsonschema`).

## Safe references

The design documents cite public guidance from trusted institutions (e.g. NIST AI Risk Management Framework). Those references are safe to consult and are not a substitute for independent security review of any implementation built from this design.