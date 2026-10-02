"""Regression tests for rlc_analyzer.py.

Run from repository root:
  python -m unittest Projects/RLC-Frequency-Response-Analyzer/tests/test_rlc_analyzer.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "rlc_analyzer.py"
SPEC = importlib.util.spec_from_file_location("rlc_analyzer", MODULE)
rlc_analyzer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = rlc_analyzer
SPEC.loader.exec_module(rlc_analyzer)


class RLCAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.circuit = rlc_analyzer.RLC(10.0, 0.01, 1e-6)

    def test_resonance_formula(self):
        self.assertAlmostEqual(self.circuit.resonance_hz, 1591.54943, places=3)

    def test_series_impedance_is_resistive_at_resonance(self):
        z = rlc_analyzer.impedance(self.circuit, self.circuit.resonance_hz, "series")
        self.assertAlmostEqual(z.real, 10.0, places=8)
        self.assertAlmostEqual(z.imag, 0.0, places=8)

    def test_sweep_has_requested_endpoints(self):
        points = rlc_analyzer.sweep(100.0, 10000.0, 5)
        self.assertEqual(len(points), 5)
        self.assertAlmostEqual(points[0], 100.0)
        self.assertAlmostEqual(points[-1], 10000.0)

    def test_analysis_current_matches_ohms_law(self):
        row = rlc_analyzer.analyze(self.circuit, "series", [self.circuit.resonance_hz])[0]
        self.assertAlmostEqual(row["magnitude_ohm"], 10.0, places=6)
        self.assertAlmostEqual(row["current_ma_at_1v"], 100.0, places=6)


if __name__ == "__main__":
    unittest.main()
