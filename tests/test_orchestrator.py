import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoda import ConfigResolver, Orchestrator, Priority, TestCase  # noqa: E402


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        here = os.path.dirname(__file__)
        examples = os.path.join(here, "..", "examples")
        resolver = ConfigResolver(
            global_dir=os.path.join(examples, "global"),
            tenants_dir=os.path.join(examples, "tenants"),
            environments_dir=os.path.join(examples, "environments"),
        )
        self.orchestrator = Orchestrator(resolver)
        self.orchestrator.onboard_tenant("catalog-search", env="staging")
        self.orchestrator.onboard_tenant("docs-search", env="staging")

    def test_shared_test_executes_for_every_tenant(self):
        suite = [
            TestCase(
                name="health_check",
                level="shared",
                kind="structural",
                assertions=[{"path": "status", "equals": 200}],
            )
        ]
        reports = self.orchestrator.run(suite, theta=1.0)
        self.assertEqual(len(reports), 2)
        for report in reports.values():
            self.assertEqual(report.gate_result.pass_rate, 1.0)

    def test_feature_gated_test_only_runs_for_enabled_tenant(self):
        suite = [
            TestCase(
                name="semantic_check",
                level="specific",
                kind="semantic",
                feature_flag="semantic_validation_v1",
                query="q",
                expected="paris",
                dimensions=["equivalence"],
            )
        ]
        # The echo executor's response.answer echoes `expected` itself, so
        # semantic similarity is 1.0 wherever the test actually runs.
        reports = self.orchestrator.run(suite, theta=0.5)
        catalog = reports["catalog-search"]
        docs = reports["docs-search"]
        # catalog-search has the flag enabled: the test runs and passes.
        self.assertEqual(catalog.gate_result.total, 1)
        # docs-search does not have the flag: the test is not selected, so
        # its gate has nothing to evaluate and defaults to PASS.
        self.assertEqual(docs.gate_result.total, 0)

    def test_isolation_holds_after_onboarding(self):
        self.orchestrator.registry.assert_isolated()


if __name__ == "__main__":
    unittest.main()
