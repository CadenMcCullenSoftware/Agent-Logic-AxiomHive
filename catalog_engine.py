#!/usr/bin/env python3
"""
catalog_engine.py — Layer 3: The Reasoning Engine.

A small, executable semantic model over the catalog knowledge graph.
Exposes four reasoning tools:
  - get_meta_model()        -> the Layer 1 grammar (node/edge/rule types)
  - search_nodes(query, filters) -> semantic/keyword entry-point search
  - traverse_graph(node_id, edge_types, depth) -> deterministic subgraph walk
  - evaluate_rule(rule_id, context_vars) -> JsonLogic rule evaluation

Store: SQLite (nodes, edges, rules tables).  Backed by catalog-meta-model.json
(Layer 1) and catalog-model.json (Layer 2).

Usage:
  python3 catalog_engine.py                 # interactive demo / self-test
  python3 catalog_engine.py --tool get_meta_model
  python3 catalog_engine.py --tool search_nodes --query "approval"
  python3 catalog_engine.py --tool traverse_graph --node node-rule-approval-required-v2 --depth 2
  python3 catalog_engine.py --tool evaluate_rule --rule node-rule-approval-required-v2 \
        --context '{"action":{"external_or_state_changing":true,"status":"approved","approval":{"required":true,"explicit":true,"prior_to_execution":true}}}'
"""
import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
META_MODEL_PATH = os.path.join(BASE_DIR, "catalog-meta-model.json")
CATALOG_PATH = os.path.join(BASE_DIR, "catalog-model.json")
DB_PATH = os.path.join(BASE_DIR, "catalog.db")


# ---------------------------------------------------------------------------
# JsonLogic subset evaluator (deterministic verifier for rule logic_payloads)
# ---------------------------------------------------------------------------
class JsonLogicError(Exception):
    pass


def _jl_var(d, var, context):
    # support dotted paths like "action.approval.required"
    cur = context
    for part in var.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def evaluate_jsonlogic(expr, context):
    """Evaluate a JsonLogic-like expression against `context`."""
    if isinstance(expr, bool):
        return expr
    if isinstance(expr, (int, float, str)) or expr is None:
        return expr
    if isinstance(expr, list):
        return [evaluate_jsonlogic(x, context) for x in expr]
    if not isinstance(expr, dict):
        raise JsonLogicError(f"unsupported expression type: {expr!r}")
    if len(expr) != 1:
        raise JsonLogicError(f"JsonLogic expression must have exactly one operator, got: {expr!r}")
    op, val = next(iter(expr.items()))

    if op == "var":
        if not isinstance(val, str):
            raise JsonLogicError("var expects a string path")
        return _jl_var(context, val, context)

    if op == "==":
        if not isinstance(val, list) or len(val) != 2:
            raise JsonLogicError("== expects [a, b]")
        return evaluate_jsonlogic(val[0], context) == evaluate_jsonlogic(val[1], context)

    if op == "!=":
        if not isinstance(val, list) or len(val) != 2:
            raise JsonLogicError("!= expects [a, b]")
        return evaluate_jsonlogic(val[0], context) != evaluate_jsonlogic(val[1], context)

    if op == ">":
        if not isinstance(val, list) or len(val) != 2:
            raise JsonLogicError("> expects [a, b]")
        return evaluate_jsonlogic(val[0], context) > evaluate_jsonlogic(val[1], context)

    if op == "<":
        if not isinstance(val, list) or len(val) != 2:
            raise JsonLogicError("< expects [a, b]")
        return evaluate_jsonlogic(val[0], context) < evaluate_jsonlogic(val[1], context)

    if op == "and":
        if not isinstance(val, list):
            raise JsonLogicError("and expects an array")
        for item in val:
            if not evaluate_jsonlogic(item, context):
                return False
        return True

    if op == "or":
        if not isinstance(val, list):
            raise JsonLogicError("or expects an array")
        for item in val:
            if evaluate_jsonlogic(item, context):
                return True
        return False

    if op == "in":
        if not isinstance(val, list) or len(val) != 2:
            raise JsonLogicError("in expects [needle, haystack]")
        needle = evaluate_jsonlogic(val[0], context)
        haystack = evaluate_jsonlogic(val[1], context)
        if not isinstance(haystack, list):
            return False
        return needle in haystack

    if op == "if":
        if not isinstance(val, list) or len(val) < 2:
            raise JsonLogicError("if expects [cond, then, else?]")
        cond = evaluate_jsonlogic(val[0], context)
        if cond:
            return evaluate_jsonlogic(val[1], context)
        if len(val) > 2:
            return evaluate_jsonlogic(val[2], context)
        return None

    if op == "missing":
        if not isinstance(val, list) or len(val) != 1:
            raise JsonLogicError("missing expects [var]")
        return _jl_var(context, val[0], context) is None

    raise JsonLogicError(f"unsupported JsonLogic operator: {op}")


# ---------------------------------------------------------------------------
# Store layer (SQLite)
# ---------------------------------------------------------------------------
class CatalogStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS meta_model (
                 key TEXT PRIMARY KEY, value TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS nodes (
                 id TEXT PRIMARY KEY,
                 node_type TEXT,
                 title TEXT,
                 summary TEXT,
                 payload TEXT,
                 epistemic_state TEXT,
                 validity_scope TEXT,
                 reasoning_hints TEXT,
                 source_artifact_id TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS edges (
                 id TEXT PRIMARY KEY,
                 from_id TEXT,
                 to_id TEXT,
                 relation TEXT,
                 reason TEXT,
                 resolution_rule TEXT,
                 epistemic_state TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS rules (
                 id TEXT PRIMARY KEY,
                 title TEXT,
                 logic_payload TEXT,
                 applies_to TEXT,
                 epistemic_state TEXT,
                 validity_scope TEXT)"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(relation)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)")
        self.conn.commit()

    def load_catalog(self, catalog, meta_model):
        c = self.conn.cursor()
        c.execute("DELETE FROM nodes")
        c.execute("DELETE FROM edges")
        c.execute("DELETE FROM rules")
        c.execute("DELETE FROM meta_model")
        c.execute(
            "INSERT INTO meta_model(key, value) VALUES (?, ?)",
            ("meta_model", json.dumps(meta_model)),
        )
        for n in catalog.get("nodes", []):
            c.execute(
                "INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    n["id"],
                    n["node_type"],
                    n["title"],
                    n.get("summary"),
                    json.dumps(n.get("payload")) if n.get("payload") is not None else None,
                    json.dumps(n["epistemic_state"]),
                    json.dumps(n.get("validity_scope")) if n.get("validity_scope") is not None else None,
                    json.dumps(n.get("reasoning_hints")) if n.get("reasoning_hints") is not None else None,
                    n.get("source_artifact_id"),
                ),
            )
        for e in catalog.get("edges", []):
            c.execute(
                "INSERT INTO edges VALUES (?,?,?,?,?,?,?)",
                (
                    e["id"],
                    e["from"],
                    e["to"],
                    e["relation"],
                    e.get("reason"),
                    e.get("resolution_rule"),
                    json.dumps(e["epistemic_state"]),
                ),
            )
        for r in catalog.get("rules", []):
            c.execute(
                "INSERT INTO rules VALUES (?,?,?,?,?,?)",
                (
                    r["id"],
                    r["title"],
                    json.dumps(r["logic_payload"]),
                    json.dumps(r.get("applies_to", [])),
                    json.dumps(r["epistemic_state"]),
                    json.dumps(r.get("validity_scope")) if r.get("validity_scope") is not None else None,
                ),
            )
        self.conn.commit()

    def get_meta_model(self):
        row = self.conn.execute(
            "SELECT value FROM meta_model WHERE key='meta_model'"
        ).fetchone()
        return json.loads(row["value"]) if row else {}

    def search_nodes(self, query="", filters=None, limit=50):
        filters = filters or {}
        sql = "SELECT * FROM nodes WHERE 1=1"
        params = []
        if query:
            like = f"%{query.lower()}%"
            sql += " AND (LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(id) LIKE ?)"
            params.extend([like, like, like])
        if filters.get("node_type"):
            sql += " AND node_type = ?"
            params.append(filters["node_type"])
        if filters.get("status"):
            sql += " AND epistemic_state LIKE ?"
            params.append(f'%"status": "{filters["status"]}"%')
        if filters.get("source_artifact_id"):
            sql += " AND source_artifact_id = ?"
            params.append(filters["source_artifact_id"])
        sql += " ORDER BY id LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._node_from_row(r) for r in rows]

    def get_node(self, node_id):
        row = self.conn.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
        return self._node_from_row(row) if row else None

    def traverse_graph(self, node_id, edge_types=None, depth=2):
        if edge_types is None:
            edge_types = []
        visited = set()
        results = {"nodes": {}, "edges": []}
        frontier = [(node_id, 0)]
        while frontier:
            current, d = frontier.pop(0)
            if current in visited:
                continue
            visited.add(current)
            node = self.get_node(current)
            if node:
                results["nodes"][current] = node
            if d >= depth:
                continue
            for e in self.outgoing_edges(current, edge_types):
                results["edges"].append(e)
                if e["to"] not in visited:
                    frontier.append((e["to"], d + 1))
        return results

    def outgoing_edges(self, node_id, edge_types=None):
        sql = "SELECT * FROM edges WHERE from_id=?"
        params = [node_id]
        if edge_types:
            placeholders = ",".join("?" for _ in edge_types)
            sql += f" AND relation IN ({placeholders})"
            params.extend(edge_types)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._edge_from_row(r) for r in rows]

    def incoming_edges(self, node_id, edge_types=None):
        sql = "SELECT * FROM edges WHERE to_id=?"
        params = [node_id]
        if edge_types:
            placeholders = ",".join("?" for _ in edge_types)
            sql += f" AND relation IN ({placeholders})"
            params.extend(edge_types)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._edge_from_row(r) for r in rows]

    def get_rule(self, rule_id):
        row = self.conn.execute("SELECT * FROM rules WHERE id=?", (rule_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "logic_payload": json.loads(row["logic_payload"]),
            "applies_to": json.loads(row["applies_to"]),
            "epistemic_state": json.loads(row["epistemic_state"]),
            "validity_scope": json.loads(row["validity_scope"]) if row["validity_scope"] else None,
        }

    def detect_conflicts(self, node_id=None):
        """Return edges of relation CONFLICTS_WITH/CONTRADICTS/SUPERSEDES."""
        sql = "SELECT * FROM edges WHERE relation IN ('CONFLICTS_WITH','CONTRADICTS','SUPERSEDES')"
        params = []
        if node_id:
            sql += " AND (from_id=? OR to_id=?)"
            params.extend([node_id, node_id])
        rows = self.conn.execute(sql, params).fetchall()
        return [self._edge_from_row(r) for r in rows]

    def _node_from_row(self, r):
        return {
            "id": r["id"],
            "node_type": r["node_type"],
            "title": r["title"],
            "summary": r["summary"],
            "payload": json.loads(r["payload"]) if r["payload"] else None,
            "epistemic_state": json.loads(r["epistemic_state"]),
            "validity_scope": json.loads(r["validity_scope"]) if r["validity_scope"] else None,
            "reasoning_hints": json.loads(r["reasoning_hints"]) if r["reasoning_hints"] else None,
            "source_artifact_id": r["source_artifact_id"],
        }

    def _edge_from_row(self, r):
        return {
            "id": r["id"],
            "from": r["from_id"],
            "to": r["to_id"],
            "relation": r["relation"],
            "reason": r["reason"],
            "resolution_rule": r["resolution_rule"],
            "epistemic_state": json.loads(r["epistemic_state"]),
        }

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# Reasoning tools
# ---------------------------------------------------------------------------
class ReasoningEngine:
    def __init__(self, store):
        self.store = store

    def get_meta_model(self):
        return self.store.get_meta_model()

    def search_nodes(self, query="", filters=None, limit=50):
        return self.store.search_nodes(query, filters, limit)

    def traverse_graph(self, node_id, edge_types=None, depth=2):
        node = self.store.get_node(node_id)
        if not node:
            raise ValueError(f"unknown node: {node_id}")
        return {
            "root": node,
            "subgraph": self.store.traverse_graph(node_id, edge_types, depth),
        }

    def evaluate_rule(self, rule_id, context_vars=None):
        context_vars = context_vars or {}
        rule = self.store.get_rule(rule_id)
        if not rule:
            raise ValueError(f"unknown rule: {rule_id}")
        payload = rule.get("logic_payload") or {}
        try:
            result = evaluate_jsonlogic(payload, context_vars)
        except JsonLogicError as exc:
            return {
                "rule_id": rule_id,
                "rule_title": rule["title"],
                "status": "error",
                "error": str(exc),
                "epistemic_state": rule["epistemic_state"],
            }
        return {
            "rule_id": rule_id,
            "rule_title": rule["title"],
            "status": "passed" if result is True else ("failed" if result is False else "indeterminate"),
            "result": result,
            "epistemic_state": rule["epistemic_state"],
            "validity_scope": rule["validity_scope"],
        }


# ---------------------------------------------------------------------------
# CLI / self-test
# ---------------------------------------------------------------------------
def load_catalog_files():
    with open(META_MODEL_PATH) as f:
        meta = json.load(f)
    with open(CATALOG_PATH) as f:
        cat = json.load(f)
    return meta, cat


def print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="Catalog reasoning engine (Layer 3)")
    ap.add_argument("--tool", choices=["get_meta_model", "search_nodes", "traverse_graph", "evaluate_rule", "conflicts", "selftest"],
                    default="selftest")
    ap.add_argument("--query", default="")
    ap.add_argument("--node", default="")
    ap.add_argument("--rule", default="")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--edge-types", default="", help="comma-separated relations")
    ap.add_argument("--context", default="{}", help="JSON context for evaluate_rule")
    ap.add_argument("--node-type", default="")
    ap.add_argument("--status", default="")
    args = ap.parse_args()

    meta, cat = load_catalog_files()
    store = CatalogStore()
    store.load_catalog(cat, meta)
    eng = ReasoningEngine(store)

    try:
        if args.tool == "get_meta_model":
            print_json(eng.get_meta_model())
        elif args.tool == "search_nodes":
            filters = {}
            if args.node_type:
                filters["node_type"] = args.node_type
            if args.status:
                filters["status"] = args.status
            print_json(eng.search_nodes(args.query, filters if filters else None))
        elif args.tool == "traverse_graph":
            et = [t.strip() for t in args.edge_types.split(",") if t.strip()] or None
            print_json(eng.traverse_graph(args.node, et, args.depth))
        elif args.tool == "evaluate_rule":
            ctx = json.loads(args.context)
            print_json(eng.evaluate_rule(args.rule, ctx))
        elif args.tool == "conflicts":
            print_json(eng.store.detect_conflicts(args.node if args.node else None))
        else:
            # selftest: exercise the 4-step reasoning loop over the catalog
            print("=== SELF-TEST: Catalog-as-a-Model reasoning loop ===")
            mm = eng.get_meta_model()
            print(f"[Orient] meta_model_version={cat.get('meta_model_version')} node_types={[p for p in mm['$defs']['node']['properties']['node_type']['enum']]}")

            hits = eng.search_nodes("approval", {"status": "canonical"})
            print(f"[Extract] search 'approval' canonical -> {[h['id'] for h in hits]}")

            sub = eng.traverse_graph("node-rule-approval-required-v2", depth=2)
            rels = [e["relation"] for e in sub["subgraph"]["edges"]]
            print(f"[Traverse] v2 approval rule subgraph edges: {rels}")
            print(f"           SUPERSEDES present: {'SUPERSEDES' in rels}")

            ctx_pass = {"action": {"external_or_state_changing": True, "status": "approved",
                                    "approval": {"required": True, "explicit": True, "prior_to_execution": True}}}
            ctx_fail = {"action": {"external_or_state_changing": True, "status": "approved",
                                    "approval": {"required": False, "explicit": True, "prior_to_execution": True}}}
            r1 = eng.evaluate_rule("node-rule-approval-required-v2", ctx_pass)
            r2 = eng.evaluate_rule("node-rule-approval-required-v2", ctx_fail)
            print(f"[Reason] approval rule pass-case -> {r1['status']} ({r1['result']})")
            print(f"[Reason] approval rule fail-case -> {r2['status']} ({r2['result']})")

            conf = eng.store.detect_conflicts()
            print(f"[Verify] conflict/supersede edges detected: {[c['id'] for c in conf]}")
            for c in conf:
                print(f"           {c['from']} --{c['relation']}-> {c['to']} | {c.get('resolution_rule') or c.get('reason')}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
