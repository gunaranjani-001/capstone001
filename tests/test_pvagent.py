import json
import unittest

from pvagent import mcp_server
from pvagent.guardrails import Guardrails, contains_pii
from pvagent.mcp_client import MCPClient
from pvagent.observability import Tracer
from eval.run_eval import evaluate


class TestMCPServer(unittest.TestCase):
    def test_tools_over_stdio(self):
        with MCPClient() as c:
            self.assertEqual(set(c.list_tools()), {"meddra_lookup", "label_lookup", "case_db_search"})
            self.assertEqual(c.call_tool("meddra_lookup", {"term": "Stomach bleeding"})["matches"][0]["pt"], "Gastrointestinal haemorrhage")
            self.assertFalse(c.call_tool("label_lookup", {"drug": "Nonexistium"})["found"])

    def test_unknown_method(self):
        self.assertIn("error", mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "nope"}))


class TestGuardrails(unittest.TestCase):
    def setUp(self):
        self.g = Guardrails(Tracer("t"), {})

    def test_certain_requires_rechallenge(self):
        self.assertEqual(self.g.check_causality("Certain", True, False, ["E1"])[0], "Probable")
        self.assertEqual(self.g.check_causality("Certain", True, True, ["E1"])[0], "Certain")

    def test_incomplete_is_unassessable(self):
        self.assertEqual(self.g.check_causality("Probable", False, False, ["E1"])[0], "Unassessable")

    def test_conclusion_needs_evidence(self):
        self.assertEqual(self.g.check_causality("Possible", True, False, [])[0], "Unassessable")

    def test_pii_detector(self):
        self.assertTrue(contains_pii("mail a@b.com"))
        self.assertFalse(contains_pii("onset 2026-01-28"))


class TestEndToEnd(unittest.TestCase):
    def test_eval_suite_passes(self):
        r = evaluate()
        self.assertEqual(r["misses"], [])
        self.assertEqual(r["exact"], r["n"])
        failed = [k for k, v in r["gates"].items() if not v]
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
