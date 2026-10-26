"""Parse promptfoo run output into tests/min, with dispersion when runs allow.

    python3 parse_runs.py runs/
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List


def read_run(path: str) -> Dict[str, float]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    results = payload.get("results", {})
    rows = results.get("results") or payload.get("results") or []
    if isinstance(rows, dict):
        rows = rows.get("results", [])
    count = len(rows)
    latencies = [float(r.get("latencyMs", 0)) for r in rows if isinstance(r, dict)]
    elapsed_s = sum(latencies) / 1000.0
    stats = results.get("stats") or {}
    if stats.get("duration"):
        elapsed_s = float(stats["duration"])
    if count == 0 or elapsed_s <= 0:
        raise ValueError(f"{path}: no timed cases found")
    return {"cases": count, "elapsed_s": elapsed_s, "tests_per_min": count * 60.0 / elapsed_s}


def main() -> None:
    directory = sys.argv[1] if len(sys.argv) > 1 else "runs"
    paths = [
        os.path.join(directory, name)
        for name in sorted(os.listdir(directory))
        if name.endswith(".json")
    ]
    if not paths:
        raise SystemExit(f"no run files in {directory}")
    rates: List[float] = []
    for path in paths:
        try:
            record = read_run(path)
        except ValueError as error:
            print(f"skipped {path}: {error}")
            continue
        rates.append(record["tests_per_min"])
        print(f"{os.path.basename(path):<28} {record['cases']:>5} cases "
              f"{record['tests_per_min']:>9.2f} tests/min")
    if not rates:
        raise SystemExit("no usable runs")
    mean = sum(rates) / len(rates)
    print(f"\nM1 mean {mean:.2f} tests/min over {len(rates)} run(s)")
    if len(rates) >= 2:
        sd = math.sqrt(sum((r - mean) ** 2 for r in rates) / (len(rates) - 1))
        half = 1.96 * sd / math.sqrt(len(rates))
        print(f"   SD {sd:.2f}, 95% CI [{mean - half:.2f}, {mean + half:.2f}]")
    else:
        print("   single run: no dispersion estimate, so no interval is reported")


if __name__ == "__main__":
    main()
