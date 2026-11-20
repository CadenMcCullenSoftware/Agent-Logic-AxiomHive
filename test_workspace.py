import json
import tempfile
import unittest
from pathlib import Path

from workspace import (
    WorkspaceError,
    WorkspaceStore,
    validate_https_source_url,
    validate_workflow_definition,
)


class SourceUrlValidationTests(unittest.TestCase):
    def test_accepts_standard_https_url(self):
        host, path, port, query = validate_https_source_url("https://example.org/docs?q=1")
        self.assertEqual((host, path, port, query), ("example.org", "/docs", 443, "q=1"))

    def test_rejects_insecure_or_malformed_urls(self):
        cases = [
            "http://example.org/",
            "https://user:pass@example.org/",
            "https://example.org:8443/",
            "https://example.org/#fragment",
            "notaurl",
            "https:///missing-host",
        ]
        for url in cases:
            with self.subTest(url=url):
                with self.assertRaises(WorkspaceError):
                    validate_https_source_url(url)

    def test_rejects_local_and_non_global_address_literals(self):
        cases = [
            "https://localhost/",
            "https://service.localhost/",
            "https://127.0.0.1/",
            "https://10.0.0.1/",
            "https://192.168.1.10/",
            "https://169.254.169.254/",
            "https://[::1]/",
            "https://[fd00::1]/",
        ]
        for url in cases:
            with self.subTest(url=url):
                with self.assertRaises(WorkspaceError):
                    validate_https_source_url(url)


class WorkflowValidationTests(unittest.TestCase):
    def valid_definition(self):
        return {
            "name": "Review workflow",
            "version": "1.0",
            "modules": ["projects", "workflows", "tasks"],
            "steps": [
                {
                    "id": "review",
                    "title": "Human review",
                    "task_type": "manual_review",
                    "config": {"prompt": "Review collected material."},
                    "depends_on": [],
                }
            ],
        }

    def test_accepts_valid_workflow_definition(self):
        self.assertEqual(validate_workflow_definition(self.valid_definition()), [])

    def test_rejects_missing_or_invalid_structure(self):
        errors = validate_workflow_definition({"name": "x"})
        self.assertTrue(any("Missing top-level properties" in e for e in errors))
        self.assertTrue(any("version must be" in e for e in errors))

    def test_rejects_unknown_module_dependency_and_task_config(self):
        definition = self.valid_definition()
        definition["modules"].append("unknown_mod")
        definition["steps"][0]["task_type"] = "organize_corrections"
        definition["steps"][0]["config"] = {"category": "Z"}
        errors = validate_workflow_definition(definition)
        self.assertTrue(any("Unknown modules" in e for e in errors))
        self.assertTrue(any("requires module 'corrections'" in e for e in errors))
        self.assertTrue(any("category must be one of A, B, C, D, E, F" in e for e in errors))

    def test_rejects_invalid_dependencies_and_unknown_agent(self):
        definition = self.valid_definition()
        definition["modules"].append("agent_coordination")
        definition["steps"].append(
            {
                "id": "second",
                "title": "Second",
                "task_type": "manual_review",
                "config": {"prompt": "Continue"},
                "depends_on": ["missing", "second"],
                "assigned_agent_id": "agt_missing",
            }
        )
        errors = validate_workflow_definition(definition, agent_ids={"agt_known"})
        self.assertTrue(any("earlier step" in e for e in errors))
        self.assertTrue(any("unknown agent" in e for e in errors))


class WorkspaceStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workspace.db")
        self.store = WorkspaceStore(self.db_path)
        self.project_id = self.store.create_project("Project A", "Test objective", "desc")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_project_note_source_and_correction_records(self):
        note_id = self.store.create_note(self.project_id, "Note", "Body")
        source_id = self.store.add_source(self.project_id, "https://example.org/paper", "Paper")
        correction_id = self.store.create_correction(self.project_id, "b", "Correction", "Details")

        notes = self.store.list_notes(self.project_id)
        sources = self.store.list_sources(self.project_id)
        corrections = self.store.list_corrections(self.project_id)

        self.assertTrue(any(n["id"] == note_id for n in notes))
        self.assertTrue(any(s["id"] == source_id and s["status"] == "pending" for s in sources))
        self.assertTrue(any(c["id"] == correction_id and c["category"] == "B" for c in corrections))
        self.assertEqual([c["id"] for c in self.store.list_corrections(self.project_id, "B")], [correction_id])
        self.assertEqual(self.store.list_corrections(self.project_id, "A"), [])

        with self.assertRaises(WorkspaceError):
            self.store.create_correction(self.project_id, "Z", "Bad", "Category")

    def test_manual_review_workflow_pauses_and_resumes(self):
        workflow_id = self.store.save_workflow(
            self.project_id,
            {
                "name": "Pause flow",
                "version": "1.0",
                "modules": ["projects", "workflows", "tasks"],
                "steps": [
                    {
                        "id": "review-step",
                        "title": "Review",
                        "task_type": "manual_review",
                        "config": {"prompt": "Approve or revise."},
                        "depends_on": [],
                    }
                ],
            },
        )
        run = self.store.start_workflow(self.project_id, workflow_id)
        self.assertEqual(run["status"], "awaiting_review")
        self.assertEqual(len(run["tasks"]), 1)
        task = run["tasks"][0]
        self.assertEqual(task["status"], "awaiting_review")
        self.assertTrue(task["output"].get("awaiting_human_review"))

        completed = self.store.complete_human_review(task["id"], "Reviewed and accepted.")
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["tasks"][0]["status"], "completed")
        self.assertEqual(
            completed["tasks"][0]["output"].get("human_review"),
            "Reviewed and accepted.",
        )

        with self.assertRaises(WorkspaceError):
            self.store.complete_human_review(task["id"], "duplicate")

    def test_records_audit_events(self):
        events = self.store.list_events(limit=50)
        actions = {(e["entity_type"], e["action"]) for e in events}
        self.assertIn(("project", "created"), actions)


if __name__ == "__main__":
    unittest.main()
