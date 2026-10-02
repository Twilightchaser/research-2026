"""Create a reproducible sample CSV for Measurement Data Inspector.

Run:
  python generate_demo_data.py --output power_rail_demo.csv --samples 120
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path


def generate(samples: int, seed: int) -> list[dict[str, str]]:
    if samples < 10:
        raise ValueError("samples must be at least 10")
    random_source = random.Random(seed)
    rows: list[dict[str, str]] = []
    for index in range(samples):
        time_s = index * 0.05
        ripple = 0.035 * math.sin(2 * math.pi * 2.0 * time_s)
        noise = random_source.gauss(0.0, 0.006)
        voltage = 5.0 + ripple + noise
        if index == samples // 2:
            voltage += 0.45  # Deliberate transient for the outlier example.
        rows.append(
            {
                "time_s": f"{time_s:.3f}",
                "voltage_v": f"{voltage:.6f}",
                "current_ma": f"{(118.0 + random_source.gauss(0.0, 1.2)):.4f}",
            }
        )
    rows[samples // 3]["voltage_v"] = ""  # Deliberate missing sample.
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic power-rail measurement CSV.")
    parser.add_argument("--output", type=Path, default=Path("power_rail_demo.csv"))
    parser.add_argument("--samples", type=int, default=120)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    try:
        rows = generate(args.samples, args.seed)
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from error

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("time_s", "voltage_v", "current_ma"))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
