# Contributing to Agent Docs

Thank you for contributing. This repository combines design guidance with a local Flask and SQLite reference workspace for evidence-grounded, user-controlled research operations. It is not a production deployment package or hosted multi-user service.

## How to contribute

1. Fork the repository and create a branch from `main`.
2. Make your changes. Prefer focused, atomic commits with clear messages.
3. Run the checks below before opening a pull request.
4. Open a pull request against `main`. Describe what changed and why.

## Repository contents

- Design documents and policy principles under the root directory (`.md` files).
- `agent-design.schema.json` — JSON Schema for agent records.
- `example-agent-record.json` — a sample valid record.
- `catalog_engine.py` — executable semantic reasoning engine over a catalog knowledge graph
- `test_catalog_engine.py` — unit tests for `catalog_engine.py`
- `app.py` — Flask web UI exposing the catalog engine reasoning tools
- `test_app.py` — UI tests for the Flask application
- `workspace.py` — SQLite-backed projects, sources, claims, pre-output review records, workflows, and coordination
- `pre_output_audit.py` — checklist record validator and CLI
- `templates/` — Flask workspace and catalog pages
- `docs/` — governance, verification, privacy, and threat-model references
- `test_workspace.py` — workspace behavior tests
- `test_pre_output_audit.py` — checklist validator and CLI tests

## Running checks

The Python catalog engine has tests and a self-test CLI, and the Flask application has UI tests:

```
python3 -m pytest -v
python3 catalog_engine.py --tool validate
python3 catalog_engine.py --tool selftest --database :memory:
python3 -m py_compile catalog_engine.py workspace.py platform_cli.py app.py pre_output_audit.py
```

Install the dependencies:

```
pip install -r requirements.txt
```

## Pull request expectations

- Keep changes scoped to a single concern.
- Update documentation when behavior or the schema changes.
- Add or update tests for behavior changes.
- Ensure `python3 -m pytest -v` passes.
- Do not commit secrets, keys, or credentials.

## Questions

Open an issue for questions about the design, schema, or principles.
