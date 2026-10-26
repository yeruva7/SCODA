"""DeepEval comparator driver.

Semantic oracle: model-graded assertions, which is why this tool and RAGAS
are the slowest on M1 in Table 2. The judge is configured here rather than
in code, so the same workload can be scored by any served open-weight
model. Requires `pip install deepeval`.

    python3 run_deepeval.py --workload ../../workloads/functional_500.json \
        --endpoint http://127.0.0.1:8080 --runs 5
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import urllib.request
from typing import Any, Dict, List

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_answer(endpoint: str, query: str, tenant: str) -> str:
    payload = json.dumps({"query": query, "tenant": tenant}).encode("utf-8")
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/search", data=payload, method="POST"
    )
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as handle:
        return str(json.loads(handle.read().decode("utf-8")).get("answer", ""))


def one_run(cases: List[Dict[str, Any]], endpoint: str, config: Dict[str, Any]) -> Dict:
    """Score every case with DeepEval's answer-relevancy metric."""
    from deepeval.metrics import AnswerRelevancyMetric
    from deepeval.test_case import LLMTestCase

    metric = AnswerRelevancyMetric(
        threshold=config["judge"]["threshold_tau"],
        model=config["judge"]["model"],
        include_reason=False,
    )
    passed = 0
    started = time.monotonic()
    for case in cases:
        actual = fetch_answer(endpoint, case["query"], config["tenant"])
        test_case = LLMTestCase(
            input=case["query"], actual_output=actual, expected_output=case["expected"]
        )
        metric.measure(test_case)
        passed += 1 if metric.score >= config["judge"]["threshold_tau"] else 0
    elapsed = time.monotonic() - started
    return {
        "cases": len(cases),
        "elapsed_s": elapsed,
        "tests_per_min": len(cases) * 60.0 / elapsed,
        "pass_rate": passed / len(cases) if cases else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--out", default="runs.json")
    args = parser.parse_args()

    config = load_config()
    with open(args.workload, "r", encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]

    records = [one_run(cases, args.endpoint, config) for _ in range(args.runs)]
    rates = [r["tests_per_min"] for r in records]
    mean = sum(rates) / len(rates)
    for index, record in enumerate(records, start=1):
        print(f"run {index:>2}: {record['tests_per_min']:8.2f} tests/min "
              f"(pass rate {record['pass_rate']*100:.1f}%)")
    print(f"\nM1 mean {mean:.2f} tests/min over {len(rates)} run(s)")
    if len(rates) >= 2:
        sd = math.sqrt(sum((r - mean) ** 2 for r in rates) / (len(rates) - 1))
        half = 1.96 * sd / math.sqrt(len(rates))
        print(f"   SD {sd:.2f}, 95% CI [{mean - half:.2f}, {mean + half:.2f}]")

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump({"tool": "deepeval", "runs": records}, handle, indent=2)
        handle.write("\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
