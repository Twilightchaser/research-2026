"""Create a self-contained ADS low-pass-filter workspace.

Run this script with ADS's bundled Python, not a system Python.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--library", default="demo_lib")
    parser.add_argument("--cell", default="LPF")
    args = parser.parse_args()

    from keysight.ads import de
    from keysight.ads.de import db_uu

    workspace = args.workspace.resolve()
    if workspace.exists():
        raise FileExistsError(f"Refusing to overwrite existing workspace: {workspace}")

    de.create_workspace(workspace)
    de.open_workspace(workspace)
    library_path = workspace / args.library
    library = de.create_new_library(args.library, library_path)
    de.active_workspace().add_library(args.library, library_path, de.LibraryMode.SHARED)
    design = db_uu.create_schematic(f"{args.library}:{args.cell}:schematic")

    def instance(lib: str, cell: str, xy: tuple[float, float], name: str, angle: float = 0, **parameters):
        item = design.add_instance(db_uu.LCVName(lib, cell, "symbol"), xy, name=name, angle=angle)
        for parameter, value in parameters.items():
            item.parameters[parameter].value = str(value)
        return item

    p1 = instance("ads_simulation", "Term", (-1, 0), "P1", -90, Num="1", Z="50 Ohm")
    instance("ads_rflib", "GROUND", (-1, -1), "G1", -90)
    l1 = instance("ads_rflib", "L", (0, 0), "L1", L="2 nH")
    l2 = instance("ads_rflib", "L", (2, 0), "L2", L="2 nH")
    c1 = instance("ads_rflib", "C", (1.5, -1), "C1", -90, C="1 pF")
    instance("ads_rflib", "GROUND", (1.5, -2), "G2", -90)
    p2 = instance("ads_simulation", "Term", (4, 0), "P2", -90, Num="2", Z="50 Ohm")
    instance("ads_rflib", "GROUND", (4, -1), "G3", -90)
    instance("ads_simulation", "S_Param", (0, -4), "SP1", Start="100 MHz", Stop="10 GHz", Step="100 MHz")

    for points in ([(-1, 0), (0, 0)], [(1, 0), (2, 0)], [(3, 0), (4, 0)], [(1.5, 0), (1.5, -1)]):
        design.add_wire(points)

    def pin(item, number: int):
        return next(value for value in item.inst_pins if value.inst_pin_id.endswith(f".{number}"))

    # Explicit labels make connectivity deterministic in automation mode while
    # the wires retain the expected visual schematic geometry.
    for item, number, label in (
        (p1, 1, "IN"), (l1, 1, "IN"),
        (l1, 2, "MID"), (l2, 1, "MID"), (c1, 1, "MID"),
        (l2, 2, "OUT"), (p2, 1, "OUT"),
    ):
        target_pin = pin(item, number)
        target_pin.add_label(label, target_pin.snap_point)

    design.save_design()
    netlist_path = workspace / "LPF_generated.net"
    netlist_path.write_text(design.generate_netlist(), encoding="utf-8")
    result = {
        "workspace": str(workspace),
        "library": args.library,
        "design": f"{args.library}:{args.cell}:schematic",
        "instances": ["P1", "G1", "L1", "L2", "C1", "G2", "P2", "G3", "SP1"],
        "wires": 4,
        "netlist": str(netlist_path),
    }
    print(json.dumps(result), flush=True)
    de.close_workspace()
    os._exit(0)


if __name__ == "__main__":
    main()
