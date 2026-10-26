"""Scaling driver: measures T(n) over a list of tenant counts, then reports
interval secants and the four candidate fits of Section V-C.

Shared cases execute once and their verdicts fan out to every tenant;
tenant-specific cases execute per tenant. That is the mechanism the
measured decline is attributed to.

    python3 workloads/driver_scaling.py --endpoint http://127.0.0.1:8080 \
        --counts 1,5,10,25,50,100,150 --workers 16
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_HERE, os.path.dirname(_HERE)]

from scoda.dispatcher import ParallelDispatcher  # noqa: E402
from scoda.evaluation import StructuralValidator, Verdict  # noqa: E402
from scoda.http_client import HttpClient  # noqa: E402
from scoda.metrics import (  # noqa: E402
    interval_secants,
    loo_relative_rmse,
    model_selection,
)
from workload import build_workload, load_workload, split_levels  # noqa: E402

TENANTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tenants", "params"
)


def load_tenants(count: int) -> List[Dict[str, Any]]:
    """First `count` tenant parameter files, in index order."""
    paths = sorted(
        os.path.join(TENANTS_DIR, name)
        for name in os.listdir(TENANTS_DIR)
        if name.startswith("tenant_")
    )
    if len(paths) < count:
        raise SystemExit(
            f"only {len(paths)} tenant files in {TENANTS_DIR}; "
            f"run tenants/generate_tenants.py --count {count}"
        )
    out = []
    for path in paths[:count]:
        with open(path, "r", encoding="utf-8") as handle:
            out.append(json.load(handle))
    return out


def measure(
    tenants: List[Dict[str, Any]],
    workload: Dict[str, Any],
    client: HttpClient,
    workers: int,
) -> Dict[str, Any]:
    """One full run at a given tenant count. Returns wall-clock minutes."""
    levels = split_levels(workload)
    validator = StructuralValidator()
    dispatcher = ParallelDispatcher(max_workers=workers)
    executed = 0
    started = time.monotonic()

    def run_case(item):
        case, tenant_id = item
        response = client.search(case["query"], tenant=tenant_id)
        if response.status != 200:
            return Verdict.FAIL
        return validator.validate(response.body, case["assertions"])

    # Shared cases: executed once against the first tenant, then fanned out.
    anchor = tenants[0]["tenant"]
    shared_items = [(case, anchor) for case in levels["shared"]]
    shared_verdicts = dispatcher.run_parallel(shared_items, run_case)
    executed += len(shared_items)

    # Occupied states determine how many shared groups actually ran.
    occupied = {t["state_id"] for t in tenants}

    # Tenant-specific cases: once per tenant that declares any.
    specific_items = []
    for tenant in tenants:
        for name in tenant.get("tenant_specific_tests", []):
            case = dict(levels["specific"][0]) if levels["specific"] else None
            if case is None:
                continue
            case["id"] = name
            specific_items.append((case, tenant["tenant"]))
    specific_verdicts = dispatcher.run_parallel(specific_items, run_case)
    executed += len(specific_items)

    elapsed_min = (time.monotonic() - started) / 60.0
    verdicts = list(shared_verdicts) + list(specific_verdicts)
    passed = sum(1 for v in verdicts if v == Verdict.PASS)
    return {
        "tenants": len(tenants),
        "minutes": elapsed_min,
        "executed": executed,
        "shared_executed": len(shared_items),
        "specific_executed": len(specific_items),
        "states_occupied": len(occupied),
        "structural_correctness": passed / len(verdicts) if verdicts else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--counts", default="1,5,10,25,50,100,150")
    parser.add_argument("--workload")
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--specific-every", type=int, default=25)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--capacity", type=float, default=28.89,
                        help="B, fixed from the deployed hierarchy; not fitted")
    parser.add_argument("--out")
    args = parser.parse_args()

    counts = [int(c) for c in args.counts.split(",") if c.strip()]
    workload = (
        load_workload(args.workload)
        if args.workload
        else build_workload("scaling", args.size, args.specific_every)
    )
    client = HttpClient(endpoint=args.endpoint)

    rows = [measure(load_tenants(n), workload, client, args.workers) for n in counts]
    times = [r["minutes"] for r in rows]

    print(f"\nworkload {workload.get('name')} | W = {args.workers} | B = {args.capacity}")
    print(f"{'n':>5} {'T(n) min':>10} {'executed':>9} {'shared':>7} "
          f"{'specific':>9} {'states':>7}")
    for row in rows:
        print(f"{row['tenants']:>5} {row['minutes']:>10.3f} {row['executed']:>9} "
              f"{row['shared_executed']:>7} {row['specific_executed']:>9} "
              f"{row['states_occupied']:>7}")

    secants = interval_secants(counts, times)
    print("\ninterval secants (min/tenant), Eq. (2d):")
    for i, secant in enumerate(secants, start=1):
        print(f"  {counts[i-1]:>4} -> {counts[i]:<4} {secant:9.4f}")
    if secants[0] > 0:
        print(f"  first/last ratio: {secants[0] / secants[-1]:.3f}x")
    if any(b > a for a, b in zip(secants, secants[1:])):
        print("  note: not strictly monotonic; an overall decline is the claim")

    if len(counts) >= 4:
        print("\nmodel selection (best AIC first):")
        for fit in model_selection(counts, times, args.capacity):
            aicc = "undefined" if fit.aicc is None else f"{fit.aicc:8.2f}"
            params = ", ".join(f"{k}={v:.4g}" for k, v in fit.params.items())
            print(f"  {fit.name:<11} k={fit.k} AIC={fit.aic:8.2f} AICc={aicc} "
                  f"R2={fit.r2:.4f} maxres={fit.max_rel_residual*100:.2f}%  {params}")
        print(f"\n  mechanism LOO relative RMSE: "
              f"{loo_relative_rmse(counts, times, args.capacity):.2f}%")
        print("  AICc is undefined when n - k - 1 <= 0; AIC is shown alongside")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"counts": counts, "rows": rows, "secants": secants},
                      handle, indent=2)
            handle.write("\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
