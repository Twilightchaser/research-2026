"""Run a small ADS-backed parameter sweep and select an LPF candidate."""

from __future__ import annotations

import json
import argparse
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
from keysight.ads import dataset


ADS_ROOT = Path(os.environ["HPEESOF_DIR"])


def simulator_environment() -> dict[str, str]:
    env = os.environ.copy()
    arch = "win32_64" if os.name == "nt" else "linux_x86_64"
    env.update(COMPL_DIR=str(ADS_ROOT), SIMARCH=arch, TIBURON_HOME=str(ADS_ROOT / "tiburonda"))
    paths = [ADS_ROOT / "bin", ADS_ROOT / "lib" / arch, ADS_ROOT / f"circuit/lib.{arch}",
             ADS_ROOT / f"adsptolemy/lib.{arch}", ADS_ROOT / "tools" / "python"]
    env["PATH"] = os.pathsep.join(map(str, paths)) + os.pathsep + env.get("PATH", "")
    return env


def metrics(path: Path) -> dict[str, float]:
    with dataset.open(path) as ds:
        frame = ds["SP1.SP"].to_dataframe()
    freq = frame.index.to_numpy(float)
    s11 = 20 * np.log10(np.maximum(np.abs(frame["S[1,1]"].to_numpy()), 1e-15))
    s21 = 20 * np.log10(np.maximum(np.abs(frame["S[2,1]"].to_numpy()), 1e-15))
    passband, stopband = freq <= 2e9, freq >= 5e9
    return {
        "passband_worst_s21_db": float(s21[passband].min()),
        "passband_worst_s11_db": float(s11[passband].max()),
        "stopband_worst_s21_db": float(s21[stopband].max()),
        "stopband_mean_s21_db": float(s21[stopband].mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    base = (workspace / "LPF_generated.net").read_text(encoding="utf-8")
    simulator = ADS_ROOT / "bin" / ("hpeesofsim.exe" if os.name == "nt" else "hpeesofsim")
    results = []
    for cutoff_ghz in (2.5, 3.0, 3.5):
        omega = 2 * math.pi * cutoff_ghz * 1e9
        inductance_nh = 50 / omega * 1e9
        capacitance_pf = 2 / (50 * omega) * 1e12
        text = re.sub(r"L=2 nH", f"L={inductance_nh:.6g} nH", base)
        text = re.sub(r"C=1 pF", f"C={capacitance_pf:.6g} pF", text)
        netlist = workspace / f"LPF_fc_{cutoff_ghz:.1f}GHz.net"
        output = workspace / f"LPF_fc_{cutoff_ghz:.1f}GHz.ds"
        netlist.write_text(text, encoding="utf-8")
        default_output = workspace / "LPF.ds"
        if default_output.exists():
            default_output.unlink()
        completed = subprocess.run([str(simulator), str(netlist)], cwd=workspace,
                                   env=simulator_environment(), capture_output=True, text=True, timeout=300)
        if completed.returncode != 0 or not default_output.exists():
            raise RuntimeError(f"Simulation failed for {cutoff_ghz} GHz: {completed.stderr}")
        if output.exists():
            output.unlink()
        shutil.copy2(default_output, output)
        row = {"cutoff_ghz": cutoff_ghz, "L1_L2_nh": inductance_nh, "C1_pf": capacitance_pf,
               "dataset": str(output), **metrics(output)}
        # Prefer candidates satisfying passband insertion loss, then strongest stopband.
        row["score"] = row["stopband_mean_s21_db"] + 20 * max(0, -0.5 - row["passband_worst_s21_db"])
        results.append(row)
        print(json.dumps(row), flush=True)
    best = min(results, key=lambda item: item["score"])
    (workspace / "LPF_tuning_results.json").write_text(
        json.dumps({"objective": "0.1-2 GHz passband, 5-10 GHz stopband", "best": best, "candidates": results},
                   indent=2), encoding="utf-8")
    print("BEST=" + json.dumps(best), flush=True)


if __name__ == "__main__":
    main()
