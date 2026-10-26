"""Tenant namespace isolation.

Invariant: for tenants i != j, the set of storage locations each tenant can
write to is disjoint, M(i) ∩ M(j) = ∅. Each namespace holds a frozen copy of
its own resolved configuration and its own result queue; the global (C1) and
environment (C3) layers are read-only at resolution time, so sharing them
does not violate isolation.
"""

from __future__ import annotations

import queue
import types
from dataclasses import dataclass, field
from typing import Any, Dict, List


def _freeze(value: Any) -> Any:
    """Recursively freeze a resolved config into an immutable structure so a
    namespace cannot mutate another's copy by reference."""
    if isinstance(value, dict):
        return types.MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass
class TenantNamespace:
    """One tenant's isolated execution context: a frozen configuration and
    a private result queue that no other namespace can enqueue to or read
    from directly."""

    tenant_id: str
    resolved_config: Any
    _results: "queue.Queue[Dict[str, Any]]" = field(
        default_factory=queue.Queue, repr=False
    )

    @classmethod
    def create(cls, tenant_id: str, resolved_config: Dict[str, Any]) -> "TenantNamespace":
        return cls(tenant_id=tenant_id, resolved_config=_freeze(resolved_config))

    def enqueue_result(self, result: Dict[str, Any]) -> None:
        self._results.put(result)

    def drain_results(self) -> List[Dict[str, Any]]:
        drained = []
        while not self._results.empty():
            drained.append(self._results.get_nowait())
        return drained


class NamespaceRegistry:
    """Owns the set of active tenant namespaces and enforces that no two
    namespaces share a mutable storage location."""

    def __init__(self) -> None:
        self._namespaces: Dict[str, TenantNamespace] = {}

    def register(self, namespace: TenantNamespace) -> None:
        if namespace.tenant_id in self._namespaces:
            raise ValueError(
                f"namespace already registered for tenant {namespace.tenant_id!r}"
            )
        self._namespaces[namespace.tenant_id] = namespace

    def get(self, tenant_id: str) -> TenantNamespace:
        return self._namespaces[tenant_id]

    def all(self) -> List[TenantNamespace]:
        return list(self._namespaces.values())

    def assert_isolated(self) -> None:
        """Verify the isolation invariant holds: every namespace's config
        object identity is distinct (no shared mutable reference)."""
        seen_ids = set()
        for ns in self._namespaces.values():
            config_id = id(ns.resolved_config)
            if config_id in seen_ids:
                raise AssertionError(
                    "isolation invariant violated: two namespaces share a "
                    "resolved-configuration object"
                )
            seen_ids.add(config_id)
