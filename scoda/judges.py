"""Pluggable LLM judges for semantic validation (Section V-D).

A judge is any callable (query, actual, expected, dimension) -> [0, 1], so
the primary judge is swapped by configuration rather than by code. Two
open-weight judges of distinct provenance are configured here for the
replication of Section VII-C1.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .http_client import HttpClient

PROMPT = (
    "Score how well the candidate answer matches the reference answer on the "
    "dimension '{dimension}'. Reply with only a number between 0 and 1.\n"
    "Question: {query}\nReference: {expected}\nCandidate: {actual}\nScore:"
)

# Open-weight replication judges (Section VII-C1). Distinct corpus,
# architecture and provenance from each other.
REPLICATION_JUDGES = ("mpt-30b-instruct", "gemma-7b-it")


def _first_float(text: str) -> Optional[float]:
    match = re.search(r"\d*\.?\d+", text)
    if match is None:
        return None
    try:
        return max(0.0, min(1.0, float(match.group())))
    except ValueError:
        return None


@dataclass
class HttpJudge:
    """Judge backed by an OpenAI-compatible /chat/completions endpoint.

    Any served open-weight model works; set model to the served name.
    """

    client: HttpClient
    model: str
    temperature: float = 0.0
    path: str = "chat/completions"
    on_unparsed: float = 0.0
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def __call__(self, query: str, actual: str, expected: str, dimension: str) -> float:
        prompt = PROMPT.format(
            dimension=dimension, query=query, expected=expected, actual=actual
        )
        response = self.client.post(
            self.path,
            {
                "model": self.model,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        text = ""
        choices = response.body.get("choices") or []
        if choices:
            text = str(choices[0].get("message", {}).get("content", ""))
        score = _first_float(text)
        self.calls.append(
            {"model": self.model, "dimension": dimension, "raw": text, "score": score}
        )
        return self.on_unparsed if score is None else score


@dataclass
class RecordingJudge:
    """Wraps a judge and records every score, for inter-rater comparison."""

    inner: Any
    scores: List[Dict[str, Any]] = field(default_factory=list)

    def __call__(self, query: str, actual: str, expected: str, dimension: str) -> float:
        score = self.inner(query, actual, expected, dimension)
        self.scores.append({"query": query, "dimension": dimension, "score": score})
        return score


@dataclass
class ReplayJudge:
    """Replays judgements from a saved run so a scored evaluation is rerunnable
    without model access."""

    table: Dict[str, float]
    default: float = 0.0

    @classmethod
    def from_file(cls, path: str) -> "ReplayJudge":
        with open(path, "r", encoding="utf-8") as handle:
            return cls(table=json.load(handle))

    @staticmethod
    def key(query: str, dimension: str) -> str:
        return f"{dimension}::{query}"

    def __call__(self, query: str, actual: str, expected: str, dimension: str) -> float:
        return self.table.get(self.key(query, dimension), self.default)


def build_judge(config: Dict[str, Any]) -> Any:
    """Construct a judge from a resolved configuration block.

    provider: "echo" (deterministic, no model), "http", or "replay".
    """
    provider = str(config.get("provider", "echo")).lower()
    if provider == "echo":
        from .evaluation import EchoJudge

        return EchoJudge()
    if provider == "replay":
        return ReplayJudge.from_file(config["path"])
    if provider == "http":
        client = HttpClient(endpoint=config["endpoint"], timeout_s=config.get("timeout_s", 30.0))
        return HttpJudge(client=client, model=config["model"])
    raise ValueError(f"unknown judge provider {provider!r}")
