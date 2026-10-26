import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoda import NamespaceRegistry, TenantNamespace  # noqa: E402


class IsolationTests(unittest.TestCase):
    def test_namespaces_cannot_be_double_registered(self):
        registry = NamespaceRegistry()
        registry.register(TenantNamespace.create("tenant-a", {"x": 1}))
        with self.assertRaises(ValueError):
            registry.register(TenantNamespace.create("tenant-a", {"x": 2}))

    def test_resolved_config_is_frozen(self):
        namespace = TenantNamespace.create("tenant-a", {"flags": {"x": True}})
        with self.assertRaises(TypeError):
            namespace.resolved_config["flags"]["x"] = False  # type: ignore[index]

    def test_isolation_invariant_holds_across_tenants(self):
        registry = NamespaceRegistry()
        registry.register(TenantNamespace.create("tenant-a", {"x": 1}))
        registry.register(TenantNamespace.create("tenant-b", {"x": 1}))
        registry.assert_isolated()  # must not raise

    def test_result_queues_are_private_per_tenant(self):
        ns_a = TenantNamespace.create("tenant-a", {})
        ns_b = TenantNamespace.create("tenant-b", {})
        ns_a.enqueue_result({"test": "t1", "verdict": "PASS"})
        self.assertEqual(len(ns_a.drain_results()), 1)
        self.assertEqual(len(ns_b.drain_results()), 0)


if __name__ == "__main__":
    unittest.main()
