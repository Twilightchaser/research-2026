import cmath
import math
from pathlib import Path

import pytest

from hfss_automation.touchstone import (
    Network,
    butler_metrics,
    phase_shifter_metrics,
    read_touchstone,
)


def two_port(transmission_phase: float, reflection_mag: float = 0.1) -> Network:
    frequencies = [30.0, 32.5, 35.0]
    transmission = 0.95 * cmath.exp(1j * math.radians(transmission_phase))
    reflection = reflection_mag + 0j
    matrices = [[[reflection, transmission], [transmission, reflection]] for _ in frequencies]
    return Network(frequencies, matrices, 2)


@pytest.mark.parametrize("fmt,data", [
    ("MA", "0.1 0 0.9 -45 0.9 -45 0.1 0"),
    ("DB", "-20 0 -0.91515 -45 -0.91515 -45 -20 0"),
    ("RI", "0.1 0 0.636396 -0.636396 0.636396 -0.636396 0.1 0"),
])
def test_reads_touchstone_formats(tmp_path: Path, fmt: str, data: str):
    path = tmp_path / "network.s2p"
    path.write_text(f"# GHz S {fmt} R 50\n30 {data}\n", encoding="utf-8")
    network = read_touchstone(path)
    assert network.n_ports == 2
    assert abs(network.s[0][1][0]) == pytest.approx(0.9, abs=1e-5)
    assert math.degrees(cmath.phase(network.s[0][1][0])) == pytest.approx(-45, abs=1e-5)


def test_phase_shifter_metrics():
    metrics = phase_shifter_metrics(two_port(0.0), two_port(-45.0), 30.0, 35.0)
    assert metrics["max_abs_phase_error_deg"] < 1e-9
    assert metrics["min_return_loss_db"] > 15.0


def test_butler_metrics():
    matrix = [[0j for _ in range(8)] for _ in range(8)]
    for destination, phase in zip(range(4, 8), [0.0, -45.0, -90.0, -135.0]):
        matrix[destination][0] = 0.5 * cmath.exp(1j * math.radians(phase))
    matrix[0][0] = 0.1
    metrics = butler_metrics(Network([32.0], [matrix], 8), 1, [5, 6, 7, 8], -45, 32, 32)
    assert metrics["max_abs_phase_error_deg"] < 1e-9
    assert metrics["max_amplitude_imbalance_db"] < 1e-9
    assert metrics["max_excess_loss_db"] < 1e-9

