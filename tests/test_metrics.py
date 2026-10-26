"""Tests for the metrics and the scaling-model fits of Section V-C."""

from __future__ import annotations

import math
import unittest

from scoda.metrics import (
    ci95,
    expansion_ratio,
    expected_occupancy,
    false_positive_rate,
    fit_mechanism,
    interval_secants,
    macro_f1,
    model_selection,
    onboarding_effort,
    prf1,
    reuse_percent,
    throughput,
    time_reduction,
)


class BasicMetricTests(unittest.TestCase):
    def test_throughput_converts_to_per_minute(self):
        self.assertAlmostEqual(throughput(500, 60.0), 500.0)
        self.assertAlmostEqual(throughput(250, 30.0), 500.0)

    def test_reuse_percent(self):
        self.assertAlmostEqual(reuse_percent(92, 100), 92.0)

    def test_onboarding_effort(self):
        self.assertAlmostEqual(onboarding_effort(52.0, 10), 5.2)

    def test_expansion_ratio(self):
        self.assertAlmostEqual(expansion_ratio(464.0, 110.0), 4.21818, places=5)

    def test_time_reduction(self):
        self.assertAlmostEqual(time_reduction(448.0, 12300.0), 0.963577, places=6)

    def test_false_positive_rate(self):
        self.assertAlmostEqual(false_positive_rate(8, 1000), 0.008)

    def test_zero_denominators_are_rejected(self):
        with self.assertRaises(ValueError):
            throughput(10, 0.0)
        with self.assertRaises(ValueError):
            reuse_percent(1, 0)
        with self.assertRaises(ValueError):
            onboarding_effort(1.0, 0)
        with self.assertRaises(ValueError):
            expansion_ratio(1.0, 0.0)


class OracleMetricTests(unittest.TestCase):
    def test_prf1_matches_definition(self):
        stats = prf1(true_pos=90, false_pos=10, false_neg=10)
        self.assertAlmostEqual(stats["precision"], 0.9)
        self.assertAlmostEqual(stats["recall"], 0.9)
        self.assertAlmostEqual(stats["f1"], 0.9)

    def test_prf1_handles_no_predictions(self):
        stats = prf1(true_pos=0, false_pos=0, false_neg=5)
        self.assertEqual(stats["precision"], 0.0)
        self.assertEqual(stats["f1"], 0.0)

    def test_macro_f1_is_unweighted(self):
        # Equal weight per dataset, regardless of dataset size.
        self.assertAlmostEqual(macro_f1([0.907, 0.897, 0.873, 0.896]), 0.89325)


class DispersionTests(unittest.TestCase):
    def test_ci95_needs_two_runs(self):
        with self.assertRaises(ValueError):
            ci95([464.0])

    def test_ci95_brackets_the_mean(self):
        low, high = ci95([460.0, 464.0, 468.0])
        self.assertLess(low, 464.0)
        self.assertGreater(high, 464.0)


class OccupancyTests(unittest.TestCase):
    def test_exact_form_requires_integer_capacity(self):
        with self.assertRaises(ValueError):
            expected_occupancy(28.89, 10, exact=True)

    def test_approximation_accepts_noninteger_capacity(self):
        value = expected_occupancy(28.89, 10, exact=False)
        self.assertGreater(value, 0.0)
        self.assertLess(value, 28.89)

    def test_occupancy_saturates_toward_capacity(self):
        near = expected_occupancy(29, 10_000, exact=True)
        self.assertAlmostEqual(near, 29.0, places=3)

    def test_occupancy_is_nondecreasing_in_tenants(self):
        values = [expected_occupancy(29, n, exact=True) for n in range(1, 60)]
        for earlier, later in zip(values, values[1:]):
            self.assertGreaterEqual(later, earlier)


class SecantTests(unittest.TestCase):
    def test_secant_is_an_interval_average(self):
        secants = interval_secants([1, 10], [48.0, 124.0])
        self.assertAlmostEqual(secants[0], (124.0 - 48.0) / 9)

    def test_mismatched_lengths_are_rejected(self):
        with self.assertRaises(ValueError):
            interval_secants([1, 10], [48.0])

    def test_nonincreasing_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            interval_secants([10, 10], [1.0, 2.0])


class FitTests(unittest.TestCase):
    def setUp(self):
        # A curve generated from the mechanism form, so the fit must recover it.
        self.capacity = 28.89
        self.counts = [1, 5, 10, 15, 25, 35, 50, 75, 100, 125, 150]
        self.times = [
            40.0 + 1.25 * n + 220.0 * (1.0 - math.exp(-n / self.capacity))
            for n in self.counts
        ]

    def test_mechanism_fit_recovers_known_parameters(self):
        fit = fit_mechanism(self.counts, self.times, self.capacity)
        self.assertAlmostEqual(fit.params["a"], 40.0, places=4)
        self.assertAlmostEqual(fit.params["b"], 1.25, places=5)
        self.assertAlmostEqual(fit.params["c"], 220.0, places=4)
        self.assertGreater(fit.r2, 0.9999)

    def test_mechanism_k_counts_residual_variance(self):
        """k = 4 for a, b, c and the variance; B is fixed, not estimated."""
        fit = fit_mechanism(self.counts, self.times, self.capacity)
        self.assertEqual(fit.k, 4)
        self.assertEqual(fit.params["B"], self.capacity)

    def test_aicc_is_none_when_undefined(self):
        fit = fit_mechanism([1, 5, 10, 15, 25], self.times[:5], self.capacity)
        self.assertEqual(fit.n, 5)
        self.assertIsNone(fit.aicc)

    def test_model_selection_prefers_the_generating_form(self):
        best = model_selection(self.counts, self.times, self.capacity)[0]
        self.assertEqual(best.name, "mechanism")


if __name__ == "__main__":
    unittest.main()
