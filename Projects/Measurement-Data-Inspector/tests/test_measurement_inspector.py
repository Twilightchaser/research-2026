"""Regression tests for measurement_inspector.py.

Run from repository root:
  python -m unittest Projects/Measurement-Data-Inspector/tests/test_measurement_inspector.py
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "measurement_inspector.py"
SPEC = importlib.util.spec_from_file_location("measurement_inspector", MODULE)
inspector = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = inspector
SPEC.loader.exec_module(inspector)


class MeasurementInspectorTests(unittest.TestCase):
    def test_summary_reports_missing_values(self):
        result = inspector.summarize([4.9, 5.0, 5.1], missing_rows=2, total_rows=5)
        self.assertEqual(result.valid_rows, 3)
        self.assertEqual(result.missing_rows, 2)
        self.assertAlmostEqual(result.mean, 5.0)

    def test_iqr_outlier_detection(self):
        values = [4.9, 5.0, 5.0, 5.1, 5.0, 12.0]
        self.assertEqual(inspector.robust_outliers(values), {5})

    def test_reader_skips_invalid_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "measurements.csv"
            source.write_text("time,voltage_v\n0,5.0\n1,\n2,bad\n3,5.2\n", encoding="utf-8")
            values, rows, missing = inspector.read_measurements(source, "voltage_v")
        self.assertEqual(values, [5.0, 5.2])
        self.assertEqual(len(rows), 2)
        self.assertEqual(missing, 2)


if __name__ == "__main__":
    unittest.main()
