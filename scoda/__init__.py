"""SCODA: Scalable Configuration-Driven Automation.

A four-layer, multi-tenant test automation architecture: configuration
resolution, namespace isolation, parallel dispatch, and
structural/semantic response evaluation, with the metrics and drivers used
to measure it.
"""

from .config import ConfigLayer, ConfigResolver, deep_merge
from .isolation import TenantNamespace, NamespaceRegistry
from .dispatcher import Orchestrator, ParallelDispatcher, TestCase
from .evaluation import (
    StructuralValidator,
    SemanticEvaluator,
    EchoJudge,
    Verdict,
)
from .gate import GateDecision, GateResult, Priority, evaluate_gate
from .reporting import TenantReport, ReportCollector
from .datasets import QAPair, load_corpus, load_dataset
from .reference_corpus import reference_corpus
from .http_client import HttpClient, RateLimiter, Response, qps_max
from .judges import HttpJudge, RecordingJudge, ReplayJudge, build_judge

__version__ = "0.2.0"

__all__ = [
    "ConfigLayer",
    "ConfigResolver",
    "deep_merge",
    "TenantNamespace",
    "NamespaceRegistry",
    "Orchestrator",
    "ParallelDispatcher",
    "TestCase",
    "StructuralValidator",
    "SemanticEvaluator",
    "EchoJudge",
    "Verdict",
    "GateDecision",
    "GateResult",
    "Priority",
    "evaluate_gate",
    "TenantReport",
    "ReportCollector",
    "QAPair",
    "load_corpus",
    "load_dataset",
    "reference_corpus",
    "HttpClient",
    "RateLimiter",
    "Response",
    "qps_max",
    "HttpJudge",
    "RecordingJudge",
    "ReplayJudge",
    "build_judge",
]
