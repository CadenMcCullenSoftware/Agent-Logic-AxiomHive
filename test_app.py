import json
import unittest

from app import _debug_mode_enabled, app


class FlaskUITests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Catalog Reasoning Engine", response.data)
        self.assertIn(b"29", response.data)  # node count

    def test_meta_model_loads(self):
        response = self.client.get("/meta-model")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Meta-model", response.data)
        self.assertIn(b"Concept", response.data)

    def test_nodes_list_loads(self):
        response = self.client.get("/nodes")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Node Search", response.data)

    def test_nodes_search_query(self):
        response = self.client.get("/nodes?query=approval")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"node-rule-approval-required-v2", response.data)

    def test_nodes_filter_by_type(self):
        response = self.client.get("/nodes?node_type=Rule")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Rule", response.data)

    def test_nodes_filter_by_status(self):
        response = self.client.get("/nodes?status=deprecated")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"deprecated", response.data)

    def test_node_detail_loads(self):
        response = self.client.get("/nodes/node-rule-approval-required-v2")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"node-rule-approval-required-v2", response.data)
        self.assertIn(b"Explicit Approval Required", response.data)

    def test_node_detail_unknown_404(self):
        response = self.client.get("/nodes/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_traverse_page_loads(self):
        response = self.client.get("/traverse")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Graph Traversal", response.data)

    def test_traverse_with_node(self):
        response = self.client.get(
            "/traverse?node=node-rule-approval-required-v2&depth=2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"REQUIRES", response.data)

    def test_evaluate_get_loads(self):
        response = self.client.get("/evaluate")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Evaluate Rule", response.data)
        self.assertIn(b"node-rule-approval-required-v2", response.data)

    def test_evaluate_post_pass_case(self):
        context = json.dumps({
            "action": {
                "external_or_state_changing": True,
                "status": "approved",
                "approval": {
                    "required": True,
                    "explicit": True,
                    "prior_to_execution": True,
                },
            }
        })
        response = self.client.post(
            "/evaluate",
            data={
                "rule_id": "node-rule-approval-required-v2",
                "context": context,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"passed", response.data)

    def test_evaluate_post_fail_case(self):
        context = json.dumps({
            "action": {
                "external_or_state_changing": True,
                "status": "approved",
                "approval": {
                    "required": False,
                    "explicit": True,
                    "prior_to_execution": True,
                },
            }
        })
        response = self.client.post(
            "/evaluate",
            data={
                "rule_id": "node-rule-approval-required-v2",
                "context": context,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"failed", response.data)

    def test_evaluate_post_invalid_json_preserves_context(self):
        context = "{invalid json"
        response = self.client.post(
            "/evaluate",
            data={"rule_id": "node-rule-approval-required-v2", "context": context},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid JSON context", response.data)
        self.assertIn(context.encode(), response.data)
        self.assertNotIn(b"<h2>Result</h2>", response.data)

    def test_debug_mode_is_limited_to_loopback_hosts(self):
        self.assertFalse(_debug_mode_enabled("0.0.0.0", True))
        self.assertFalse(_debug_mode_enabled("192.168.1.5", True))
        self.assertFalse(_debug_mode_enabled("localhost", True))
        self.assertTrue(_debug_mode_enabled("127.0.0.1", True))
        self.assertTrue(_debug_mode_enabled("::1", True))
        self.assertFalse(_debug_mode_enabled("127.0.0.1", False))

    def test_relationships_loads(self):
        response = self.client.get("/relationships")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Conflicts", response.data)
        self.assertIn(b"Supersessions", response.data)

    def test_validate_loads(self):
        response = self.client.get("/validate")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"valid", response.data.lower())

    def test_api_nodes(self):
        response = self.client.get("/api/nodes?query=approval")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertTrue(any(n["id"] == "node-rule-approval-required-v2" for n in data))

    def test_api_evaluate(self):
        response = self.client.post(
            "/api/evaluate",
            data=json.dumps({
                "rule_id": "node-rule-approval-required-v2",
                "context": {
                    "action": {
                        "external_or_state_changing": True,
                        "status": "approved",
                        "approval": {
                            "required": True,
                            "explicit": True,
                            "prior_to_execution": True,
                        },
                    }
                },
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "passed")


if __name__ == "__main__":
    unittest.main()
