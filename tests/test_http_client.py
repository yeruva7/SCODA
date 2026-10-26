"""Tests for the service limit of Section V-B and the shared rate limiter."""

from __future__ import annotations

import threading
import time
import unittest

from scoda.http_client import RateLimiter, qps_max


class ServiceLimitTests(unittest.TestCase):
    def test_qps_max_matches_section_v_b(self):
        # QPS_cap * (1 - u_prod) * alpha
        self.assertAlmostEqual(qps_max(150.0, 0.90, 0.95), 14.25)
        self.assertAlmostEqual(qps_max(100.0, 0.80, 0.95), 19.00)

    def test_alpha_one_leaves_full_headroom(self):
        self.assertAlmostEqual(qps_max(50.0, 0.50, 1.0), 25.0)

    def test_full_utilization_leaves_no_headroom(self):
        self.assertAlmostEqual(qps_max(50.0, 1.0, 0.95), 0.0)

    def test_alpha_outside_unit_interval_is_rejected(self):
        for bad in (0.0, -0.1, 1.5):
            with self.assertRaises(ValueError):
                qps_max(50.0, 0.5, bad)

    def test_utilization_outside_unit_interval_is_rejected(self):
        for bad in (-0.1, 1.1):
            with self.assertRaises(ValueError):
                qps_max(50.0, bad, 0.95)


class RateLimiterTests(unittest.TestCase):
    def test_limiter_is_shared_across_threads(self):
        """The cap is an aggregate, so W threads must not each get the rate."""
        rate = 50.0
        limiter = RateLimiter(rate)
        acquisitions = 25

        def worker():
            for _ in range(acquisitions // 5):
                limiter.acquire()

        started = time.monotonic()
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        elapsed = time.monotonic() - started

        # 25 acquisitions at 50/s cannot complete faster than ~0.48 s.
        self.assertGreater(elapsed, (acquisitions - 1) / rate * 0.9)

    def test_nonpositive_rate_is_rejected(self):
        for bad in (0.0, -1.0):
            with self.assertRaises(ValueError):
                RateLimiter(bad)


if __name__ == "__main__":
    unittest.main()
