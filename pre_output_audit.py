#!/usr/bin/env python3
"""Validate and summarize pre-output audit checklist records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REQUIRED_TOP_LEVEL = {
    "audit_id",
    "timestamp_utc",
    "actor",
    "commander_or_requestor",
    "output_type",
    "output_scope",
    "information_hierarchy_applied",
    "unsourced_statements_separated",
    "gates",
    "disposition",
    "notes",
}
REQUIRED_GATES = ("safety", "privacy", "fairness", "technical_accuracy")
VALID_STATUSES = {"pass", "fail", "na"}
VALID_DISPOSITIONS = {"release", "revise", "block"}


class AuditValidationError(ValueError):
    """Raised when an audit checklist record is invalid."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_audit_record(record: Any) -> list[str]:
    errors: list[str] = []
    _require(isinstance(record, dict), "Audit record must be a JSON object.", errors)
    if not isinstance(record, dict):
        return errors

    missing = sorted(REQUIRED_TOP_LEVEL - set(record))
    extra = sorted(set(record) - REQUIRED_TOP_LEVEL)
    if missing:
        errors.append(f"Missing top-level fields: {', '.join(missing)}.")
    if extra:
        errors.append(f"Unsupported top-level fields: {', '.join(extra)}.")

    for field in ("audit_id", "timestamp_utc", "actor", "commander_or_requestor", "output_type", "output_scope"):
        value = record.get(field)
        _require(isinstance(value, str) and value.strip(), f"{field} must be a non-empty string.", errors)

    for field in ("information_hierarchy_applied", "unsourced_statements_separated"):
        _require(isinstance(record.get(field), bool), f"{field} must be a boolean.", errors)

    disposition = record.get("disposition")
    _require(isinstance(disposition, str) and disposition in VALID_DISPOSITIONS,
             "disposition must be one of: release, revise, block.", errors)
    notes = record.get("notes")
    _require(isinstance(notes, list) and all(isinstance(n, str) for n in notes),
             "notes must be an array of strings.", errors)

    gates = record.get("gates")
    _require(isinstance(gates, dict), "gates must be an object.", errors)
    if isinstance(gates, dict):
        missing_gates = sorted(set(REQUIRED_GATES) - set(gates))
        extra_gates = sorted(set(gates) - set(REQUIRED_GATES))
        if missing_gates:
            errors.append(f"Missing gates: {', '.join(missing_gates)}.")
        if extra_gates:
            errors.append(f"Unsupported gates: {', '.join(extra_gates)}.")
        for gate_name in REQUIRED_GATES:
            gate = gates.get(gate_name)
            if not isinstance(gate, dict):
                errors.append(f"gates.{gate_name} must be an object.")
                continue
            status = gate.get("status")
            _require(isinstance(status, str) and status in VALID_STATUSES,
                     f"gates.{gate_name}.status must be pass, fail, or na.", errors)
            for list_field in ("checks", "evidence", "issues"):
                value = gate.get(list_field)
                _require(isinstance(value, list) and all(isinstance(item, str) for item in value),
                         f"gates.{gate_name}.{list_field} must be an array of strings.", errors)
            if status == "fail":
                issues = gate.get("issues", [])
                _require(isinstance(issues, list) and len(issues) > 0,
                         f"gates.{gate_name} with fail status must include at least one issue.", errors)
            if status == "pass":
                checks = gate.get("checks", [])
                evidence = gate.get("evidence", [])
                _require(isinstance(checks, list) and len(checks) > 0,
                         f"gates.{gate_name} with pass status must include at least one check.", errors)
                _require(isinstance(evidence, list) and len(evidence) > 0,
                         f"gates.{gate_name} with pass status must include supporting evidence.", errors)
            if status == "na":
                evidence = gate.get("evidence", [])
                _require(isinstance(evidence, list) and len(evidence) > 0,
                         f"gates.{gate_name} with na status must include justification evidence.", errors)

    # Consistency checks
    if isinstance(record.get("gates"), dict):
        any_fail = any(
            isinstance(record["gates"].get(g), dict) and record["gates"][g].get("status") == "fail"
            for g in REQUIRED_GATES
        )
        if record.get("disposition") == "release" and any_fail:
            errors.append("disposition cannot be release when any gate has fail status.")
        if record.get("disposition") == "release":
            if record.get("information_hierarchy_applied") is not True:
                errors.append("disposition release requires information_hierarchy_applied=true.")
            if record.get("unsourced_statements_separated") is not True:
                errors.append("disposition release requires unsourced_statements_separated=true.")
        if any_fail and record.get("disposition") == "block":
            # block is allowed for fail, but revise is more typical; no hard error
            pass

    return errors


def load_record(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditValidationError(f"Could not read audit record: {exc}") from exc


def summarize(record: dict[str, Any]) -> dict[str, Any]:
    gates = record.get("gates", {}) if isinstance(record, dict) else {}
    statuses = {
        name: (gates.get(name, {}) or {}).get("status")
        for name in REQUIRED_GATES
        if isinstance(gates, dict)
    }
    return {
        "audit_id": record.get("audit_id"),
        "disposition": record.get("disposition"),
        "gate_statuses": statuses,
        "information_hierarchy_applied": record.get("information_hierarchy_applied"),
        "unsourced_statements_separated": record.get("unsourced_statements_separated"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-output audit checklist validator")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate an audit checklist JSON file")
    validate.add_argument("path", type=Path)
    validate.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args(argv)

    try:
        record = load_record(args.path)
    except AuditValidationError as exc:
        if args.json:
            print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        else:
            print(str(exc), file=sys.stderr)
        return 2

    errors = validate_audit_record(record)
    result = {"valid": not errors, "errors": errors}
    if isinstance(record, dict):
        result["summary"] = summarize(record)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if errors:
            print("INVALID", file=sys.stderr)
            for err in errors:
                print(f"- {err}", file=sys.stderr)
        else:
            print("VALID")
            print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
