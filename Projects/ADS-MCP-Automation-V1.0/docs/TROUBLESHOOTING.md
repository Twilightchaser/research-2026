# Troubleshooting and lessons learned

## Problems found during ADS 2026 validation

| Symptom | Root cause | Project safeguard |
|---|---|---|
| ADS crash-report dialogs after MCP calls | A second ADS automation runtime was loaded while `hpeesofde` GUI was running, or native modules crashed during Python teardown | GUI process detection, lazy worker startup, atomic plans, and `os._exit(0)` after the control channel closes |
| Worker waited forever | ADS bundled Python buffered stdin and ADS native code wrote diagnostics to stdout | Worker starts with `-u`; internal control uses authenticated localhost TCP; commands have bounded timeouts |
| JSON protocol broke after opening a workspace | ADS wrote non-JSON messages to stdout | Protocol no longer uses worker stdout |
| `ads_add_pin` failed with `Design has no attribute layers` | Layout-layer pin logic was incorrectly used on a schematic | AI instructions require `ads_simulation:Term` for schematic ports |
| Existing design could not be edited | `READ_WRITE` is not an ADS 2026 `DesignMode` | Existing designs open with `DesignMode.APPEND`; `WRITE` is never used for edits because it can overwrite content |
| Generated netlist call failed | `de.generate_netlist()` was called with a Design instead of a hierarchy | Uses `design.generate_netlist()` |
| Components looked connected but netlisted as separate nodes | Visual wire placement did not establish deterministic automation connectivity | Validate the netlist; use explicit pin net labels for critical connections |
| `hpeesofsim` returned Windows `0xC0000135` | Required ADS DLL and bundled `python313.dll` directories were absent from `PATH` | `simulator_environment()` sets `HPEESOF_DIR`, `COMPL_DIR`, `SIMARCH`, `TIBURON_HOME`, and all documented runtime paths |
| A `.ds` file created with `hpeesofsim -r` could not be opened | `-r` creates a raw output format; changing the suffix does not make it an ADS dataset | Let ADS create its normal dataset; copy it only after simulation completes |
| `vtb.defs` SystemVue include warning | Optional VTB/SystemVue content is not installed or its include is stale | Treated as a warning when circuit simulation and dataset generation still succeed |
| ADS Launcher usage dialog appeared | `ads.exe -h` was used during diagnosis | Do not probe GUI launchers in automated health checks |

## Required definition of success

A modeling task succeeds only when the workspace, OA design database, and
generated netlist all exist and the netlist contains the intended shared node
names. A simulation succeeds only when `hpeesofsim` returns zero and a readable
ADS dataset contains the expected variables, such as `S[1,1]` and `S[2,1]`.

## Permissions and paths

Use a user-writable workspace outside the ADS installation directory. The demo
used an install-directory workspace only because it was explicitly requested;
public examples accept paths as arguments. Refuse to overwrite a pre-existing
workspace unless the caller explicitly handles backup/removal.
