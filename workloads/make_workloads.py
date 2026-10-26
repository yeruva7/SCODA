"""Write the committed workload files, so every tool runs the same cases.

    python3 workloads/make_workloads.py
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_HERE, os.path.dirname(_HERE)]

from workload import build_workload, write_workload  # noqa: E402

SPECS = (
    # name, size, specific_every, filename
    ("functional_500", 500, 0, "functional_500.json"),
    ("semantic_2000", 2000, 0, "semantic_2000.json"),
    ("scaling_mixed", 500, 25, "scaling_mixed.json"),
)


def main() -> None:
    for name, size, specific_every, filename in SPECS:
        workload = build_workload(name, size, specific_every)
        path = os.path.join(_HERE, filename)
        write_workload(workload, path)
        shared = sum(1 for c in workload["cases"] if c.get("level") == "shared")
        print(f"{filename:<24} {size:>5} cases  shared {shared:>5}  "
              f"specific {size - shared:>4}")


if __name__ == "__main__":
    main()
