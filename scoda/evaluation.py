"""Response analysis: structural assertions and semantic (LLM-judge-style)
evaluation for nondeterministic outputs.

A deterministic service can be checked with structural assertions (status
code, field presence, schema shape). A service whose correct output varies
in surface form needs a semantic judge: a pluggable scorer that rates how
well an actual response matches an expected answer along one or more
dimensions, against a threshold tau.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class StructuralValidator:
    """Checks a response against a JSON-schema-like assertion list, e.g.
    ``[{"path": "status", "equals": 200}, {"path": "body.id", "exists": True}]``.
    """

    def validate(self, response: Dict[str, Any], assertions: List[Dict[str, Any]]) -> Verdict:
        if not assertions:
            return Verdict.SKIP
        for assertion in assertions:
            value = self._extract(response, assertion.get("path", ""))
            if "equals" in assertion and value != assertion["equals"]:
                return Verdict.FAIL
            if assertion.get("exists") and value is None:
                return Verdict.FAIL
        return Verdict.PASS

    @staticmethod
    def _extract(response: Dict[str, Any], dotted_path: str) -> Any:
        node: Any = response
        for part in dotted_path.split("."):
            if not part:
                continue
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node


Judge = Callable[[str, str, str, str], float]
"""A judge scores (query, actual_response, expected_answer, dimension) -> [0,1]."""


def echo_judge(query: str, actual: str, expected: str, dimension: str) -> float:
    """A deterministic, dependency-free judge: scores lexical
    similarity between the actual and expected text. Intended for local
    testing and CI; swap in a real model-backed judge for production use."""
    if not expected:
        return 1.0
    return difflib.SequenceMatcher(None, actual.lower(), expected.lower()).ratio()


class EchoJudge:
    """Callable wrapper around :func:`echo_judge`, matching the ``Judge``
    protocol used by :class:`SemanticEvaluator`."""

    def __call__(self, query: str, actual: str, expected: str, dimension: str) -> float:
        return echo_judge(query, actual, expected, dimension)


@dataclass
class SemanticEvaluator:
    """Averages per-dimension judge scores and compares against a
    threshold, with optional hard per-dimension minima (e.g. for a safety
    dimension that must never be averaged away)."""

    judge: Judge = field(default_factory=EchoJudge)

    def evaluate(
        self,
        query: str,
        actual: str,
        expected: str,
        dimensions: List[str],
        tau: float,
        dimension_minima: Optional[Dict[str, float]] = None,
    ) -> Verdict:
        dimension_minima = dimension_minima or {}
        scores: Dict[str, float] = {}
        for dimension in dimensions:
            scores[dimension] = self.judge(query, actual, expected, dimension)

        for dimension, minimum in dimension_minima.items():
            if scores.get(dimension, 0.0) < minimum:
                return Verdict.FAIL

        if not scores:
            return Verdict.SKIP

        mean_score = sum(scores.values()) / len(scores)
        return Verdict.PASS if mean_score >= tau else Verdict.FAIL
