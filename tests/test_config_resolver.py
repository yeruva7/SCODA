import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoda import ConfigResolver, deep_merge  # noqa: E402


class DeepMergeTests(unittest.TestCase):
    def test_scalar_override_wins(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        self.assertEqual(deep_merge(base, override), {"a": 1, "b": 3})

    def test_nested_dicts_merge_recursively(self):
        base = {"flags": {"x": True, "y": False}}
        override = {"flags": {"y": True, "z": True}}
        merged = deep_merge(base, override)
        self.assertEqual(merged, {"flags": {"x": True, "y": True, "z": True}})

    def test_non_dict_values_are_replaced_not_merged(self):
        base = {"tags": ["a", "b"]}
        override = {"tags": ["c"]}
        self.assertEqual(deep_merge(base, override), {"tags": ["c"]})

    def test_base_is_not_mutated(self):
        base = {"flags": {"x": True}}
        deep_merge(base, {"flags": {"x": False}})
        self.assertTrue(base["flags"]["x"])


class ConfigResolverTests(unittest.TestCase):
    def setUp(self):
        here = os.path.dirname(__file__)
        examples = os.path.join(here, "..", "examples")
        self.resolver = ConfigResolver(
            global_dir=os.path.join(examples, "global"),
            tenants_dir=os.path.join(examples, "tenants"),
            environments_dir=os.path.join(examples, "environments"),
        )

    def test_resolution_order_global_then_tenant_then_env_then_runtime(self):
        resolved = self.resolver.resolve(
            "catalog-search", "staging", runtime={"dispatch_id": "abc"}
        )
        # tenant layer enables semantic validation over the global default
        self.assertTrue(resolved["validation"]["semantic"]["enabled"])
        # global default supplies structural validation, untouched by tenant
        self.assertTrue(resolved["validation"]["structural"]["enabled"])
        # environment layer contributes its own key
        self.assertEqual(resolved["qps_cap"], 50)
        # runtime (C4) layer is merged last
        self.assertEqual(resolved["dispatch_id"], "abc")
        # tenant identity survives resolution
        self.assertEqual(resolved["tenant"], "catalog-search")

    def test_tenant_without_overrides_falls_back_to_global(self):
        resolved = self.resolver.resolve("docs-search", "staging")
        self.assertFalse(resolved["validation"]["semantic"]["enabled"])
        self.assertTrue(resolved["validation"]["structural"]["enabled"])

    def test_unknown_tenant_still_resolves_against_global_and_env(self):
        resolved = self.resolver.resolve("unregistered-tenant", "staging")
        self.assertEqual(resolved["tenant"], "unregistered-tenant")
        self.assertTrue(resolved["validation"]["structural"]["enabled"])


if __name__ == "__main__":
    unittest.main()
