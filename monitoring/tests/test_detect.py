"""Unit tests for the deterministic detector. Run: make monitor-test"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import detect  # noqa: E402

# Baseline alternating around 10 with std = 1 (values 9 and 11).
BASE = [9.0, 11.0] * 15


class WesternElectricRules(unittest.TestCase):
    def test_quiet_series_is_none(self):
        r = detect.evaluate(BASE + [10, 9, 11, 10, 10, 9, 11, 10])
        self.assertEqual(r["tier"], "none")
        self.assertIsNone(r["rule"])

    def test_r1_single_point_beyond_3_sigma(self):
        r = detect.evaluate(BASE + [10, 10, 10, 10, 10, 10, 10, 13.5])
        self.assertEqual((r["tier"], r["rule"]), ("3sigma", "R1"))

    def test_r2_two_of_three_beyond_2_sigma(self):
        r = detect.evaluate(BASE + [10, 10, 10, 10, 10, 12.5, 10, 12.5])
        self.assertEqual((r["tier"], r["rule"]), ("2sigma", "R2"))

    def test_r3_four_of_five_beyond_1_sigma(self):
        r = detect.evaluate(BASE + [10, 10, 10, 11.5, 11.5, 10, 11.5, 11.5])
        self.assertEqual((r["tier"], r["rule"]), ("1sigma", "R3"))

    def test_r4_slow_drift_eight_on_one_side(self):
        r = detect.evaluate(BASE + [10.2, 10.3, 10.1, 10.4, 10.2, 10.3, 10.1, 10.2])
        self.assertEqual((r["tier"], r["rule"]), ("1sigma", "R4"))

    def test_direction_up_ignores_good_side(self):
        r = detect.evaluate(BASE + [10, 10, 10, 10, 10, 10, 10, 6.0], direction="up")
        self.assertEqual(r["tier"], "none")

    def test_direction_down_and_both(self):
        series = BASE + [10, 10, 10, 10, 10, 10, 10, 6.0]
        self.assertEqual(detect.evaluate(series, direction="down")["tier"], "3sigma")
        self.assertEqual(detect.evaluate(series, direction="both")["side"], "down")

    def test_insufficient_data(self):
        r = detect.evaluate([1.0, 2.0, 3.0])
        self.assertEqual(r["status"], "insufficient_data")
        self.assertEqual(r["tier"], "none")

    def test_flat_baseline_any_rise_is_3_sigma(self):
        r = detect.evaluate([0.0] * 30 + [0, 0, 0, 0, 0, 0, 0, 0.1])
        self.assertEqual(r["tier"], "3sigma")


class Inputs(unittest.TestCase):
    def test_parse_series_numbers_and_objects(self):
        self.assertEqual(detect.parse_series("[1, 2.5]"), [1.0, 2.5])
        self.assertEqual(detect.parse_series(json.dumps([{"t": "a", "v": 3}, {"t": "b", "v": None}])), [3.0])
        self.assertEqual(detect.parse_series(""), [])


if __name__ == "__main__":
    unittest.main()
