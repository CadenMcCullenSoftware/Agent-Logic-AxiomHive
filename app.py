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
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from workspace import (
    CLAIM_CLASSES,
    CLAIM_SUPPORT_STATUSES,
    CORRECTION_CATEGORIES,
    OUTPUT_REVIEW_GATES,
    WORKSPACE_DB_PATH,
    WorkspaceError,
    WorkspaceStore,
    retrieve_https_source,
    validate_workflow_definition,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
META_MODEL_PATH = os.path.join(BASE_DIR, "catalog-meta-model.json")
CATALOG_PATH = os.path.join(BASE_DIR, "catalog-model.json")
DB_PATH = os.path.join(BASE_DIR, "catalog.db")
WORKSPACE_DB = os.environ.get("WORKSPACE_DB_PATH", WORKSPACE_DB_PATH)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)


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


def new_workspace() -> WorkspaceStore:
    return WorkspaceStore(WORKSPACE_DB)


def workflow_draft() -> str:
    return json.dumps({
        "name": "Research review",
        "version": "1.0",
        "modules": ["projects", "workflows", "tasks", "sources", "corrections"],
        "steps": [
            {"id": "review-sources", "title": "Review collected sources",
             "task_type": "review_sources", "config": {}, "depends_on": []},
            {"id": "organize-corrections", "title": "Organize corrections",
             "task_type": "organize_corrections", "config": {},
             "depends_on": ["review-sources"]},
            {"id": "human-review", "title": "Present for human review",
             "task_type": "manual_review",
             "config": {"prompt": "Review the organized project material."},
             "depends_on": ["organize-corrections"]},
        ],
    }, indent=2)


def _form_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _project_or_404(store: WorkspaceStore, project_id: str) -> dict[str, Any] | None:
    project = store.get_project(project_id)
    if project is None:
        return None
    return project


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


@app.get("/workspace")
def workspace_home():
    store = new_workspace()
    return render_template("workspace_index.html", projects=store.list_projects())


@app.post("/workspace/projects")
def workspace_create_project():
    store = new_workspace()
    try:
        project_id = store.create_project(
            request.form.get("name", ""), request.form.get("objective", ""),
            request.form.get("description", ""),
        )
    except WorkspaceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("workspace_home"))
    return redirect(url_for("project_detail", project_id=project_id))


@app.post("/projects/<project_id>/update")
def project_update(project_id: str):
    store = new_workspace()
    try:
        store.update_project(
            project_id, request.form.get("name", ""),
            request.form.get("objective", ""), request.form.get("description", ""),
        )
        flash("Project information updated.", "success")
    except WorkspaceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.get("/projects/<project_id>")
def project_detail(project_id: str):
    store = new_workspace()
    project = _project_or_404(store, project_id)
    if project is None:
        return render_template("error.html", message="Project not found."), 404
    return render_template(
        "project.html", project=project, notes=store.list_notes(project_id),
        sources=store.list_sources(project_id), corrections=store.list_corrections(project_id),
        workflows=store.list_workflows(project_id),
    )


@app.post("/projects/<project_id>/notes")
def project_create_note(project_id: str):
    store = new_workspace()
    if _project_or_404(store, project_id) is None:
        return render_template("error.html", message="Project not found."), 404
    try:
        store.create_note(project_id, request.form.get("title", ""), request.form.get("body", ""))
        flash("Project note saved.", "success")
    except WorkspaceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.post("/projects/<project_id>/sources")
def project_add_source(project_id: str):
    store = new_workspace()
    if _project_or_404(store, project_id) is None:
        return render_template("error.html", message="Project not found."), 404
    try:
        store.add_source(project_id, request.form.get("url", ""), request.form.get("title", ""))
        flash("Source added to the project.", "success")
    except WorkspaceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("project_detail", project_id=project_id) + "#sources")


@app.post("/projects/<project_id>/sources/<source_id>/retrieve")
def project_retrieve_source(project_id: str, source_id: str):
    store = new_workspace()
    source = store.get_source(project_id, source_id)
    if source is None:
        return render_template("error.html", message="Source not found for this project."), 404
    try:
        content_type, content = retrieve_https_source(source["url"])
        store.finish_source_retrieval(source_id, content_type=content_type, content=content)
        flash("Source retrieved and stored for project review.", "success")
    except WorkspaceError as exc:
        store.finish_source_retrieval(source_id, error=str(exc))
        flash(f"Source retrieval failed: {exc}", "error")
    return redirect(url_for("project_detail", project_id=project_id) + "#sources")


@app.get("/projects/<project_id>/sources/<source_id>")
def project_source_detail(project_id: str, source_id: str):
    store = new_workspace()
    project = _project_or_404(store, project_id)
    source = store.get_source(project_id, source_id)
    if project is None or source is None:
        return render_template("error.html", message="Source not found for this project."), 404
    return render_template("source_detail.html", project=project, source=source)


@app.route("/projects/<project_id>/claims", methods=["GET", "POST"])
def project_claims(project_id: str):
    store = new_workspace()
    project = _project_or_404(store, project_id)
    if project is None:
        return render_template("error.html", message="Project not found."), 404
    if request.method == "POST":
        try:
            store.create_claim(
                project_id,
                request.form.get("text", ""),
                request.form.get("epistemic_class", ""),
                request.form.get("support_status", ""),
                request.form.getlist("source_ids"),
                request.form.get("support_summary", ""),
                request.form.get("uncertainty", ""),
                request.form.get("verification_criterion", ""),
                request.form.get("attribution", ""),
                request.form.get("sources_reviewed") == "yes",
            )
            flash("Claim recorded.", "success")
        except WorkspaceError as exc:
            flash(str(exc), "error")
        return redirect(url_for("project_claims", project_id=project_id))
    return render_template(
        "claims.html", project=project, claims=store.list_claims(project_id),
        sources=store.list_sources(project_id), claim_classes=CLAIM_CLASSES,
        support_statuses=CLAIM_SUPPORT_STATUSES,
    )


@app.route("/projects/<project_id>/audit", methods=["GET", "POST"])
def project_pre_output_audit(project_id: str):
    store = new_workspace()
    project = _project_or_404(store, project_id)
    if project is None:
        return render_template("error.html", message="Project not found."), 404
    if request.method == "POST":
        gates = {}
        for gate_name in OUTPUT_REVIEW_GATES:
            gates[gate_name] = {
                "status": request.form.get(f"{gate_name}_status", ""),
                "checks": _form_lines(request.form.get(f"{gate_name}_checks", "")),
                "evidence": _form_lines(request.form.get(f"{gate_name}_evidence", "")),
                "issues": _form_lines(request.form.get(f"{gate_name}_issues", "")),
            }
        record = {
            "actor": request.form.get("actor", "").strip(),
            "commander_or_requestor": request.form.get("commander_or_requestor", "").strip(),
            "output_type": request.form.get("output_type", "").strip(),
            "output_scope": request.form.get("output_scope", "").strip(),
            "information_hierarchy_applied": request.form.get("information_hierarchy_applied") == "yes",
            "unsourced_statements_separated": request.form.get("unsourced_statements_separated") == "yes",
            "gates": gates,
            "disposition": request.form.get("disposition", ""),
            "notes": _form_lines(request.form.get("notes", "")),
        }
        try:
            audit = store.create_pre_output_audit(project_id, record)
            flash(f"Pre-output audit recorded with disposition: {audit['status']}.", "success")
        except WorkspaceError as exc:
            return render_template(
                "audit.html", project=project, claims=store.list_claims(project_id),
                checks=OUTPUT_REVIEW_GATES, audits=store.list_pre_output_audits(project_id),
                form_data=request.form, errors=str(exc).splitlines(),
            ), 400
        return redirect(url_for("project_pre_output_audit", project_id=project_id))
    audits = store.list_pre_output_audits(project_id)
    return render_template(
        "audit.html", project=project, claims=store.list_claims(project_id),
        checks=OUTPUT_REVIEW_GATES, audits=audits, form_data={}, errors=[],
    )


@app.get("/projects/<project_id>/corrections")
def project_corrections(project_id: str):
    store = new_workspace()
    project = _project_or_404(store, project_id)
    if project is None:
        return render_template("error.html", message="Project not found."), 404
    category = request.args.get("category", "")
    if category and category not in CORRECTION_CATEGORIES:
        category = ""
    return render_template(
        "corrections.html", project=project,
        corrections=store.list_corrections(project_id, category or None),
        categories=CORRECTION_CATEGORIES, selected_category=category,
    )


@app.post("/projects/<project_id>/corrections")
def project_add_correction(project_id: str):
    store = new_workspace()
    if _project_or_404(store, project_id) is None:
        return render_template("error.html", message="Project not found."), 404
    try:
        store.create_correction(
            project_id, request.form.get("category", ""),
            request.form.get("title", ""), request.form.get("body", ""),
        )
        flash("Correction added.", "success")
    except WorkspaceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("project_corrections", project_id=project_id))


@app.route("/projects/<project_id>/workflows", methods=["GET", "POST"])
def project_workflows(project_id: str):
    store = new_workspace()
    project = _project_or_404(store, project_id)
    if project is None:
        return render_template("error.html", message="Project not found."), 404
    draft = workflow_draft()
    errors: list[str] = []
    if request.method == "POST":
        draft = request.form.get("definition", "")
        try:
            definition = json.loads(draft)
            agent_ids = {agent["id"] for agent in store.list_agents()}
            errors = validate_workflow_definition(definition, agent_ids)
            if request.form.get("action") == "save" and not errors:
                store.save_workflow(project_id, definition)
                flash("Validated workflow saved.", "success")
                return redirect(url_for("project_workflows", project_id=project_id))
        except (json.JSONDecodeError, TypeError) as exc:
            errors = [f"Invalid workflow JSON: {exc}"]
        except WorkspaceError as exc:
            errors = str(exc).splitlines()
    return render_template(
        "workflows.html", project=project, workflows=store.list_workflows(project_id),
        draft=draft, errors=errors,
    )


@app.post("/projects/<project_id>/workflows/<workflow_id>/run")
def project_run_workflow(project_id: str, workflow_id: str):
    if request.form.get("confirm_run") != "yes":
        flash("Confirm that you want to run this local workflow.", "error")
        return redirect(url_for("project_workflows", project_id=project_id))
    try:
        run = new_workspace().start_workflow(project_id, workflow_id)
    except WorkspaceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("project_workflows", project_id=project_id))
    return redirect(url_for("workflow_run_detail", run_id=run["id"]))


@app.get("/runs/<run_id>")
def workflow_run_detail(run_id: str):
    run = new_workspace().get_run(run_id)
    if run is None:
        return render_template("error.html", message="Workflow run not found."), 404
    project = new_workspace().get_project(run["project_id"])
    return render_template("run.html", run=run, project=project)


@app.post("/runs/<run_id>/tasks/<task_id>/review")
def workflow_task_review(run_id: str, task_id: str):
    store = new_workspace()
    run = store.get_run(run_id)
    if run is None or task_id not in {task["id"] for task in run["tasks"]}:
        return render_template("error.html", message="Task not found for this workflow run."), 404
    try:
        store.complete_human_review(task_id, request.form.get("review", ""))
    except WorkspaceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("workflow_run_detail", run_id=run_id))


@app.route("/agents", methods=["GET", "POST"])
def agent_coordination():
    store = new_workspace()
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "define":
                store.create_agent(request.form.get("name", ""), request.form.get("specialty", ""))
                flash("Agent definition saved.", "success")
            elif action == "message":
                store.send_agent_message(
                    request.form.get("body", ""),
                    request.form.get("sender_agent_id") or None,
                    request.form.get("recipient_agent_id") or None,
                    request.form.get("project_id") or None,
                )
                flash("Coordination message recorded.", "success")
        except WorkspaceError as exc:
            flash(str(exc), "error")
        return redirect(url_for("agent_coordination"))
    return render_template(
        "agents.html", agents=store.list_agents(), projects=store.list_projects(),
        messages=store.list_agent_messages(),
    )


@app.get("/operations")
def operations_log():
    return render_template("operations.html", events=new_workspace().list_events())


@app.post("/api/workflows/validate")
def api_validate_workflow():
    body = request.get_json(silent=True) or {}
    definition = body.get("definition") if isinstance(body, dict) else None
    agent_ids = {agent["id"] for agent in new_workspace().list_agents()}
    errors = validate_workflow_definition(definition, agent_ids)
    return jsonify({"valid": not errors, "errors": errors})


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
