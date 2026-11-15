# Catalog-as-a-Model Design

The catalog turns the repository's design documents into a source-linked graph
that a reasoning process can query. It is an executable index and rule substrate,
not a trained model or an autonomous decision-maker.

## Layers

1. **Meta-model** — [catalog-meta-model.json](./catalog-meta-model.json) defines
   the allowed node and edge shapes, epistemic states, validity scopes, and rule
   records. `CONFLICTS_WITH` and `CONTRADICTS` edges require a non-empty
   `resolution_rule`.
2. **Catalog** — [catalog-model.json](./catalog-model.json) instantiates the
   graph. Artifact nodes identify source documents; nodes and edges cite those
   artifacts as provenance. Edges connect catalog entities, while rule records
   carry executable logic.
3. **Engine** — [catalog_engine.py](./catalog_engine.py) validates and loads the
   catalog into SQLite, then exposes metadata lookup, keyword search, directed
   graph traversal, conflict listing, and deterministic rule evaluation.

## Validation and provenance

The engine validates the meta-model as Draft 2020-12 JSON Schema, validates the
catalog against it, then checks graph endpoints, unique identifiers, rule-node
links, and provenance references. Validation happens before database changes.
The database replacement itself is transactional, so an insertion failure
cannot leave a partial catalog.

These checks establish structural consistency and traceable identifiers. They
do not establish that a source is accurate, that a claim is true, or that a
resolution is appropriate.

## Reasoning behavior and limits

- `search_nodes` is a case-insensitive substring search over node IDs, titles,
  and summaries; it is not embedding-based semantic search.
- `traverse_graph` follows outgoing edges only. Results are bounded by the
  requested hop depth.
- Conflict-resolution text is required and reported, but is not interpreted or
  executed by the engine. A caller must supply context and evaluate any
  applicable executable rule.
- The JsonLogic evaluator intentionally supports a small, documented subset:
  `var`, `==`, `!=`, `>`, `<`, `and`, `or`, `in`, `if`, and `missing`. It uses
  JSON-value truthiness, strict value equality (with numeric int/float
  equivalence), and numeric-only ordering. Unsupported operators or malformed
  operands produce explicit errors rather than guessed results.
- Rule evaluation returns `passed` or `failed` only for boolean results.
  Non-boolean results are `indeterminate`; the evaluator does not turn prose
  outcomes such as `"PASS"` into authorization.

## Run and validate

Install the single runtime dependency, then run:

```sh
python3 -m pip install -r requirements.txt
python3 catalog_engine.py --tool validate
python3 catalog_engine.py --tool selftest --database :memory:
python3 -m unittest -v
```

The CLI accepts `--database :memory:` to avoid creating a local SQLite file.
Other commands use `catalog.db` by default and reload the JSON catalog on each
invocation.
