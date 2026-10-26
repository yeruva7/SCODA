#!/usr/bin/env python3
"""Runnable example: onboard two tenants with different configuration
states, run a shared + tenant-specific test suite, and print each tenant's
gate decision.

Run from the repository root:
    python3 examples/run_example.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoda import ConfigResolver, Orchestrator, TestCase, Priority  # noqa: E402

HERE = os.path.dirname(__file__)


def build_resolver() -> ConfigResolver:
    return ConfigResolver(
        global_dir=os.path.join(HERE, "global"),
        tenants_dir=os.path.join(HERE, "tenants"),
        environments_dir=os.path.join(HERE, "environments"),
    )


def build_suite():
    return [
        # Shared: no tenant-specific override needed, executes once and the
        # result is reused across every tenant namespace.
        TestCase(
            name="health_check",
            level="shared",
            kind="structural",
            assertions=[{"path": "status", "equals": 200}],
        ),
        # Tenant-specific, gated behind a feature flag injected at C2/C4.
        TestCase(
            name="semantic_equivalence_check",
            level="specific",
            kind="semantic",
            feature_flag="semantic_validation_v1",
            query="What is the capital of France?",
            expected="Paris",
            dimensions=["equivalence"],
        ),
    ]


def main() -> None:
    resolver = build_resolver()
    orchestrator = Orchestrator(resolver)

    orchestrator.onboard_tenant(
        "catalog-search", env="staging", runtime={"dispatch_id": "run-001"}
    )
    orchestrator.onboard_tenant(
        "docs-search", env="staging", runtime={"dispatch_id": "run-001"}
    )

    orchestrator.registry.assert_isolated()

    suite = build_suite()
    reports = orchestrator.run(suite, theta=0.95, priority=Priority.STANDARD)

    for tenant_id in sorted(reports):
        print(reports[tenant_id].summary())


if __name__ == "__main__":
    main()
