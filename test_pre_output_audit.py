import json
import tempfile
import unittest
from pathlib import Path

from pre_output_audit import main, validate_audit_record


def valid_record():
    return {
        "audit_id": "audit_test_001",
        "timestamp_utc": "2026-11-20T00:00:00Z",
        "actor": "tester",
        "commander_or_requestor": "commander",
        "output_type": "text",
        "output_scope": "Test output",
        "information_hierarchy_applied": True,
        "unsourced_statements_separated": True,
        "gates": {
            "safety": {"status": "pass", "checks": ["ok"], "evidence": ["e"], "issues": []},
            "privacy": {"status": "pass", "checks": ["ok"], "evidence": ["e"], "issues": []},
            "fairness": {"status": "pass", "checks": ["ok"], "evidence": ["e"], "issues": []},
            "technical_accuracy": {"status": "pass", "checks": ["ok"], "evidence": ["e"], "issues": []},
        },
        "disposition": "release",
        "notes": [],
    }


class PreOutputAuditTests(unittest.TestCase):
    def test_template_like_valid_record_passes(self):
        self.assertEqual(validate_audit_record(valid_record()), [])

    def test_missing_required_fields_fails(self):
        record = {"audit_id": "x"}
        errors = validate_audit_record(record)
        self.assertTrue(any("Missing top-level fields" in e for e in errors))

    def test_fail_gate_requires_issue(self):
        record = valid_record()
        record["disposition"] = "revise"
        record["gates"]["safety"]["status"] = "fail"
        record["gates"]["safety"]["issues"] = []
        errors = validate_audit_record(record)
        self.assertTrue(any("fail status must include at least one issue" in e for e in errors))

    def test_release_cannot_have_failed_gate(self):
        record = valid_record()
        record["gates"]["privacy"]["status"] = "fail"
        record["gates"]["privacy"]["issues"] = ["leak risk"]
        errors = validate_audit_record(record)
        self.assertTrue(any("cannot be release" in e for e in errors))

    def test_release_requires_hierarchy_and_separation(self):
        record = valid_record()
        record["information_hierarchy_applied"] = False
        errors = validate_audit_record(record)
        self.assertTrue(any("information_hierarchy_applied=true" in e for e in errors))

    def test_na_gate_requires_justification_evidence(self):
        record = valid_record()
        record["disposition"] = "release"
        record["gates"]["fairness"]["status"] = "na"
        record["gates"]["fairness"]["evidence"] = []
        errors = validate_audit_record(record)
        self.assertTrue(any("na status must include justification evidence" in e for e in errors))

    def test_cli_validate_json_output(self):
        record = valid_record()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            rc = main(["validate", str(path), "--json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
