"""Semantic evaluation driver: judge scores, and F1 when labels are given.

Precision, recall and F1 need human meaning-compatibility labels. Without
them the driver reports scores and pass rates only; it does not treat the
judge's own verdict as ground truth.

    python3 workloads/driver_semantic.py --endpoint http://127.0.0.1:8080 \
        --judge-endpoint http://127.0.0.1:8080 \
        --workload workloads/semantic_2000.json --labels labels.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_HERE, os.path.dirname(_HERE)]

from scoda.dispatcher import ParallelDispatcher  # noqa: E402
from scoda.evaluation import SemanticEvaluator, Verdict  # noqa: E402
from scoda.http_client import HttpClient  # noqa: E402
from scoda.judges import HttpJudge  # noqa: E402
from scoda.metrics import macro_f1, prf1  # noqa: E402
from workload import load_workload  # noqa: E402


def score_case(
    case: Dict[str, Any],
    client: HttpClient,
    evaluator: SemanticEvaluator,
    tenant: str,
    dimensions: List[str],
    tau: float,
    minima: Dict[str, float],
) -> Dict[str, Any]:
    response = client.search(case["query"], tenant=tenant)
    actual = str(response.body.get("answer", ""))
    verdict = evaluator.evaluate(
        case["query"], actual, case["expected"], dimensions, tau, minima
    )
    return {
        "id": case["id"],
        "dataset": case.get("dataset", "unknown"),
        "verdict": verdict.value if isinstance(verdict, Verdict) else str(verdict),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--judge-endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--judge-model", default="gemma-7b-it")
    parser.add_argument("--workload", required=True)
    parser.add_argument("--labels", help="JSON mapping case id -> true|false")
    parser.add_argument("--tau", type=float, default=0.75)
    parser.add_argument("--dimensions", default="equivalence,completeness",
                        help="comma-separated judge dimensions, averaged")
    parser.add_argument("--safety-minimum", type=float,
                        help="hard per-dimension minimum, never averaged away")
    parser.add_argument("--tenant", default="tenant-0001")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out")
    args = parser.parse_args()

    workload = load_workload(args.workload)
    cases = workload["cases"][: args.limit] if args.limit else workload["cases"]

    judge = HttpJudge(
        client=HttpClient(endpoint=args.judge_endpoint, timeout_s=30.0),
        model=args.judge_model,
    )
    evaluator = SemanticEvaluator(judge=judge)
    client = HttpClient(endpoint=args.endpoint)
    dispatcher = ParallelDispatcher(max_workers=args.workers)

    dimensions = [d.strip() for d in args.dimensions.split(",") if d.strip()]
    minima = {"safety": args.safety_minimum} if args.safety_minimum else {}

    records = dispatcher.run_parallel(
        cases,
        lambda case: score_case(
            case, client, evaluator, args.tenant, dimensions, args.tau, minima
        ),
    )
    passed = sum(1 for r in records if r["verdict"] == Verdict.PASS.value)
    print(f"judge {args.judge_model} | tau {args.tau} | {len(records)} cases")
    print(f"pass rate {100.0 * passed / len(records):.2f}%")

    if not args.labels:
        print("\nno labels supplied, so no precision, recall or F1 is reported.")
        print("The judge's verdict is not ground truth for itself.")
        return

    with open(args.labels, "r", encoding="utf-8") as handle:
        labels = json.load(handle)

    per_dataset: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    )
    scored = 0
    for record in records:
        if record["id"] not in labels:
            continue
        scored += 1
        truth = bool(labels[record["id"]])
        predicted = record["verdict"] == Verdict.PASS.value
        bucket = per_dataset[record["dataset"]]
        if predicted and truth:
            bucket["tp"] += 1
        elif predicted and not truth:
            bucket["fp"] += 1
        elif not predicted and truth:
            bucket["fn"] += 1
        else:
            bucket["tn"] += 1

    if scored == 0:
        raise SystemExit("no case id in the workload matched the labels file")

    print(f"\nlabelled cases scored: {scored}")
    print(f"{'dataset':<22} {'precision':>10} {'recall':>8} {'F1':>8}")
    per_dataset_f1: List[float] = []
    for dataset in sorted(per_dataset):
        counts = per_dataset[dataset]
        stats = prf1(counts["tp"], counts["fp"], counts["fn"])
        per_dataset_f1.append(stats["f1"])
        print(f"{dataset:<22} {stats['precision']*100:>9.1f}% "
              f"{stats['recall']*100:>7.1f}% {stats['f1']:>8.3f}")
    print(f"\nmacro F1 over {len(per_dataset_f1)} dataset(s): "
          f"{macro_f1(per_dataset_f1):.4f}")
    print("Aggregate is the unweighted mean of the per-dataset rows, so each "
          "dataset contributes equally.")

    total_fp = sum(c["fp"] for c in per_dataset.values())
    print(f"false-positive rate: {total_fp / scored * 100:.2f}% "
          f"({total_fp} of {scored} verdicts)")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"judge": args.judge_model, "tau": args.tau,
                       "records": records}, handle, indent=2)
            handle.write("\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
