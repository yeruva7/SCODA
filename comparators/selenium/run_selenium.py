"""Selenium WebDriver comparator driver.

Structural oracle only, one browser profile per tenant, which is the
configuration locus the taxonomy records for this generation. Requires
`pip install selenium` and a local driver binary; the measurement protocol
is identical to the SCODA side (same workload file, 16-way parallelism,
five runs, one discarded warm-up).

    python3 run_selenium.py --endpoint http://127.0.0.1:8080 \
        --workload ../../workloads/functional_500.json --runs 5
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def make_driver(config: Dict[str, Any]):
    """One headless browser per worker. Imported lazily so the file reads
    without selenium installed."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    for flag in config["browser"]["flags"]:
        options.add_argument(flag)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(config["browser"]["page_load_timeout_s"])
    return driver


def run_case(driver, endpoint: str, case: Dict[str, Any], tenant: str) -> bool:
    from selenium.webdriver.common.by import By

    url = f"{endpoint.rstrip('/')}/?tenant={tenant}&q={case['query']}"
    driver.get(url)
    nodes = driver.find_elements(By.CSS_SELECTOR, "[data-result]")
    return len(nodes) > 0


def one_run(cases: List[Dict[str, Any]], endpoint: str, config: Dict[str, Any]) -> Dict:
    workers = config["parallelism"]["workers"]
    drivers = [make_driver(config) for _ in range(workers)]
    passed = 0
    started = time.monotonic()
    try:
        def execute(indexed):
            index, case = indexed
            driver = drivers[index % workers]
            return run_case(driver, endpoint, case, config["tenant"])

        with ThreadPoolExecutor(max_workers=workers) as pool:
            for ok in pool.map(execute, enumerate(cases)):
                passed += 1 if ok else 0
    finally:
        for driver in drivers:
            driver.quit()
    elapsed = time.monotonic() - started
    return {
        "cases": len(cases),
        "elapsed_s": elapsed,
        "tests_per_min": len(cases) * 60.0 / elapsed,
        "structural_correctness": passed / len(cases) if cases else 0.0,
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

    one_run(cases[: min(20, len(cases))], args.endpoint, config)  # discarded warm-up
    records = [one_run(cases, args.endpoint, config) for _ in range(args.runs)]
    rates = [r["tests_per_min"] for r in records]
    mean = sum(rates) / len(rates)

    for index, record in enumerate(records, start=1):
        print(f"run {index:>2}: {record['tests_per_min']:8.2f} tests/min")
    print(f"\nM1 mean {mean:.2f} tests/min over {len(rates)} run(s)")
    if len(rates) >= 2:
        sd = math.sqrt(sum((r - mean) ** 2 for r in rates) / (len(rates) - 1))
        half = 1.96 * sd / math.sqrt(len(rates))
        print(f"   SD {sd:.2f}, 95% CI [{mean - half:.2f}, {mean + half:.2f}]")

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump({"tool": "selenium", "runs": records}, handle, indent=2)
        handle.write("\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
