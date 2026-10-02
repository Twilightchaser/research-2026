"""RLC frequency-response analyser (standard library only).

Example:
  python rlc_analyzer.py --topology series --r 10 --l 0.01 --c 1e-6 --start 100 --stop 10000 --points 12 --csv response.csv
"""

from __future__ import annotations

import argparse
import cmath
import csv
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RLC:
    r_ohm: float
    l_h: float
    c_f: float

    def validate(self) -> None:
        if self.r_ohm < 0 or self.l_h <= 0 or self.c_f <= 0:
            raise ValueError("R must be non-negative; L and C must be positive")

    @property
    def resonance_hz(self) -> float:
        return 1 / (2 * math.pi * math.sqrt(self.l_h * self.c_f))


def impedance(circuit: RLC, frequency_hz: float, topology: str) -> complex:
    omega = 2 * math.pi * frequency_hz
    z_l = complex(0, omega * circuit.l_h)
    z_c = complex(0, -1 / (omega * circuit.c_f))
    if topology == "series":
        return complex(circuit.r_ohm, 0) + z_l + z_c
    conductance = 0 if circuit.r_ohm == 0 else 1 / circuit.r_ohm
    admittance = complex(conductance, 0) + 1 / z_l + 1 / z_c
    return 1 / admittance


def sweep(start: float, stop: float, count: int) -> list[float]:
    if start <= 0 or stop <= start or count < 2:
        raise ValueError("require 0 < start < stop and points >= 2")
    ratio = (stop / start) ** (1 / (count - 1))
    return [start * ratio**index for index in range(count)]


def analyze(circuit: RLC, topology: str, frequencies: list[float]) -> list[dict[str, float]]:
    rows = []
    for frequency in frequencies:
        z = impedance(circuit, frequency, topology)
        magnitude = abs(z)
        rows.append(
            {
                "frequency_hz": frequency,
                "z_real_ohm": z.real,
                "z_imag_ohm": z.imag,
                "magnitude_ohm": magnitude,
                "phase_deg": math.degrees(cmath.phase(z)),
                "current_ma_at_1v": 1000 / magnitude,
            }
        )
    return rows


def render(circuit: RLC, topology: str, rows: list[dict[str, float]]) -> None:
    print(f"{topology.title()} RLC | R={circuit.r_ohm:g} ohm, L={circuit.l_h:g} H, C={circuit.c_f:g} F")
    print(f"Calculated resonance: {circuit.resonance_hz:.3f} Hz\n")
    print(f"{'f (Hz)':>12} {'|Z| (ohm)':>14} {'phase (deg)':>14} {'I @ 1 V (mA)':>16}")
    print("-" * 60)
    for row in rows:
        print(f"{row['frequency_hz']:12.3f} {row['magnitude_ohm']:14.5g} {row['phase_deg']:14.3f} {row['current_ma_at_1v']:16.5g}")


def save_csv(destination: Path, rows: list[dict[str, float]]) -> None:
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Calculate a series or parallel RLC frequency response.")
    result.add_argument("--topology", choices=("series", "parallel"), default="series")
    result.add_argument("--r", required=True, type=float, help="resistance in ohms")
    result.add_argument("--l", required=True, type=float, help="inductance in henries")
    result.add_argument("--c", required=True, type=float, help="capacitance in farads")
    result.add_argument("--start", required=True, type=float, help="start frequency in hertz")
    result.add_argument("--stop", required=True, type=float, help="stop frequency in hertz")
    result.add_argument("--points", default=20, type=int)
    result.add_argument("--csv", type=Path, help="optional CSV output")
    return result


def main() -> int:
    args = parser().parse_args()
    circuit = RLC(args.r, args.l, args.c)
    try:
        circuit.validate()
        rows = analyze(circuit, args.topology, sweep(args.start, args.stop, args.points))
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from error
    render(circuit, args.topology, rows)
    if args.csv:
        save_csv(args.csv, rows)
        print(f"\nSaved {len(rows)} samples to {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
