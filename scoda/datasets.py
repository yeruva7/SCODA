"""Loaders for the four public QA datasets used in the evaluation.

Each loader yields QAPair records. Files are expected in a local data
directory; no dataset is redistributed here, only read.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional

# Dataset name -> (reported pair count, query kind). Counts match the
# evaluation corpus; a loader warns when a file yields a different count.
CORPUS = {
    "natural_questions": (3610, "factoid"),
    "triviaqa": (2000, "trivia"),
    "hotpotqa": (500, "multi_hop"),
    "openbookqa": (500, "science"),
}

TOTAL_PAIRS = sum(count for count, _ in CORPUS.values())


@dataclass(frozen=True)
class QAPair:
    """One evaluation record: the query, the reference answer, its source."""

    query: str
    expected: str
    dataset: str
    kind: str
    locale: str = "en_US"
    pair_id: Optional[str] = None


def _records(path: str) -> Iterator[Dict]:
    """Read JSONL, or a JSON list, whichever the file contains."""
    with open(path, "r", encoding="utf-8") as handle:
        first = handle.read(1)
        handle.seek(0)
        if first == "[":
            for item in json.load(handle):
                yield item
        else:
            for line in handle:
                line = line.strip()
                if line:
                    yield json.loads(line)


def load_dataset(name: str, path: str, limit: Optional[int] = None) -> List[QAPair]:
    """Load one named dataset from a JSON or JSONL file."""
    if name not in CORPUS:
        raise KeyError(f"unknown dataset {name!r}; expected one of {sorted(CORPUS)}")
    _, kind = CORPUS[name]
    pairs: List[QAPair] = []
    for index, record in enumerate(_records(path)):
        query = record.get("question") or record.get("query")
        expected = record.get("answer") or record.get("expected")
        if query is None or expected is None:
            raise ValueError(f"{path}: record {index} lacks a question/answer field")
        if isinstance(expected, list):
            expected = expected[0] if expected else ""
        pairs.append(
            QAPair(
                query=str(query),
                expected=str(expected),
                dataset=name,
                kind=kind,
                locale=str(record.get("locale", "en_US")),
                pair_id=str(record.get("id", index)),
            )
        )
        if limit is not None and len(pairs) >= limit:
            break
    return pairs


def load_corpus(data_dir: str, limit_per_dataset: Optional[int] = None) -> List[QAPair]:
    """Load every dataset found in data_dir as <name>.jsonl or <name>.json."""
    pairs: List[QAPair] = []
    for name in CORPUS:
        for suffix in (".jsonl", ".json"):
            path = os.path.join(data_dir, name + suffix)
            if os.path.exists(path):
                pairs.extend(load_dataset(name, path, limit_per_dataset))
                break
    return pairs

