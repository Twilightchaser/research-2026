"""Measurement CSV quality inspector.

The tool reads a CSV with one numerical measurement column, reports common
data-quality indicators, rejects malformed inputs clearly, and can write a
cleaned CSV with missing rows removed.

Example:
  python measurement_inspector.py sample.csv --column voltage_v --cleaned clean.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Summary:
    total_rows: int
    valid_rows: int
    missing_rows: int
    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float
    outlier_count: int


def read_measurements(source: Path, column: str) -> tuple[list[float], list[dict[str, str]], int]:
    if not source.is_file():
        raise ValueError(f"file does not exist: {source}")
    with source.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or column not in reader.fieldnames:
            available = ", ".join(reader.fieldnames or [])
            raise ValueError(f"column '{column}' was not found; available columns: {available}")
        valid_values: list[float] = []
        clean_rows: list[dict[str, str]] = []
        missing_rows = 0
        for row in reader:
            raw_value = (row.get(column) or "").strip()
            try:
                value = float(raw_value)
                if not math.isfinite(value):
                    raise ValueError
            except ValueError:
                missing_rows += 1
                continue
            valid_values.append(value)
            clean_rows.append(row)
    if not valid_values:
        raise ValueError("no valid numeric measurements were found")
    return valid_values, clean_rows, missing_rows


def robust_outliers(values: list[float]) -> set[int]:
    if len(values) < 4:
        return set()
    q1, q3 = statistics.quantiles(values, n=4, method="inclusive")[0], statistics.quantiles(values, n=4, method="inclusive")[2]
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return {index for index, value in enumerate(values) if value < lower or value > upper}


def summarize(values: list[float], missing_rows: int, total_rows: int) -> Summary:
    outliers = robust_outliers(values)
    deviation = statistics.stdev(values) if len(values) > 1 else 0.0
    return Summary(
        total_rows=total_rows,
        valid_rows=len(values),
        missing_rows=missing_rows,
        minimum=min(values),
        maximum=max(values),
        mean=statistics.fmean(values),
        median=statistics.median(values),
        standard_deviation=deviation,
        outlier_count=len(outliers),
    )


def show(summary: Summary, column: str) -> None:
    print(f"Measurement column: {column}")
    print(f"Rows: {summary.valid_rows}/{summary.total_rows} valid; {summary.missing_rows} invalid or missing")
    print(f"Range: {summary.minimum:.6g} to {summary.maximum:.6g}")
    print(f"Mean: {summary.mean:.6g} | Median: {summary.median:.6g} | Std dev: {summary.standard_deviation:.6g}")
    print(f"IQR-rule outliers: {summary.outlier_count}")


def write_cleaned(destination: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Inspect one numerical measurement column in a CSV file.")
    result.add_argument("source", type=Path, help="input CSV file")
    result.add_argument("--column", required=True, help="numerical column to inspect")
    result.add_argument("--cleaned", type=Path, help="optional clean CSV destination")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        values, clean_rows, missing_rows = read_measurements(args.source, args.column)
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from error
    result = summarize(values, missing_rows, len(clean_rows) + missing_rows)
    show(result, args.column)
    if args.cleaned:
        write_cleaned(args.cleaned, clean_rows)
        print(f"Cleaned CSV written to {args.cleaned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
