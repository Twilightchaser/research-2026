"""Generate and simulate an ADS schematic netlist in one atomic process."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--design", default="demo_lib:LPF:schematic")
    args = parser.parse_args()

    from keysight.ads import de
    from keysight.ads.de import db_uu

    workspace = args.workspace.resolve()
    de.open_workspace(workspace)
    design = db_uu.open_design(args.design)
    netlist_text = design.generate_netlist()
    netlist_path = workspace / "LPF_generated.net"
    netlist_path.write_text(netlist_text, encoding="utf-8")
    design.close_design()
    de.close_workspace()

    ads_root = Path(os.environ["HPEESOF_DIR"])
    simulator = ads_root / "bin" / ("hpeesofsim.exe" if os.name == "nt" else "hpeesofsim")
    sim_env = os.environ.copy()
    sim_env["COMPL_DIR"] = str(ads_root)
    sim_env["SIMARCH"] = "win32_64" if os.name == "nt" else "linux_x86_64"
    sim_env["TIBURON_HOME"] = str(ads_root / "tiburonda")
    runtime_paths = [
        ads_root / "bin",
        ads_root / "lib" / sim_env["SIMARCH"],
        ads_root / f"circuit/lib.{sim_env['SIMARCH']}",
        ads_root / f"adsptolemy/lib.{sim_env['SIMARCH']}",
        ads_root / "tools" / "python",
    ]
    sim_env["PATH"] = os.pathsep.join(map(str, runtime_paths)) + os.pathsep + sim_env.get("PATH", "")
    completed = subprocess.run(
        [str(simulator), str(netlist_path)],
        cwd=workspace,
        env=sim_env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    log_path = workspace / "LPF_simulation.log"
    log_path.write_text(completed.stdout + "\n--- STDERR ---\n" + completed.stderr, encoding="utf-8")
    result = {
        "returncode": completed.returncode,
        "netlist": str(netlist_path),
        "log": str(log_path),
        "datasets": [str(path) for path in workspace.rglob("*.ds")],
    }
    print(json.dumps(result), flush=True)
    os._exit(0 if completed.returncode == 0 else 1)


if __name__ == "__main__":
    main()
