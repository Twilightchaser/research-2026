"""Dependency-free Touchstone 1.x parsing and microwave metrics."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Network:
    frequency_ghz: list[float]
    # s[frequency][destination][source]
    s: list[list[list[complex]]]
    n_ports: int


def _complex_pair(a: float, b: float, fmt: str) -> complex:
    if fmt == "RI":
        return complex(a, b)
    if fmt == "DB":
        return 10 ** (a / 20.0) * cmath.exp(1j * math.radians(b))
    return a * cmath.exp(1j * math.radians(b))


def _frequency_to_ghz(value: float, unit: str) -> float:
    return value * {"HZ": 1e-9, "KHZ": 1e-6, "MHZ": 1e-3, "GHZ": 1.0}[unit]


def read_touchstone(path: str | Path) -> Network:
    path = Path(path)
    suffix = path.suffix.lower()
    if not suffix.startswith(".s") or not suffix.endswith("p"):
        raise ValueError(f"Cannot infer port count from {path.name}")
    try:
        n_ports = int(suffix[2:-1])
    except ValueError as exc:
        raise ValueError(f"Cannot infer port count from {path.name}") from exc
    if n_ports < 1:
        raise ValueError("Touchstone network must contain at least one port")

    unit, fmt = "GHZ", "MA"
    numeric: list[float] = []
    records: list[list[float]] = []
    needed = 1 + 2 * n_ports * n_ports
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.split("!", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            raise ValueError("Touchstone 2.x keyword blocks are not supported")
        if line.startswith("#"):
            parts = line[1:].upper().split()
            if parts:
                if parts[0] not in {"HZ", "KHZ", "MHZ", "GHZ"}:
                    raise ValueError(f"Unsupported frequency unit: {parts[0]}")
                unit = parts[0]
            for candidate in ("RI", "MA", "DB"):
                if candidate in parts:
                    fmt = candidate
            continue
        numeric.extend(float(value.replace("D", "E")) for value in line.split())
        while len(numeric) >= needed:
            records.append(numeric[:needed])
            numeric = numeric[needed:]
    if numeric:
        raise ValueError(f"Incomplete Touchstone record in {path}")
    if not records:
        raise ValueError(f"No network data found in {path}")

    frequencies: list[float] = []
    matrices: list[list[list[complex]]] = []
    for record in records:
        frequencies.append(_frequency_to_ghz(record[0], unit))
        values = [_complex_pair(record[i], record[i + 1], fmt) for i in range(1, needed, 2)]
        matrix = [[0j for _ in range(n_ports)] for _ in range(n_ports)]
        index = 0
        # Touchstone 1.x order: S11,S21,...,SN1,S12,... (column-major).
        for source in range(n_ports):
            for destination in range(n_ports):
                matrix[destination][source] = values[index]
                index += 1
        matrices.append(matrix)
    return Network(frequencies, matrices, n_ports)


def db(value: complex) -> float:
    magnitude = abs(value)
    return 20.0 * math.log10(magnitude) if magnitude > 0 else -math.inf


def wrap_deg(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def angle_deg(value: complex) -> float:
    return math.degrees(cmath.phase(value))


def band_indices(frequencies: Iterable[float], start: float, stop: float) -> list[int]:
    if start > stop:
        raise ValueError("Band start must not exceed band stop")
    return [index for index, frequency in enumerate(frequencies) if start <= frequency <= stop]


def align_networks(a: Network, b: Network, tolerance_ghz: float = 1e-6) -> None:
    if len(a.frequency_ghz) != len(b.frequency_ghz):
        raise ValueError("Networks have different frequency counts")
    if any(abs(x - y) > tolerance_ghz for x, y in zip(a.frequency_ghz, b.frequency_ghz)):
        raise ValueError("Networks are not sampled at the same frequencies")


def phase_shifter_metrics(
    reference: Network,
    shifted: Network,
    start_ghz: float,
    stop_ghz: float,
    target_phase_deg: float = -45.0,
) -> dict[str, float | int]:
    if reference.n_ports != 2 or shifted.n_ports != 2:
        raise ValueError("Phase-shifter metrics require two 2-port networks")
    align_networks(reference, shifted)
    indices = band_indices(reference.frequency_ghz, start_ghz, stop_ghz)
    if not indices:
        raise ValueError("No samples in requested band")

    phase_difference, phase_error, insertion_loss, return_loss = [], [], [], []
    for index in indices:
        delta = wrap_deg(
            angle_deg(shifted.s[index][1][0]) - angle_deg(reference.s[index][1][0])
        )
        phase_difference.append(delta)
        phase_error.append(abs(wrap_deg(delta - target_phase_deg)))
        insertion_loss.append(-db(shifted.s[index][1][0]))
        return_loss.append(-db(shifted.s[index][0][0]))
    return {
        "samples": len(indices),
        "mean_phase_deg": sum(phase_difference) / len(phase_difference),
        "mean_abs_phase_error_deg": sum(phase_error) / len(phase_error),
        "max_abs_phase_error_deg": max(phase_error),
        "mean_insertion_loss_db": sum(insertion_loss) / len(insertion_loss),
        "max_insertion_loss_db": max(insertion_loss),
        "min_return_loss_db": min(return_loss),
        "phase_span_deg": max(phase_difference) - min(phase_difference),
    }


def butler_metrics(
    network: Network,
    input_port: int,
    output_ports: list[int],
    target_progression_deg: float,
    start_ghz: float,
    stop_ghz: float,
) -> dict[str, float | int]:
    if not 1 <= input_port <= network.n_ports:
        raise ValueError("Input port out of range")
    if len(output_ports) < 2 or any(not 1 <= port <= network.n_ports for port in output_ports):
        raise ValueError("At least two valid output ports are required")
    indices = band_indices(network.frequency_ghz, start_ghz, stop_ghz)
    if not indices:
        raise ValueError("No samples in requested band")

    source = input_port - 1
    outputs = [port - 1 for port in output_ports]
    amplitude_imbalance, phase_error, return_loss, excess_loss = [], [], [], []
    for index in indices:
        values = [network.s[index][destination][source] for destination in outputs]
        amplitudes = [db(value) for value in values]
        phases = [angle_deg(value) for value in values]
        amplitude_imbalance.append(max(amplitudes) - min(amplitudes))
        for left, right in zip(phases, phases[1:]):
            phase_error.append(abs(wrap_deg((right - left) - target_progression_deg)))
        return_loss.append(-db(network.s[index][source][source]))
        delivered_power = sum(abs(value) ** 2 for value in values)
        excess_loss.append(
            -10.0 * math.log10(delivered_power) if delivered_power > 0 else math.inf
        )
    return {
        "samples": len(indices),
        "max_amplitude_imbalance_db": max(amplitude_imbalance),
        "mean_amplitude_imbalance_db": sum(amplitude_imbalance) / len(amplitude_imbalance),
        "max_abs_phase_error_deg": max(phase_error),
        "mean_abs_phase_error_deg": sum(phase_error) / len(phase_error),
        "min_return_loss_db": min(return_loss),
        "max_excess_loss_db": max(excess_loss),
    }

