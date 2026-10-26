"""Workload specification helpers shared by the drivers.

A workload file is JSON so it parses with the standard library:

    {"name": "functional_500", "cases": [{"id", "query", "expected",
      "assertions": [{"path", "op", "value"}], "level": "shared"|"specific"}]}
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from scoda.datasets import QAPair
from scoda.reference_corpus import reference_corpus

DEFAULT_ASSERTIONS = [
    {"path": "status", "op": "equals", "value": "ok"},
    {"path": "results", "op": "non_empty"},
    {"path": "page.size", "op": "equals", "value": 10},
]


def case_from_pair(pair: QAPair, index: int, level: str = "shared") -> Dict[str, Any]:
    return {
        "id": pair.pair_id or f"case-{index:05d}",
        "query": pair.query,
        "expected": pair.expected,
        "dataset": pair.dataset,
        "level": level,
        "assertions": list(DEFAULT_ASSERTIONS),
    }


def build_workload(name: str, size: int, specific_every: int = 0) -> Dict[str, Any]:
    """Build a workload of the given size from the reference corpus.

    specific_every marks every k-th case tenant-specific; 0 makes all cases
    shared, which is the functional-throughput configuration.
    """
    cases = []
    for index, pair in enumerate(reference_corpus(size)):
        level = "shared"
        if specific_every and index % specific_every == 0:
            level = "specific"
        cases.append(case_from_pair(pair, index, level))
    return {"name": name, "size": size, "cases": cases}


def load_workload(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        workload = json.load(handle)
    if "cases" not in workload:
        raise ValueError(f"{path}: workload has no 'cases' list")
    return workload


def write_workload(workload: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(workload, handle, indent=2)
        handle.write("\n")


def split_levels(workload: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    shared = [c for c in workload["cases"] if c.get("level", "shared") == "shared"]
    specific = [c for c in workload["cases"] if c.get("level") == "specific"]
    return {"shared": shared, "specific": specific}
