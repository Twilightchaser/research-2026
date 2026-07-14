"""Audit paired reference and phase-channel Touchstone exports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .touchstone import phase_shifter_metrics, read_touchstone


def audit(root: Path, start: float, stop: float, target: float) -> list[dict]:
    rows = []
    for ref_path in sorted(root.glob("*/exports/ref_channel.s2p")):
        shifted_path = ref_path.with_name("ps_channel.s2p")
        if not shifted_path.exists():
            continue
        metrics = phase_shifter_metrics(
            read_touchstone(ref_path), read_touchstone(shifted_path), start, stop, target
        )
        status, reasons = "PASS_BASELINE", []
        if metrics["max_abs_phase_error_deg"] > 5.0:
            status = "INVALID_BASELINE"
            reasons.append("target phase not achieved")
        if metrics["max_insertion_loss_db"] > 1.0:
            status = "INVALID_BASELINE"
            reasons.append("excessive insertion loss")
        if metrics["min_return_loss_db"] < 15.0:
            status = "INVALID_BASELINE"
            reasons.append("poor input match")
        rows.append({
            "run_id": ref_path.parents[1].name,
            "status": status,
            "reason": "; ".join(reasons),
            **{key: round(value, 5) if isinstance(value, float) else value for key, value in metrics.items()},
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--band-start", type=float, default=30.0)
    parser.add_argument("--band-stop", type=float, default=35.0)
    parser.add_argument("--target-phase", type=float, default=-45.0)
    args = parser.parse_args(argv)
    rows = audit(args.root, args.band_start, args.band_stop, args.target_phase)
    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "existing_run_audit.csv"
    json_path = args.output / "existing_run_audit.json"
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    invalid = sum(row["status"] != "PASS_BASELINE" for row in rows)
    print(f"Audited {len(rows)} paired runs; invalid baseline: {invalid}")
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())

