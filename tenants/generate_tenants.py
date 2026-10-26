"""Generate the per-tenant parameter files used by the scaling drivers.

Tenants draw a reusable configuration state from a fixed catalog, which is
the A3 assumption behind Eq. (2b): independent draws over B equiprobable
states. Drawing is seeded, so the whole tenant population is reproducible
from this script alone.

    python3 tenants/generate_tenants.py --count 150
"""

from __future__ import annotations

import argparse
import json
import os
import random
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS_DIR = os.path.join(HERE, "params")

# Deployed hierarchy of Section V-C: g1 = 1 global, g3 = 3 environments,
# mean g4 = 9.63 runtime fan-out. The product is the reported capacity B.
G1, G3, MEAN_G4 = 1, 3, 9.63
CAPACITY = G1 * G3 * MEAN_G4  # 28.89

# Integer state catalog for exact draws. The noninteger CAPACITY above is
# the effective capacity used only in the exponential approximation.
STATE_COUNT = 29

LOCALES = ("en_US", "en_GB", "de_DE", "fr_FR", "ja_JP", "es_ES", "pt_BR")
SURFACES = ("catalog", "docs", "support", "media", "news")

# Shared groups keyed by state; a tenant inherits every group its state
# carries and authors only what its own flags add.
SHARED_GROUPS = (
    "structural_core",
    "pagination",
    "ranking_sanity",
    "locale_fallback",
    "empty_query",
)


def state_profile(state: int) -> Dict[str, object]:
    """Deterministic shared-group membership and threshold for one state."""
    rng = random.Random(90000 + state)
    groups = [g for g in SHARED_GROUPS if rng.random() < 0.72] or [SHARED_GROUPS[0]]
    return {
        "state_id": state,
        "shared_groups": groups,
        "threshold_pass_rate": round(rng.choice([0.95, 0.97, 1.0]), 2),
    }


def build_tenant(index: int, rng: random.Random) -> Dict[str, object]:
    """One tenant parameter file. index is one-based."""
    state = rng.randrange(STATE_COUNT)
    profile = state_profile(state)
    semantic = rng.random() < 0.60
    specific_count = rng.choice([0, 0, 1, 1, 2])
    return {
        "tenant": f"tenant-{index:04d}",
        "config_level": "tenant-base",
        "surface": SURFACES[index % len(SURFACES)],
        "locale": LOCALES[index % len(LOCALES)],
        "state_id": profile["state_id"],
        "inherits_shared_groups": profile["shared_groups"],
        "flags": {
            "semantic_validation_v1": semantic,
            "strict_pagination": bool(rng.random() < 0.3),
        },
        "validation": {
            "structural": {"enabled": True},
            "semantic": {
                "enabled": semantic,
                "threshold_tau": 0.75 if semantic else None,
                "judge_criteria": "equivalence" if semantic else None,
                "dimension_minima": {"safety": 0.9} if semantic else {},
            },
        },
        "gate": {
            "threshold_pass_rate": profile["threshold_pass_rate"],
            "priority": "critical" if index % 4 == 0 else "standard",
        },
        "tenant_specific_tests": [
            f"specific_{index:04d}_{slot}" for slot in range(specific_count)
        ],
    }


def generate(count: int, seed: int, out_dir: str) -> List[str]:
    rng = random.Random(seed)
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for index in range(1, count + 1):
        tenant = build_tenant(index, rng)
        path = os.path.join(out_dir, f"tenant_{index:04d}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(tenant, handle, indent=2)
            handle.write("\n")
        written.append(path)
    manifest = {
        "count": count,
        "seed": seed,
        "state_count": STATE_COUNT,
        "effective_capacity": round(CAPACITY, 2),
        "hierarchy": {"g1": G1, "g3": G3, "mean_g4": MEAN_G4},
        "shared_groups": list(SHARED_GROUPS),
        "files": [os.path.basename(p) for p in written],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=150)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--out", default=PARAMS_DIR)
    args = parser.parse_args()
    written = generate(args.count, args.seed, args.out)
    occupied = len({json.load(open(p))["state_id"] for p in written})
    print(f"wrote {len(written)} tenant parameter files to {args.out}")
    print(f"distinct states occupied: {occupied} of {STATE_COUNT}")


if __name__ == "__main__":
    main()
