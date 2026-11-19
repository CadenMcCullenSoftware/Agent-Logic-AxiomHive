#!/usr/bin/env python3
"""
app.py — Web UI for the Catalog Reasoning Engine.

Exposes the catalog engine's reasoning tools as a browser interface:
  - Meta-model (Layer 1 grammar)
  - Node search with filters
  - Node detail view
  - Graph traversal (subgraph walk)
  - JsonLogic rule evaluation
  - Conflict / supersession detection
  - Catalog validation

Run:
  python3 app.py
"""
from __future__ import annotations

import ipaddress
import json
import os
import sys
import threading
import webbrowser
from typing import Any

from catalog_engine import (
    CatalogStore,
    CatalogValidationError,
    ReasoningEngine,
    evaluate_jsonlogic,
    validate_catalog,
)
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
META_MODEL_PATH = os.path.join(BASE_DIR, "catalog-meta-model.json")
CATALOG_PATH = os.path.join(BASE_DIR, "catalog-model.json")
DB_PATH = os.path.join(BASE_DIR, "catalog.db")

app = Flask(__name__)


def _debug_mode_enabled(host: str, requested: bool) -> bool:
    if not requested:
        return False
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    with open(META_MODEL_PATH) as f:
        meta = json.load(f)
    with open(CATALOG_PATH) as f:
        cat = json.load(f)
    return meta, cat


def new_engine(database: str = DB_PATH) -> ReasoningEngine:
    meta, cat = load_inputs()
    validate_catalog(cat, meta)
    store = CatalogStore(database)
    store.load_catalog(cat, meta)
    return ReasoningEngine(store)


@app.get("/")
def index():
    meta, cat = load_inputs()
    return render_template(
        "index.html",
        meta_model_version=cat.get("meta_model_version"),
        node_count=len(cat.get("nodes", [])),
        edge_count=len(cat.get("edges", [])),
        rule_count=len(cat.get("rules", [])),
    )


@app.get("/meta-model")
def meta_model():
    meta, _ = load_inputs()
    return render_template("meta_model.html", meta_model=meta)


@app.get("/nodes")
def nodes():
    eng = new_engine(":memory:")
    try:
        query = request.args.get("query", "")
        node_type = request.args.get("node_type", "") or None
        status = request.args.get("status", "") or None
        limit = int(request.args.get("limit", "50"))
        filters: dict[str, Any] = {}
        if node_type:
            filters["node_type"] = node_type
        if status:
            filters["status"] = status
        results = eng.search_nodes(query, filters if filters else None, limit=limit)
        node_types = sorted(
            {n["node_type"] for n in results}
        )
        return render_template(
            "nodes.html",
            nodes=results,
            query=query,
            node_type=node_type or "",
            status=status or "",
            limit=limit,
            node_types=node_types,
        )
    finally:
        eng.store.close()


@app.get("/nodes/<node_id>")
def node_detail(node_id):
    eng = new_engine(":memory:")
    try:
        node = eng.store.get_node(node_id)
        if not node:
            return render_template("error.html", message=f"Unknown node: {node_id}"), 404
        incoming = eng.store.incoming_edges(node_id)
        outgoing = eng.store.outgoing_edges(node_id)
        conflicts = eng.store.detect_conflicts(node_id)
        supersessions = eng.store.detect_supersessions(node_id)
        return render_template(
            "node_detail.html",
            node=node,
            incoming=incoming,
            outgoing=outgoing,
            conflicts=conflicts,
            supersessions=supersessions,
        )
    finally:
        eng.store.close()


@app.get("/traverse")
def traverse():
    eng = new_engine(":memory:")
    try:
        node_id = request.args.get("node", "")
        edge_types_raw = request.args.get("edge_types", "")
        depth = int(request.args.get("depth", "2"))
        edge_types = [t.strip() for t in edge_types_raw.split(",") if t.strip()] or None
        result = None
        error = None
        if node_id:
            try:
                result = eng.traverse_graph(node_id, edge_types, depth)
            except ValueError as exc:
                error = str(exc)
        return render_template(
            "traverse.html",
            result=result,
            error=error,
            node_id=node_id,
            edge_types=edge_types_raw,
            depth=depth,
        )
    finally:
        eng.store.close()


@app.get("/evaluate")
def evaluate_form():
    eng = new_engine(":memory:")
    try:
        rules = eng.store.conn.execute("SELECT id, title FROM rules ORDER BY id").fetchall()
        return render_template("evaluate.html", rules=[dict(r) for r in rules], result=None)
    finally:
        eng.store.close()


@app.post("/evaluate")
def evaluate_post():
    eng = new_engine(":memory:")
    try:
        rule_id = request.form.get("rule_id", "")
        context_raw = request.form.get("context", "{}")
        try:
            context_vars = json.loads(context_raw)
            if not isinstance(context_vars, dict):
                raise ValueError("JSON context must be an object")
        except ValueError as exc:
            result = None
            error = f"Invalid JSON context: {exc}"
        else:
            result = eng.evaluate_rule(rule_id, context_vars)
            error = None
        rules = eng.store.conn.execute("SELECT id, title FROM rules ORDER BY id").fetchall()
        return render_template(
            "evaluate.html",
            rules=[dict(r) for r in rules],
            result=result,
            error=error,
            rule_id=rule_id,
            context=context_raw,
        ), 400 if error else 200
    finally:
        eng.store.close()


@app.get("/relationships")
def relationships():
    eng = new_engine(":memory:")
    try:
        node_id = request.args.get("node", "") or None
        conflicts = eng.store.detect_conflicts(node_id)
        supersessions = eng.store.detect_supersessions(node_id)
        return render_template(
            "relationships.html",
            conflicts=conflicts,
            supersessions=supersessions,
            node_id=node_id or "",
        )
    finally:
        eng.store.close()


@app.get("/validate")
def validate():
    meta, cat = load_inputs()
    try:
        validate_catalog(cat, meta)
        valid = True
        error = None
        summary = {
            "meta_model_version": cat.get("meta_model_version"),
            "nodes": len(cat.get("nodes", [])),
            "edges": len(cat.get("edges", [])),
            "rules": len(cat.get("rules", [])),
        }
    except CatalogValidationError as exc:
        valid = False
        error = str(exc)
        summary = None
    return render_template("validate.html", valid=valid, error=error, summary=summary)


@app.get("/api/nodes")
def api_nodes():
    eng = new_engine(":memory:")
    try:
        query = request.args.get("query", "")
        node_type = request.args.get("node_type") or None
        status = request.args.get("status") or None
        limit = int(request.args.get("limit", "50"))
        filters: dict[str, Any] = {}
        if node_type:
            filters["node_type"] = node_type
        if status:
            filters["status"] = status
        results = eng.search_nodes(query, filters if filters else None, limit=limit)
        return jsonify(results)
    finally:
        eng.store.close()


@app.get("/api/rules/<rule_id>")
def api_rule(rule_id):
    eng = new_engine(":memory:")
    try:
        rule = eng.store.get_rule(rule_id)
        if not rule:
            return jsonify({"error": f"unknown rule: {rule_id}"}), 404
        return jsonify(rule)
    finally:
        eng.store.close()


@app.post("/api/evaluate")
def api_evaluate():
    eng = new_engine(":memory:")
    try:
        body = request.get_json(force=True) or {}
        rule_id = body.get("rule_id", "")
        context_vars = body.get("context", {})
        result = eng.evaluate_rule(rule_id, context_vars)
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400
    finally:
        eng.store.close()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Catalog Reasoning Engine browser UI")
    ap.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=5000, help="Port to bind (default: 5000)")
    ap.add_argument(
        "--browser",
        action="store_true",
        help="Open the default web browser automatically",
    )
    debug_group = ap.add_mutually_exclusive_group()
    debug_group.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Run with Flask debug mode on loopback hosts only",
    )
    debug_group.add_argument(
        "--no-debug",
        dest="debug",
        action="store_false",
        help="Run without Flask debug mode (default)",
    )
    ap.set_defaults(debug=False)
    args = ap.parse_args()

    url = f"http://{args.host}:{args.port}/"

    if args.browser:
        def _open_browser():
            webbrowser.open(url)

        threading.Timer(1.25, _open_browser).start()

    debug = _debug_mode_enabled(args.host, args.debug)
    if args.debug and not debug:
        print("Warning: debug mode is disabled for non-loopback hosts.", file=sys.stderr)
    app.run(debug=debug, host=args.host, port=args.port)
