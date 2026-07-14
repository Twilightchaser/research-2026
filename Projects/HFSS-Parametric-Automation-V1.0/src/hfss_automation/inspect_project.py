"""Inspect an HFSS project and write a JSON structure report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, TypeVar


T = TypeVar("T")


def safe_call(func: Callable[[], T]) -> T | str:
    try:
        return func()
    except Exception as exc:  # An inspection should report partial failures.
        return f"ERROR: {type(exc).__name__}: {exc}"


def inspect_project(
    project_path: Path,
    design: str | None,
    version: str | None,
    non_graphical: bool,
) -> dict:
    from ansys.aedt.core import Desktop, Hfss

    report: dict = {"project_path": str(project_path.resolve()), "designs": {}}
    desktop = Desktop(
        version=version,
        non_graphical=non_graphical,
        new_desktop=True,
        close_on_exit=True,
    )
    hfss = Hfss(project=str(project_path.resolve()), design=design, solution_type="Modal")
    try:
        design_names = safe_call(lambda: list(hfss.design_list))
        if isinstance(design_names, str):
            design_names = [hfss.design_name]
        for design_name in design_names:
            safe_call(lambda name=design_name: hfss.set_active_design(name))
            objects = safe_call(lambda: list(hfss.modeler.object_names))
            object_names = objects if isinstance(objects, list) else []
            report["designs"][design_name] = {
                "solution_type": safe_call(lambda: hfss.solution_type),
                "objects": objects,
                "sheet_names": safe_call(lambda: list(hfss.modeler.sheet_names)),
                "solid_names": safe_call(lambda: list(hfss.modeler.solid_names)),
                "boundaries": safe_call(lambda: [
                    {"name": boundary.name, "type": getattr(boundary, "type", "")}
                    for boundary in hfss.boundaries
                ]),
                "setups": safe_call(lambda: list(hfss.setup_names)),
                "excitations": safe_call(lambda: list(hfss.excitations)),
                "candidate_port_objects": [
                    name for name in object_names if "port" in name.lower()
                ],
            }
    finally:
        try:
            hfss.release_desktop(close_projects=True, close_desktop=True)
        except TypeError:
            hfss.release_desktop(close_projects=True)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--design")
    parser.add_argument("--aedt-version", default=None)
    parser.add_argument("--non-graphical", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not args.project.is_file() or args.project.suffix.lower() != ".aedt":
        raise FileNotFoundError(args.project)
    report = inspect_project(args.project, args.design, args.aedt_version, args.non_graphical)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

