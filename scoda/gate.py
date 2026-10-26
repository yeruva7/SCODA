"""Release gate: turns a tenant's pass rate into a PASS / BLOCK / ALERT
decision, based on a threshold and a priority level."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable

from .evaluation import Verdict


class Priority(str, Enum):
    CRITICAL = "critical"
    STANDARD = "standard"


class GateDecision(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    ALERT = "ALERT"


@dataclass
class GateResult:
    decision: GateDecision
    pass_rate: float
    total: int
    passed: int
    skipped: int


def evaluate_gate(
    verdicts: Iterable[Verdict],
    theta: float,
    priority: Priority = Priority.STANDARD,
) -> GateResult:
    """Compute the pass rate over non-skipped verdicts and decide the gate.

    PASS   if pass_rate >= theta
    BLOCK  if pass_rate <  theta and priority is CRITICAL
    ALERT  if pass_rate <  theta otherwise

    An empty evaluated set cannot establish a pass, so it blocks regardless
    of priority rather than vacuously satisfying the threshold.
    """
    verdicts = list(verdicts)
    total = len(verdicts)
    skipped = sum(1 for v in verdicts if v == Verdict.SKIP)
    non_skipped = total - skipped
    passed = sum(1 for v in verdicts if v == Verdict.PASS)

    if non_skipped == 0:
        return GateResult(
            decision=GateDecision.BLOCK,
            pass_rate=0.0,
            total=total,
            passed=passed,
            skipped=skipped,
        )

    pass_rate = passed / non_skipped

    if pass_rate >= theta:
        decision = GateDecision.PASS
    elif priority == Priority.CRITICAL:
        decision = GateDecision.BLOCK
    else:
        decision = GateDecision.ALERT

    return GateResult(
        decision=decision,
        pass_rate=pass_rate,
        total=total,
        passed=passed,
        skipped=skipped,
    )
