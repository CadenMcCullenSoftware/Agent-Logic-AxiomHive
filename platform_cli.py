#!/usr/bin/env python3
"""Command-line entry points for the local research workspace."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from workspace import WorkspaceError, WorkspaceStore, validate_workflow_definition


def main() -> None:
    parser = argparse.ArgumentParser(description="Research workspace operations")
    parser.add_argument("--database", help="Workspace SQLite database path")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("projects", help="List workspace projects")
    validate = commands.add_parser("validate-workflow", help="Validate a workflow JSON file")
    validate.add_argument("definition", type=Path)
    run = commands.add_parser("run-workflow", help="Save and run a workflow for a project")
    run.add_argument("project_id")
    run.add_argument("definition", type=Path)
    run.add_argument("--confirm", action="store_true",
                     help="Confirm authorization to execute this local workflow")
    args = parser.parse_args()
    store = WorkspaceStore(args.database) if args.database else WorkspaceStore()

    if args.command == "projects":
        print(json.dumps(store.list_projects(), indent=2, ensure_ascii=False))
        return
    try:
        definition = json.loads(args.definition.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read workflow definition: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    agent_ids = {agent["id"] for agent in store.list_agents()}
    errors = validate_workflow_definition(definition, agent_ids)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2), file=sys.stderr)
        raise SystemExit(1)
    if args.command == "validate-workflow":
        print(json.dumps({"valid": True, "name": definition["name"]}, indent=2))
        return
    if not args.confirm:
        print("Workflow execution requires --confirm.", file=sys.stderr)
        raise SystemExit(2)
    try:
        workflow_id = store.save_workflow(args.project_id, definition)
        result = store.start_workflow(args.project_id, workflow_id)
    except WorkspaceError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
