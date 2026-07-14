"""Generate a deterministic Latin-hypercube manufacturing-tolerance plan."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path


def latin_hypercube(
    names: list[str], limits: list[float], count: int, seed: int
) -> list[dict[str, str | float]]:
    if not names or len(names) != len(limits):
        raise ValueError("Tolerance names and limits must be non-empty and equal in length")
    if count < 1 or any(limit < 0 for limit in limits):
        raise ValueError("Sample count must be positive and tolerance limits non-negative")
    rng = random.Random(seed)
    columns: dict[str, list[float]] = {}
    for name, limit in zip(names, limits):
        values = [-limit + 2.0 * limit * ((stratum + rng.random()) / count) for stratum in range(count)]
        rng.shuffle(values)
        columns[name] = values
    return [
        {
            "run_id": f"TOL_{index + 1:03d}",
            **{name: f"{columns[name][index]:+.6f}mm" for name in names},
        }
        for index in range(count)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    tolerances = config["tolerances_mm"]
    rows = latin_hypercube(
        list(tolerances), list(tolerances.values()),
        int(config["tolerance_samples"]), int(config["random_seed"]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} samples to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

