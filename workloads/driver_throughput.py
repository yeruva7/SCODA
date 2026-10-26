"""M1 driver: peak throughput on a fixed functional workload.

Reports tests/min per run plus the mean and a 95% interval across runs, so
a single-rate figure is never presented as if it had dispersion.

    python3 workloads/driver_throughput.py --endpoint http://127.0.0.1:8080 \
        --size 500 --runs 10 --workers 16
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
from scoda.http_client import HttpClient, RateLimiter, qps_max  # noqa: E402
from scoda.metrics import ci95, mean, stdev, throughput  # noqa: E402
from workload import build_workload, load_workload  # noqa: E402


def one_run(
    cases: List[Dict[str, Any]], client: HttpClient, workers: int, tenant: str
) -> Dict[str, Any]:
    validator = StructuralValidator()
    dispatcher = ParallelDispatcher(max_workers=workers)

    def execute(case: Dict[str, Any]) -> Verdict:
        response = client.search(case["query"], tenant=tenant)
        if response.status != 200:
            return Verdict.FAIL
        return validator.validate(response.body, case["assertions"])

    started = time.monotonic()
    verdicts = dispatcher.run_parallel(cases, execute)
    elapsed = time.monotonic() - started
    passed = sum(1 for v in verdicts if v == Verdict.PASS)
    return {
        "tests": len(cases),
        "elapsed_s": elapsed,
        "tests_per_min": throughput(len(cases), elapsed),
        "structural_correctness": passed / len(cases) if cases else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--workload", help="JSON workload file; built from the reference corpus when absent")
    parser.add_argument("--size", type=int, default=500)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--tenant", default="tenant-0001")
    parser.add_argument("--qps-cap", type=float,
                        help="service capacity of your endpoint; required with --cap")
    parser.add_argument("--u-prod", type=float,
                        help="live-traffic utilization of your endpoint, in [0, 1]")
    parser.add_argument("--alpha", type=float, default=0.95)
    parser.add_argument("--cap", action="store_true",
                        help="apply the Section V-B service limit; peak is measured without it")
    parser.add_argument("--out", help="write the per-run records here as JSON")
    args = parser.parse_args()

    workload = (
        load_workload(args.workload)
        if args.workload
        else build_workload("functional", args.size)
    )
    cases = workload["cases"]

    limiter = None
    if args.cap:
        if args.qps_cap is None or args.u_prod is None:
            raise SystemExit("--cap requires --qps-cap and --u-prod for your endpoint")
        cap = qps_max(args.qps_cap, args.u_prod, args.alpha)
        limiter = RateLimiter(cap)
        print(f"service limit QPS_max = {cap:.2f} req/s")
    client = HttpClient(endpoint=args.endpoint, limiter=limiter)

    records = [one_run(cases, client, args.workers, args.tenant) for _ in range(args.runs)]
    rates = [r["tests_per_min"] for r in records]

    print(f"\nworkload {workload.get('name')} | {len(cases)} cases | W = {args.workers}")
    for index, record in enumerate(records, start=1):
        print(f"  run {index:>2}: {record['tests_per_min']:8.2f} tests/min "
              f"({record['elapsed_s']:.2f} s, structural "
              f"{record['structural_correctness']*100:.1f}%)")
    print(f"\nM1 mean {mean(rates):.2f} tests/min over {len(rates)} run(s)")
    if len(rates) >= 2:
        low, high = ci95(rates)
        print(f"   SD {stdev(rates):.2f}, 95% CI [{low:.2f}, {high:.2f}]")
    else:
        print("   single run: no dispersion estimate, so no interval is reported")
    implied = args.workers / (mean(rates) / 60.0)
    print(f"   implied mean per-test time + network delay: {implied:.3f} s")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"workload": workload.get("name"), "workers": args.workers,
                       "runs": records}, handle, indent=2)
            handle.write("\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
