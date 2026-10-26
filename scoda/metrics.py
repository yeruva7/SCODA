"""Metrics M1-M5 and the operational metrics of Section VI.

Everything here is computed from measurements the drivers collect. No
reported figure from the paper is hard-coded: a value only appears if the
caller measured it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean of an empty sequence")
    return sum(values) / len(values)


def stdev(values: Sequence[float]) -> float:
    """Sample standard deviation; 0.0 for a single observation."""
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))


def ci95(values: Sequence[float]) -> Tuple[float, float]:
    """Normal-approximation 95% interval on the mean. Needs n >= 2."""
    if len(values) < 2:
        raise ValueError("a confidence interval needs at least two runs")
    half = 1.96 * stdev(values) / math.sqrt(len(values))
    mu = mean(values)
    return (mu - half, mu + half)


# ---------------------------------------------------------------- framework

def throughput(tests_executed: int, elapsed_s: float) -> float:
    """M1, tests per minute over a fixed workload."""
    if elapsed_s <= 0:
        raise ValueError("elapsed time must be positive")
    return tests_executed * 60.0 / elapsed_s


def reuse_percent(shared_artifacts: int, total_artifacts: int) -> float:
    """M2, the fraction of artifacts inherited rather than authored."""
    if total_artifacts <= 0:
        raise ValueError("total_artifacts must be positive")
    return 100.0 * shared_artifacts / total_artifacts


def onboarding_effort(cumulative_hours: float, tenants: int) -> float:
    """M4, person-hours per tenant."""
    if tenants <= 0:
        raise ValueError("tenants must be positive")
    return cumulative_hours / tenants


# -------------------------------------------------------------- operational

def expansion_ratio(scoda_rate: float, baseline_rate: float) -> float:
    """Psi, the throughput ratio against a baseline."""
    if baseline_rate <= 0:
        raise ValueError("baseline_rate must be positive")
    return scoda_rate / baseline_rate


def time_reduction(scoda_time: float, reference_time: float) -> float:
    """Phi = 1 - T_scoda / T_reference."""
    if reference_time <= 0:
        raise ValueError("reference_time must be positive")
    return 1.0 - scoda_time / reference_time


def false_positive_rate(incorrect_failures: int, total_verdicts: int) -> float:
    """FPR, the fraction of verdicts that failed a correct response."""
    if total_verdicts <= 0:
        raise ValueError("total_verdicts must be positive")
    return incorrect_failures / total_verdicts


def prf1(true_pos: int, false_pos: int, false_neg: int) -> Dict[str, float]:
    """Precision, recall and F1 for the semantic oracle."""
    precision = true_pos / (true_pos + false_pos) if true_pos + false_pos else 0.0
    recall = true_pos / (true_pos + false_neg) if true_pos + false_neg else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def macro_f1(per_dataset_f1: Sequence[float]) -> float:
    """Unweighted mean of per-dataset F1, so each dataset counts equally."""
    return mean(per_dataset_f1)


# ----------------------------------------------------------------- scaling

def interval_secants(counts: Sequence[int], times: Sequence[float]) -> List[float]:
    """Delta T_i = (T(n_i) - T(n_{i-1})) / (n_i - n_{i-1}), Eq. (2d).

    An interval secant averages the one-tenant increments across the
    interval; it is not the increment at its endpoint.
    """
    if len(counts) != len(times):
        raise ValueError("counts and times must have equal length")
    if len(counts) < 2:
        raise ValueError("at least two tenant counts are needed")
    out = []
    for i in range(1, len(counts)):
        span = counts[i] - counts[i - 1]
        if span <= 0:
            raise ValueError("tenant counts must be strictly increasing")
        out.append((times[i] - times[i - 1]) / span)
    return out


def expected_occupancy(capacity: float, tenants: int, exact: bool = True) -> float:
    """E[d(n)] from Eq. (2b). The exact form needs an integer capacity; the
    exponential approximation accepts a noninteger effective capacity."""
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    if exact:
        if abs(capacity - round(capacity)) > 1e-9:
            raise ValueError(
                "the exact occupancy form requires an integer capacity; "
                "pass exact=False to use the exponential approximation"
            )
        return capacity * (1.0 - (1.0 - 1.0 / capacity) ** tenants)
    return capacity * (1.0 - math.exp(-tenants / capacity))


@dataclass
class Fit:
    """One fitted model: parameters, fit quality, and its AIC terms."""

    name: str
    params: Dict[str, float]
    rss: float
    r2: float
    max_rel_residual: float
    k: int
    n: int

    @property
    def aic(self) -> float:
        return self.n * math.log(self.rss / self.n) + 2 * self.k

    @property
    def aicc(self) -> Optional[float]:
        """Undefined when n - k - 1 <= 0, which is why it is optional."""
        denom = self.n - self.k - 1
        if denom <= 0:
            return None
        return self.aic + (2 * self.k * (self.k + 1)) / denom

    def predict_at(self, n: int) -> float:
        raise NotImplementedError


def _ols(design: List[List[float]], targets: Sequence[float]) -> List[float]:
    """Solve normal equations by Gauss-Jordan. Pure Python, no numpy."""
    width = len(design[0])
    normal = [[0.0] * (width + 1) for _ in range(width)]
    for row, target in zip(design, targets):
        for i in range(width):
            for j in range(width):
                normal[i][j] += row[i] * row[j]
            normal[i][width] += row[i] * target
    for col in range(width):
        pivot = max(range(col, width), key=lambda r: abs(normal[r][col]))
        if abs(normal[pivot][col]) < 1e-12:
            raise ValueError("design matrix is singular")
        normal[col], normal[pivot] = normal[pivot], normal[col]
        scale = normal[col][col]
        normal[col] = [v / scale for v in normal[col]]
        for row_index in range(width):
            if row_index == col:
                continue
            factor = normal[row_index][col]
            if factor:
                normal[row_index] = [
                    a - factor * b for a, b in zip(normal[row_index], normal[col])
                ]
    return [normal[i][width] for i in range(width)]


def _quality(name: str, params: Dict[str, float], counts, times, predict, k: int) -> Fit:
    predicted = [predict(n) for n in counts]
    residuals = [t - p for t, p in zip(times, predicted)]
    rss = sum(r * r for r in residuals)
    mu = mean(times)
    tss = sum((t - mu) ** 2 for t in times)
    max_rel = max(abs(r) / t for r, t in zip(residuals, times))
    return Fit(
        name=name,
        params=params,
        rss=rss,
        r2=1.0 - rss / tss if tss else 1.0,
        max_rel_residual=max_rel,
        k=k,
        n=len(counts),
    )


def fit_mechanism(counts: Sequence[int], times: Sequence[float], capacity: float) -> Fit:
    """Fit T(n) = a + bn + c(1 - exp(-n/B)) with B held fixed, Eq. (2e).

    Linear in a, b and c once B is fixed, so this is exact least squares.
    k = 4 counts a, b, c and the residual variance; B is not estimated.
    """
    design = [[1.0, float(n), 1.0 - math.exp(-n / capacity)] for n in counts]
    a, b, c = _ols(design, times)
    predict = lambda n: a + b * n + c * (1.0 - math.exp(-n / capacity))
    return _quality(
        "mechanism", {"a": a, "b": b, "c": c, "B": capacity}, counts, times, predict, k=4
    )


def fit_linear(counts: Sequence[int], times: Sequence[float]) -> Fit:
    design = [[1.0, float(n)] for n in counts]
    a, b = _ols(design, times)
    return _quality("linear", {"a": a, "b": b}, counts, times, lambda n: a + b * n, k=3)


def fit_log_linear(counts: Sequence[int], times: Sequence[float]) -> Fit:
    design = [[1.0, math.log(n)] for n in counts]
    a, b = _ols(design, times)
    return _quality(
        "log-linear", {"a": a, "b": b}, counts, times, lambda n: a + b * math.log(n), k=3
    )


def fit_power_law(counts: Sequence[int], times: Sequence[float]) -> Fit:
    """Fit T = a n^alpha by least squares in log space."""
    design = [[1.0, math.log(n)] for n in counts]
    log_a, alpha = _ols(design, [math.log(t) for t in times])
    a = math.exp(log_a)
    return _quality(
        "power-law", {"a": a, "alpha": alpha}, counts, times, lambda n: a * n**alpha, k=3
    )


def model_selection(
    counts: Sequence[int], times: Sequence[float], capacity: float
) -> List[Fit]:
    """All four candidate forms, best AIC first.

    AICc is reported by Fit.aicc and is None when n - k - 1 <= 0, so a
    small-sample comparison does not silently fall back to AIC.
    """
    fits = [
        fit_mechanism(counts, times, capacity),
        fit_linear(counts, times),
        fit_log_linear(counts, times),
        fit_power_law(counts, times),
    ]
    return sorted(fits, key=lambda f: f.aic)


def loo_relative_rmse(
    counts: Sequence[int], times: Sequence[float], capacity: float, name: str = "mechanism"
) -> float:
    """Leave-one-out relative RMSE for one candidate form."""
    builders = {
        "mechanism": lambda c, t: fit_mechanism(c, t, capacity),
        "linear": fit_linear,
        "log-linear": fit_log_linear,
        "power-law": fit_power_law,
    }
    predictors = {
        "mechanism": lambda p, n: p["a"] + p["b"] * n + p["c"] * (1 - math.exp(-n / p["B"])),
        "linear": lambda p, n: p["a"] + p["b"] * n,
        "log-linear": lambda p, n: p["a"] + p["b"] * math.log(n),
        "power-law": lambda p, n: p["a"] * n ** p["alpha"],
    }
    errors = []
    for held in range(len(counts)):
        kept_counts = [c for i, c in enumerate(counts) if i != held]
        kept_times = [t for i, t in enumerate(times) if i != held]
        fit = builders[name](kept_counts, kept_times)
        predicted = predictors[name](fit.params, counts[held])
        errors.append(((predicted - times[held]) / times[held]) ** 2)
    return 100.0 * math.sqrt(mean(errors))
