"""Configuration aggregation: the four-level override hierarchy.

Layer priority, lowest to highest:
    C1 (global)   -> organization-wide defaults
    C2 (tenant)   -> per-tenant base configuration
    C3 (env)      -> per-environment overrides (staging, production, ...)
    C4 (runtime)  -> values injected at dispatch time (CI/CD job variables),
                     never authored as a file

Each layer is merged into the next with deep-merge, right-hand precedence:
later layers win on scalar conflicts; dict-valued keys merge recursively.
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` onto ``base``. Dicts merge key-wise;
    any other value type (including lists) is replaced wholesale."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


@dataclass
class ConfigLayer:
    """A single named configuration layer, loaded from a JSON file or an
    in-memory dict."""

    name: str
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, name: str, path: str) -> "ConfigLayer":
        if not os.path.exists(path):
            return cls(name=name, data={})
        with open(path, "r", encoding="utf-8") as fh:
            return cls(name=name, data=json.load(fh))

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ConfigLayer":
        return cls(name=name, data=dict(data))


class ConfigResolver:
    """Resolves the four configuration layers into one effective
    configuration for a given (tenant, environment) pair.

    C4 (runtime) is supplied as a plain dict at resolve time, since it is
    built from the caller's own dispatch-time context (e.g. CI/CD job
    variables) rather than loaded from disk.
    """

    def __init__(
        self,
        global_dir: str,
        tenants_dir: str,
        environments_dir: str,
    ) -> None:
        self.global_dir = global_dir
        self.tenants_dir = tenants_dir
        self.environments_dir = environments_dir

    def _load_global(self) -> ConfigLayer:
        path = os.path.join(self.global_dir, "defaults.json")
        return ConfigLayer.from_file("global", path)

    def _load_tenant(self, tenant_id: str) -> ConfigLayer:
        path = os.path.join(self.tenants_dir, f"{tenant_id}.json")
        return ConfigLayer.from_file(f"tenant:{tenant_id}", path)

    def _load_environment(self, env: str) -> ConfigLayer:
        path = os.path.join(self.environments_dir, f"{env}.json")
        return ConfigLayer.from_file(f"env:{env}", path)

    def resolve(
        self,
        tenant_id: str,
        env: str,
        runtime: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return the fully merged configuration: C1 (+) C2 (+) C3 (+) C4."""
        c1 = self._load_global().data
        c2 = self._load_tenant(tenant_id).data
        c3 = self._load_environment(env).data
        c4 = dict(runtime or {})

        merged = deep_merge(c1, c2)
        merged = deep_merge(merged, c3)
        merged = deep_merge(merged, c4)
        self._validate(merged, tenant_id)
        return merged

    @staticmethod
    def _validate(config: Dict[str, Any], tenant_id: str) -> None:
        """Minimal structural validation: resolved config must declare a
        validation block and must not silently drop the tenant identity."""
        if "validation" not in config:
            raise ValueError(
                f"resolved configuration for tenant {tenant_id!r} is "
                "missing a 'validation' block"
            )
        config.setdefault("tenant", tenant_id)
