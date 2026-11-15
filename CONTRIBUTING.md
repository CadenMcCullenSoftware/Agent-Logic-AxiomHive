# Contributing to Agent Docs

Thank you for contributing. This repository is a policy-and-specification package for an evidence-grounded, user-controlled AI research assistant. It is documentation-forward and intentionally lightweight: there is no production application code or deployable service here.

## How to contribute

1. Fork the repository and create a branch from `main`.
2. Make your changes. Prefer small, focused commits with clear messages.
3. Run the checks below before opening a pull request.
4. Open a pull request against `main`. Describe what changed and why.

## Repository contents

- Design documents and policy principles under the root directory (`.md` files).
- `agent-design.schema.json` — JSON Schema for agent records.
- `example-agent-record.json` — a sample valid record.
- `catalog_engine.py` — a small executable semantic reasoning engine over a catalog knowledge graph.
- `test_catalog_engine.py` — unit tests for `catalog_engine.py`.

## Running checks

The Python catalog engine has tests and a self-test CLI:

```
python3 -m unittest -v
python3 catalog_engine.py --tool validate
python3 catalog_engine.py --tool selftest --database :memory:
```

Install the dependency:

```
pip install -r requirements.txt
```

## Pull request expectations

- Keep changes scoped to a single concern.
- Update documentation when behavior or the schema changes.
- Add or update tests for any change to `catalog_engine.py`.
- Ensure `python3 -m unittest -v` passes.
- Do not commit secrets, keys, or credentials.

## Questions

Open an issue for questions about the design, schema, or principles.