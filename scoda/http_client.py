"""HTTP transport with the service-limit cap of Section V-B applied.

The cap is QPS_max = QPS_cap * (1 - u_prod) * alpha, so test traffic stays
inside the capacity left by live traffic. The limiter is shared across
worker threads; without that the cap would apply per worker and the
aggregate would exceed it by a factor of W.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def qps_max(qps_cap: float, u_prod: float, alpha: float) -> float:
    """Service limit from Section V-B. alpha must lie in (0, 1]."""
    if not 0.0 < alpha <= 1.0:
        raise ValueError(f"alpha must be in (0, 1], got {alpha}")
    if not 0.0 <= u_prod <= 1.0:
        raise ValueError(f"u_prod must be in [0, 1], got {u_prod}")
    return qps_cap * (1.0 - u_prod) * alpha


class RateLimiter:
    """Shared token-bucket limiter enforcing an aggregate requests/second."""

    def __init__(self, rate: float) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        self._interval = 1.0 / rate
        self._lock = threading.Lock()
        self._next = time.monotonic()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._next - now
            if wait <= 0:
                self._next = now + self._interval
                wait = 0.0
            else:
                self._next += self._interval
        if wait > 0:
            time.sleep(wait)


@dataclass
class Response:
    status: int
    body: Dict[str, Any]
    elapsed_s: float


@dataclass
class HttpClient:
    """Minimal JSON client. endpoint is the base URL of the system under test."""

    endpoint: str
    limiter: Optional[RateLimiter] = None
    timeout_s: float = 10.0
    headers: Dict[str, str] = field(default_factory=dict)

    def post(self, path: str, payload: Dict[str, Any]) -> Response:
        if self.limiter is not None:
            self.limiter.acquire()
        url = self.endpoint.rstrip("/") + "/" + path.lstrip("/")
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        request.add_header("Content-Type", "application/json")
        for key, value in self.headers.items():
            request.add_header(key, value)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as handle:
                raw = handle.read().decode("utf-8")
                status = handle.status
        except urllib.error.HTTPError as error:
            raw, status = error.read().decode("utf-8"), error.code
        elapsed = time.monotonic() - started
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw}
        return Response(status=status, body=body, elapsed_s=elapsed)

    def search(self, query: str, tenant: str, **extra: Any) -> Response:
        """Issue one search request against the configured endpoint."""
        payload: Dict[str, Any] = {"query": query, "tenant": tenant}
        payload.update(extra)
        return self.post("search", payload)
