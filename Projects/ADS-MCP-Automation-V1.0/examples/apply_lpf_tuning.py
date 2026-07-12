"""Apply the selected tuning result back to the ADS schematic."""

from __future__ import annotations

import json
import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--design", default="demo_lib:LPF:schematic")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    result = json.loads((workspace / "LPF_tuning_results.json").read_text(encoding="utf-8"))["best"]

    from keysight.ads import de
    from keysight.ads.de import db_uu

    de.open_workspace(workspace)
    design = db_uu.open_design(args.design, de.db.DesignMode.APPEND)
    instances = {item.name: item for item in design.instances}
    for name in ("L1", "L2"):
        instances[name].parameters["L"].value = f"{result['L1_L2_nh']:.8g} nH"
    instances["C1"].parameters["C"].value = f"{result['C1_pf']:.8g} pF"
    design.save_design()
    (workspace / "LPF_generated.net").write_text(design.generate_netlist(), encoding="utf-8")
    design.close_design()
    de.close_workspace()
    print(json.dumps(result), flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
