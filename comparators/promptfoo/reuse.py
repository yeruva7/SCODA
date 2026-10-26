"""M2 for promptfoo: inherited versus authored artifacts at a tenant count.

Each promptfoo tenant needs its own file, so inheritance is whatever the
shared base contributes. Run with --tenants to pick the count.

    python3 reuse.py --tenants 10
"""

from __future__ import annotations

import argparse
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TENANTS_DIR = os.path.join(HERE, "tenants")
BASE = os.path.join(HERE, "cases", "shared_base.yaml")


def count_keys(path: str) -> int:
    """Count assertion and variable entries, the unit of authored work."""
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return len(re.findall(r"^\s*-\s", text, flags=re.MULTILINE))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenants", type=int, default=10)
    args = parser.parse_args()

    shared = count_keys(BASE)
    names = sorted(
        name for name in os.listdir(TENANTS_DIR) if name.endswith((".yaml", ".yml"))
    )[: args.tenants]
    authored = sum(count_keys(os.path.join(TENANTS_DIR, name)) for name in names)
    authored += len(names)  # the tenant file itself

    inherited = shared * len(names)
    total = inherited + authored
    print(f"tenants            {len(names)}")
    print(f"shared base units  {shared}")
    print(f"inherited          {inherited}")
    print(f"authored           {authored}")
    if total:
        print(f"M2 reuse           {100.0 * inherited / total:.1f}%")


if __name__ == "__main__":
    main()
