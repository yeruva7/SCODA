"""Per-tenant reporting: each tenant sees only its own outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .gate import GateResult


@dataclass
class TenantReport:
    tenant_id: str
    gate_result: GateResult
    failures: List[Dict[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        gr = self.gate_result
        return (
            f"[{self.tenant_id}] {gr.decision.value} "
            f"(pass_rate={gr.pass_rate:.1%}, "
            f"{gr.passed}/{gr.total - gr.skipped} passed, "
            f"{gr.skipped} skipped)"
        )


class ReportCollector:
    """Collects one report per tenant and keeps them strictly separated:
    no cross-tenant aggregation that would let one tenant's failures leak
    into another's view."""

    def __init__(self) -> None:
        self._reports: Dict[str, TenantReport] = {}

    def record(self, report: TenantReport) -> None:
        self._reports[report.tenant_id] = report

    def for_tenant(self, tenant_id: str) -> TenantReport:
        return self._reports[tenant_id]

    def all_summaries(self) -> List[str]:
        return [r.summary() for r in self._reports.values()]
