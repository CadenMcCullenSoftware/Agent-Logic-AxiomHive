import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from catalog_engine import (
    CatalogStore,
    CatalogValidationError,
    JsonLogicError,
    ReasoningEngine,
    evaluate_jsonlogic,
    validate_catalog,
)


ROOT = Path(__file__).resolve().parent


def load_inputs():
    meta_model = json.loads((ROOT / "catalog-meta-model.json").read_text())
    catalog = json.loads((ROOT / "catalog-model.json").read_text())
    return meta_model, catalog


class AgentDesignSchemaTests(unittest.TestCase):
    def test_pre_response_checks_must_all_be_true(self):
        schema = json.loads((ROOT / "agent-design.schema.json").read_text())
        checks_schema = schema["properties"]["pre_response_checks"]
        checks = {name: True for name in checks_schema["required"]}
        validator = Draft202012Validator(checks_schema)

        self.assertTrue(validator.is_valid(checks))
        checks["privacy_minimized"] = False
        self.assertFalse(validator.is_valid(checks))


class CatalogValidationTests(unittest.TestCase):
    def setUp(self):
        self.meta_model, self.catalog = load_inputs()

    def test_repository_catalog_is_valid(self):
        validate_catalog(self.catalog, self.meta_model)

    def test_rejects_dangling_edge_endpoints(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["edges"][0]["to"] = "missing-node"
        with self.assertRaisesRegex(CatalogValidationError, "unknown to node"):
            validate_catalog(catalog, self.meta_model)

    def test_rejects_unknown_provenance(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["nodes"][0]["epistemic_state"]["source_artifact_id"] = "missing.md"
        with self.assertRaisesRegex(CatalogValidationError, "unknown source artifact"):
            validate_catalog(catalog, self.meta_model)

    def test_rejects_unknown_node_source_artifact(self):
        catalog = copy.deepcopy(self.catalog)
        node = next(node for node in catalog["nodes"] if node["node_type"] != "Artifact")
        node["source_artifact_id"] = "missing.md"
        with self.assertRaisesRegex(CatalogValidationError, "unknown source artifact"):
            validate_catalog(catalog, self.meta_model)

    def test_conflict_edges_require_resolution_rule(self):
        catalog = copy.deepcopy(self.catalog)
        conflict = next(edge for edge in catalog["edges"] if edge["relation"] == "CONFLICTS_WITH")
        conflict.pop("resolution_rule")
        with self.assertRaisesRegex(CatalogValidationError, "does not match meta-model"):
            validate_catalog(catalog, self.meta_model)

    def test_rejects_unsupported_rule_operators(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["rules"][0]["logic_payload"] = {"execute": ["unsafe"]}
        with self.assertRaisesRegex(CatalogValidationError, "unsupported JsonLogic operator"):
            validate_catalog(catalog, self.meta_model)


class JsonLogicTests(unittest.TestCase):
    def test_handles_json_boolean_edge_cases(self):
        self.assertTrue(evaluate_jsonlogic({"if": [[], "truthy", "falsey"]}, {}))
        self.assertTrue(evaluate_jsonlogic({"if": [{"var": "obj"}, "truthy", "falsey"]}, {"obj": {}}))
        self.assertFalse(evaluate_jsonlogic({"==": [True, 1]}, {}))

    def test_malformed_numeric_comparison_is_reported(self):
        with self.assertRaisesRegex(JsonLogicError, "numeric operands"):
            evaluate_jsonlogic({">": [{"var": "age"}, 5]}, {"age": "unknown"})


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.meta_model, self.catalog = load_inputs()
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "catalog.db")
        self.store = CatalogStore(db_path)
        self.store.load_catalog(self.catalog, self.meta_model)
        self.engine = ReasoningEngine(self.store)

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_approval_rule_distinguishes_pass_and_fail(self):
        rule_id = "node-rule-approval-required-v2"
        approved = {
            "action": {
                "external_or_state_changing": True,
                "status": "approved",
                "approval": {
                    "required": True,
                    "explicit": True,
                    "prior_to_execution": True,
                },
            }
        }
        unapproved = copy.deepcopy(approved)
        unapproved["action"]["approval"]["required"] = False
        self.assertEqual(self.engine.evaluate_rule(rule_id, approved)["status"], "passed")
        self.assertEqual(self.engine.evaluate_rule(rule_id, unapproved)["status"], "failed")

    def test_status_filter_parses_serialized_epistemic_state(self):
        state = self.store.conn.execute(
            "SELECT epistemic_state FROM nodes WHERE id=?",
            ("node-artifact-design-md",),
        ).fetchone()["epistemic_state"]
        self.store.conn.execute(
            "UPDATE nodes SET epistemic_state=? WHERE id=?",
            (json.dumps(json.loads(state), separators=(",", ":")), "node-artifact-design-md"),
        )
        self.store.conn.commit()
        results = self.engine.search_nodes(
            filters={"status": "canonical"},
        )
        self.assertIn("node-artifact-design-md", {node["id"] for node in results})

    def test_status_filter_applies_limit_before_decoding_rows(self):
        original = self.store._node_from_row
        decoded = []

        def track_decode(row):
            decoded.append(row["id"])
            return original(row)

        self.store._node_from_row = track_decode
        results = self.engine.search_nodes(filters={"status": "canonical"}, limit=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(len(decoded), 1)

    def test_conflicts_and_supersessions_are_returned_separately(self):
        conflicts = self.store.detect_conflicts()
        supersessions = self.store.detect_supersessions()
        self.assertTrue(all(edge["relation"] != "SUPERSEDES" for edge in conflicts))
        self.assertTrue(all(edge["relation"] == "SUPERSEDES" for edge in supersessions))

    def test_invalid_load_keeps_existing_catalog(self):
        invalid = copy.deepcopy(self.catalog)
        invalid["edges"][0]["to"] = "missing-node"
        with self.assertRaises(CatalogValidationError):
            self.store.load_catalog(invalid, self.meta_model)
        self.assertIsNotNone(self.store.get_node("node-artifact-design-md"))


if __name__ == "__main__":
    unittest.main()
