# Instructions for AI agents

Use `ads_execute_plan` for modeling. Put workspace creation/opening, library and
design operations, component placement, deterministic connectivity, save, and
netlist generation in one plan. Do not start ADS manually first: headless ADS
automation and the interactive GUI must not run concurrently.

For schematic ports, place `ads_simulation:Term:symbol`; do not use layout pin
layers such as `231`. Pass component values through `parameters_json` or the
plan step's `parameters` object. Prefer explicit net labels when exact
connectivity matters; visual wire overlap alone must be verified in the
generated netlist.

After modeling, inspect the generated netlist and call `ads_run_netlist`.
Success requires `returncode == 0` and a newly written `.ds` file. A process
launch by itself is not proof of a successful simulation.

Never hardcode an ADS install path. Use `ADS_PATH`/`HPEESOF_DIR`. Never disable
antivirus, patch licensing binaries, overwrite an existing workspace, or kill
an interactive ADS process without the user's confirmation that work is saved.
