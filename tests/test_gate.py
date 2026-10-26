import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoda import GateDecision, Priority, Verdict, evaluate_gate  # noqa: E402


class GateTests(unittest.TestCase):
    def test_pass_when_rate_meets_threshold(self):
        verdicts = [Verdict.PASS] * 9 + [Verdict.FAIL]
        result = evaluate_gate(verdicts, theta=0.9)
        self.assertEqual(result.decision, GateDecision.PASS)
        self.assertAlmostEqual(result.pass_rate, 0.9)

    def test_block_on_critical_priority_below_threshold(self):
        verdicts = [Verdict.PASS] * 8 + [Verdict.FAIL] * 2
        result = evaluate_gate(verdicts, theta=0.95, priority=Priority.CRITICAL)
        self.assertEqual(result.decision, GateDecision.BLOCK)

    def test_alert_on_standard_priority_below_threshold(self):
        verdicts = [Verdict.PASS] * 8 + [Verdict.FAIL] * 2
        result = evaluate_gate(verdicts, theta=0.95, priority=Priority.STANDARD)
        self.assertEqual(result.decision, GateDecision.ALERT)

    def test_skipped_verdicts_excluded_from_denominator(self):
        verdicts = [Verdict.PASS, Verdict.PASS, Verdict.SKIP, Verdict.SKIP]
        result = evaluate_gate(verdicts, theta=1.0)
        self.assertEqual(result.decision, GateDecision.PASS)
        self.assertEqual(result.total, 4)
        self.assertEqual(result.skipped, 2)

    def test_empty_evaluated_set_is_blocked(self):
        result = evaluate_gate([], theta=0.99)
        self.assertEqual(result.decision, GateDecision.BLOCK)
        self.assertEqual(result.pass_rate, 0.0)

    def test_all_skipped_is_blocked(self):
        result = evaluate_gate([Verdict.SKIP, Verdict.SKIP], theta=0.5)
        self.assertEqual(result.decision, GateDecision.BLOCK)
        self.assertEqual(result.skipped, 2)


if __name__ == "__main__":
    unittest.main()
