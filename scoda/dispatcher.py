"""Parallel test execution engine.

Tests bound to a shared level (no tenant-overridden key) execute once and
the result is distributed to every tenant namespace; tests bound to a
tenant-specific level execute once per tenant. This is the mechanism by
which incremental cost per additional tenant declines as shared
configuration states saturate, rather than growing linearly with the
number of tenants.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .config import ConfigResolver
from .evaluation import SemanticEvaluator, StructuralValidator, Verdict
from .gate import GateResult, Priority, evaluate_gate
from .isolation import NamespaceRegistry, TenantNamespace
from .reporting import ReportCollector, TenantReport

TestExecutor = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]
"""Executes one test case against a resolved config, returning a response
dict. Swap in a real HTTP/gRPC/streaming client for production use."""


@dataclass
class TestCase:
    name: str
    level: str  # "shared" or "specific"
    kind: str = "structural"  # "structural" or "semantic"
    query: str = ""
    expected: str = ""
    dimensions: Optional[List[str]] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    feature_flag: Optional[str] = None


def default_test_executor(test: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """A trivial in-process responder: echoes the test's expected value back
    as the actual response, so the sample suite is runnable with no network
    dependency. Replace with a real client for an actual system under test.
    """
    return {"status": 200, "body": {"id": test.get("name")}, "answer": test.get("expected", "")}


class Orchestrator:
    """Top-level entry point: resolves configuration, selects tests, runs
    them, evaluates responses, and produces a gate decision and report for
    each tenant."""

    def __init__(
        self,
        resolver: ConfigResolver,
        executor: TestExecutor = default_test_executor,
        structural: Optional[StructuralValidator] = None,
        semantic: Optional[SemanticEvaluator] = None,
        max_workers: int = 4,
    ) -> None:
        self.resolver = resolver
        self.executor = executor
        self.structural = structural or StructuralValidator()
        self.semantic = semantic or SemanticEvaluator()
        self.registry = NamespaceRegistry()
        self.reports = ReportCollector()
        self.dispatcher = ParallelDispatcher(max_workers=max_workers)

    def onboard_tenant(
        self, tenant_id: str, env: str, runtime: Optional[Dict[str, Any]] = None
    ) -> TenantNamespace:
        resolved = self.resolver.resolve(tenant_id, env, runtime)
        namespace = TenantNamespace.create(tenant_id, resolved)
        self.registry.register(namespace)
        return namespace

    def select_tests(self, suite: List[TestCase], config: Dict[str, Any]) -> List[TestCase]:
        """A test is shared if it declares level == 'shared'; otherwise it
        runs only when the tenant's resolved config enables its feature
        flag (specific to this tenant's state)."""
        active_flags = set(config.get("flags", {}).keys())
        selected = []
        for test in suite:
            if test.level == "shared":
                selected.append(test)
            elif test.feature_flag is None or test.feature_flag in active_flags:
                selected.append(test)
        return selected

    def _run_one(self, test: TestCase, config: Dict[str, Any]) -> Verdict:
        response = self.executor(
            {"name": test.name, "query": test.query, "expected": test.expected},
            config,
        )
        if test.kind == "structural":
            return self.structural.validate(response, test.assertions or [])
        tau = config.get("validation", {}).get("semantic", {}).get("threshold_tau", 0.75)
        return self.semantic.evaluate(
            query=test.query,
            actual=str(response.get("answer", "")),
            expected=test.expected,
            dimensions=test.dimensions or ["equivalence"],
            tau=tau,
        )

    def run(
        self,
        suite: List[TestCase],
        theta: float = 0.95,
        priority: Priority = Priority.STANDARD,
    ) -> Dict[str, TenantReport]:
        """Run the shared tests once, then every tenant's specific tests in
        parallel, and produce one gate decision per tenant."""
        namespaces = self.registry.all()
        if not namespaces:
            return {}

        shared_tests = [t for t in suite if t.level == "shared"]
        shared_verdicts = [self._run_one(t, dict(namespaces[0].resolved_config)) for t in shared_tests]

        def run_tenant(namespace: TenantNamespace) -> TenantReport:
            config = dict(namespace.resolved_config)
            specific = [
                t for t in self.select_tests(suite, config) if t.level != "shared"
            ]
            verdicts = list(shared_verdicts)
            verdicts.extend(self._run_one(t, config) for t in specific)
            gate_result = evaluate_gate(verdicts, theta=theta, priority=priority)
            return TenantReport(tenant_id=namespace.tenant_id, gate_result=gate_result)

        results = self.dispatcher.run_parallel(namespaces, run_tenant)
        for report in results:
            self.reports.record(report)
        return {r.tenant_id: r for r in results}


class ParallelDispatcher:
    """Thin wrapper over a thread pool: runs one callable per item and
    collects results in submission order."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers

    def run_parallel(self, items: List[Any], fn: Callable[[Any], Any]) -> List[Any]:
        if not items:
            return []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(fn, item): item for item in items}
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        return results
