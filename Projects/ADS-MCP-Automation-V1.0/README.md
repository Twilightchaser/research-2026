# ADS MCP Server

An MCP server for automating Keysight Advanced Design System (ADS) through the
official `keysight.ads` Python API.

> This is an independent open-source project. It is not affiliated with or
> endorsed by Keysight Technologies. ADS and PathWave are Keysight trademarks.

## Execution model

```text
MCP client -> Python MCP server -> ADS bundled Python worker -> keysight.ads API
```

The MCP process can use a normal Python installation. ADS database operations
run in ADS's bundled Python so the Keysight API and native libraries are loaded
from the selected installation. The recommended `ads_execute_plan` tool uses a
short-lived worker for one complete modeling transaction.

The worker uses **ADS automation mode**. It can create and edit workspaces,
libraries, schematics, and layouts without attaching to an already-running ADS
GUI. ADS user-interface APIs are not available in this mode. Files created by
the worker can subsequently be opened in the ADS GUI.

On ADS 2026, close the interactive ADS GUI before starting headless MCP
operations. The server intentionally refuses to start a second runtime while
`hpeesofde` is running because that combination can trigger native crash-report
dialogs on some installations.

## Requirements

- A supported, licensed ADS installation with the Python Design Environment API
  (ADS 2024 or newer; ADS 2026 is tested)
- Windows 10/11 or a supported ADS Linux distribution
- Python 3.10 or newer for the MCP process

## Install

```bash
git clone https://github.com/YOUR_ACCOUNT/ads-mcp-server.git
cd ads-mcp-server
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate
python -m pip install -e .
```

## Configure an MCP client

```json
{
  "mcpServers": {
    "ads": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ads_mcp_server"],
      "env": {
        "ADS_PATH": "/path/to/your/ADS-installation"
      }
    }
  }
}
```

`ADS_PATH` is optional when auto-detection succeeds. `HPEESOF_DIR` is also
accepted. `--ads-path PATH` takes precedence when passed on the command line.
The path may be the ADS root or its bundled Python executable.

Optional timeout variables:

- `ADS_MCP_START_TIMEOUT` (default: 45 seconds)
- `ADS_MCP_COMMAND_TIMEOUT` (default: 60 seconds)

## Available tools

- Recommended: `ads_execute_plan`, `ads_run_netlist`
- Connection: `ads_status`
- Workspaces: `ads_open_workspace`, `ads_create_workspace`,
  `ads_close_workspace`
- Libraries: `ads_list_libraries`, `ads_create_library`, `ads_open_library`
- Designs: `ads_list_designs`, `ads_create_schematic`, `ads_create_layout`,
  `ads_open_design`, `ads_save_design`, `ads_close_design`
- Geometry and connectivity: `ads_add_rectangle`, `ads_add_polygon`,
  `ads_add_line`, `ads_add_pin`, `ads_add_instance`, `ads_add_wire`,
  `ads_add_text`
- Inspection: `ads_list_parameters`, `ads_set_parameter`, `ads_list_layers`,
  `ads_generate_netlist`
- Advanced: `ads_ael_call`

The fine-grained tools are useful for inspection and development. For AI
modeling, prefer one atomic plan so workspace/design objects never need to
survive a native worker restart. See [AI workflow](docs/AI_WORKFLOW.md).

`ads_ael_call` is intended for trusted local use. AEL calls that require the
interactive ADS application may not work in automation mode.

## Development and verification

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ads_mcp_server --help
```

For an installation smoke test, close ADS, configure `ADS_PATH`, start the
server, and call `ads_status`. A healthy connection reports
`ads_sdk_available: true` and `execution_mode: automation`.

Unit tests do not require ADS and cover discovery, the worker protocol, stderr
draining, and timeouts. Full integration tests require ADS and a valid license.
The included LPF example has been validated end-to-end on ADS 2026: schematic,
netlist, `hpeesofsim`, dataset reading, parameter sweep, and write-back.

## Scope and limitations

- This project automates the ADS database; it does not simulate mouse or
  keyboard input in the ADS GUI.
- API availability varies by ADS release and installed license bundle.
- `ads_run_netlist` runs text netlists. Dataset interpretation and optimization
  policies remain application-specific; reusable examples are included.
- Linux auto-detection is best effort; set `ADS_PATH` for nonstandard installs.

## Examples and diagnostics

- `examples/create_lpf_demo.py`: deterministic schematic and netlist creation
- `examples/simulate_lpf.py`: documented simulator environment and dataset run
- `examples/tune_lpf.py`: ADS-backed parameter sweep and scoring
- `examples/apply_lpf_tuning.py`: write the selected values back to the design
- [Troubleshooting](docs/TROUBLESHOOTING.md): failure modes and safeguards found
  during real ADS 2026 validation

## License

MIT
