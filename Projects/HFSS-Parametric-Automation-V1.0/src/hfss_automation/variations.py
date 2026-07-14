"""Run isolated HFSS variations against a manually accepted AEDT model.

The workflow deliberately does not generate electromagnetic geometry. Each
run copies a known-good project and changes named design variables only. This
keeps ports, boundaries, materials, mesh operations, and reference planes
identical across baseline and proposed variants.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
import shutil
from typing import Any


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
RESERVED_COLUMNS = {"run_id", "notes"}


def load_plan(path: Path) -> list[dict[str, str]]:
    """Load and validate a CSV variation plan."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "run_id" not in reader.fieldnames:
            raise ValueError("Variation plan must contain a run_id column")
        variable_columns = [name for name in reader.fieldnames if name not in RESERVED_COLUMNS]
        if not variable_columns:
            raise ValueError("Variation plan must contain at least one variable column")
        rows = list(reader)

    if not rows:
        raise ValueError("Variation plan is empty")
    seen: set[str] = set()
    for number, row in enumerate(rows, start=2):
        run_id = (row.get("run_id") or "").strip()
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError(
                f"Invalid run_id on CSV line {number}: {run_id!r}; "
                "use letters, numbers, dot, underscore, or hyphen"
            )
        if run_id in seen:
            raise ValueError(f"Duplicate run_id on CSV line {number}: {run_id}")
        seen.add(run_id)
        row["run_id"] = run_id
    return rows


def variable_assignments(row: dict[str, str]) -> dict[str, str]:
    """Return non-empty HFSS variable assignments from one plan row."""
    return {
        name: raw.strip()
        for name, raw in row.items()
        if name not in RESERVED_COLUMNS and raw is not None and raw.strip()
    }


def apply_variables(hfss: Any, row: dict[str, str]) -> None:
    assignments = variable_assignments(row)
    if not assignments:
        raise ValueError(f"Run {row['run_id']} has no variable assignments")
    for name, value in assignments.items():
        hfss[name] = value


def source_lock_path(source_project: Path) -> Path:
    return source_project.with_suffix(source_project.suffix + ".lock")


def prepare_run_directory(output_root: Path, run_id: str, overwrite: bool) -> Path:
    output_root = output_root.resolve()
    run_dir = (output_root / run_id).resolve()
    if output_root not in run_dir.parents:
        raise ValueError(f"Unsafe run directory: {run_dir}")
    if run_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Run directory already exists: {run_dir}; use --overwrite explicitly")
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    return run_dir


def run_one(
    source_project: Path,
    design_name: str,
    setup_name: str,
    sweep_name: str,
    output_root: Path,
    row: dict[str, str],
    version: str | None,
    solve: bool,
    non_graphical: bool,
    overwrite: bool,
) -> Path:
    """Copy, parameterize, optionally solve, and then close one isolated run."""
    from ansys.aedt.core import Desktop, Hfss

    run_id = row["run_id"]
    run_dir = prepare_run_directory(output_root, run_id, overwrite)
    project_copy = run_dir / f"{source_project.stem}_{run_id}.aedt"
    shutil.copy2(source_project, project_copy)

    desktop = None
    hfss = None
    try:
        desktop = Desktop(
            version=version,
            non_graphical=non_graphical,
            new_desktop=True,
            close_on_exit=True,
        )
        hfss = Hfss(project=str(project_copy), design=design_name, solution_type="Modal")
        apply_variables(hfss, row)
        hfss.save_project()
        if not solve:
            return project_copy

        if setup_name not in hfss.setup_names:
            raise ValueError(f"Setup {setup_name!r} not found; available: {hfss.setup_names}")
        hfss.analyze_setup(setup_name)
        port_count = len(hfss.excitations)
        if port_count < 1:
            raise RuntimeError("No HFSS excitations found; refusing to export an empty network")
        export_path = run_dir / f"{run_id}.s{port_count}p"
        hfss.export_touchstone(
            setup=setup_name,
            sweep=sweep_name,
            output_file=str(export_path),
        )
        return export_path
    finally:
        if hfss is not None:
            try:
                hfss.release_desktop(close_projects=True, close_desktop=True)
            except TypeError:  # Compatibility with older PyAEDT releases.
                hfss.release_desktop(close_projects=True)
        elif desktop is not None:
            try:
                desktop.release_desktop(close_projects=True, close_desktop=True)
            except TypeError:
                desktop.release_desktop(close_projects=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--setup", default="Setup1")
    parser.add_argument("--sweep", default="Sweep")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--aedt-version", default=None, help="Example: 2026.1; default uses latest installed")
    parser.add_argument("--solve", action="store_true", help="Solve and export Touchstone; otherwise build only")
    parser.add_argument("--non-graphical", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing per-run directories")
    parser.add_argument("--allow-locked-source", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print without launching AEDT")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source_project.expanduser().resolve()
    plan = args.plan.expanduser().resolve()
    output = args.output_root.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".aedt":
        raise FileNotFoundError(f"Expected an existing .aedt source project: {source}")
    if source_lock_path(source).exists() and not args.allow_locked_source:
        raise RuntimeError(
            f"Source project appears open: {source_lock_path(source)}. "
            "Close AEDT or pass --allow-locked-source only if you understand the risk."
        )

    rows = load_plan(plan)
    print(f"Validated {len(rows)} run(s); source={source}; output={output}")
    for index, row in enumerate(rows, start=1):
        print(f"[{index}/{len(rows)}] {row['run_id']}: {variable_assignments(row)}")
        if args.dry_run:
            continue
        result = run_one(
            source, args.design, args.setup, args.sweep, output, row,
            args.aedt_version, args.solve, args.non_graphical, args.overwrite,
        )
        print(f"  -> {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

