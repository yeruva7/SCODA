"""M2/M4 driver: file reuse and onboarding effort per tenant.

Reuse is computed from the tenant parameter files, by counting inherited
shared groups against total applicable artifacts. Effort is read from an
effort log, because person-hours are recorded by people, not measured by a
harness; the driver refuses to invent them.

    python3 workloads/driver_onboarding.py --counts 1,10,25,50,100,150 \
        --effort-log effort.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_HERE, os.path.dirname(_HERE)]

from scoda.metrics import onboarding_effort, reuse_percent  # noqa: E402

TENANTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tenants", "params"
)


def load_tenants(count: int) -> List[Dict[str, Any]]:
    paths = sorted(
        os.path.join(TENANTS_DIR, name)
        for name in os.listdir(TENANTS_DIR)
        if name.startswith("tenant_")
    )[:count]
    out = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            out.append(json.load(handle))
    return out


def reuse_at(count: int) -> Dict[str, Any]:
    """M2 at a tenant count: inherited artifacts over total applicable."""
    tenants = load_tenants(count)
    inherited = sum(len(t.get("inherits_shared_groups", [])) for t in tenants)
    authored = sum(len(t.get("tenant_specific_tests", [])) for t in tenants)
    # A tenant's own parameter file is itself an authored artifact.
    authored += len(tenants)
    total = inherited + authored
    return {
        "tenants": count,
        "inherited": inherited,
        "authored": authored,
        "reuse_percent": reuse_percent(inherited, total),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", default="1,10,25,50,100,150")
    parser.add_argument("--effort-log", help="JSON mapping tenant count -> cumulative hours")
    args = parser.parse_args()

    counts = [int(c) for c in args.counts.split(",") if c.strip()]

    print(f"{'n':>5} {'inherited':>10} {'authored':>9} {'M2 reuse %':>11}")
    curve = [reuse_at(n) for n in counts]
    for row in curve:
        print(f"{row['tenants']:>5} {row['inherited']:>10} {row['authored']:>9} "
              f"{row['reuse_percent']:>11.1f}")

    if not args.effort_log:
        print("\nM4 not reported: pass --effort-log with recorded person-hours.")
        print("Effort is a human record; this driver will not synthesize it.")
        return

    with open(args.effort_log, "r", encoding="utf-8") as handle:
        effort = {int(k): float(v) for k, v in json.load(handle).items()}

    print(f"\n{'n':>5} {'cumulative h':>13} {'h/tenant':>9} {'secant h/tenant':>16}")
    previous_n = previous_h = None
    for n in counts:
        if n not in effort:
            continue
        hours = effort[n]
        secant = ""
        if previous_n is not None:
            secant = f"{(hours - previous_h) / (n - previous_n):16.3f}"
        print(f"{n:>5} {hours:>13.2f} {onboarding_effort(hours, n):>9.3f}{secant}")
        previous_n, previous_h = n, hours


if __name__ == "__main__":
    main()
