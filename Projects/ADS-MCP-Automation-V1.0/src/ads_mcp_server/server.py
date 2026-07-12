"""ADS MCP Server — exposes Keysight ADS operations as MCP tools.

Uses the official mcp Python package for the MCP protocol layer.
All ADS operations are dispatched through AdsBridge -> ads_worker -> keysight.ads SDK.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .ads_bridge import (
    AdsBridge,
    _ads_root_from_python,
    _find_ads_python,
    _verify_ads_path,
    interactive_ads_running,
    simulator_environment,
)

# Path to the worker script that runs inside ADS Python
import os as _os
_WORKER_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "ads_worker.py")

# ---------------------------------------------------------------------------
# Initialize bridge
# ---------------------------------------------------------------------------

_bridge: AdsBridge | None = None


def _get_bridge() -> AdsBridge:
    """Get or initialize the ADS bridge singleton."""
    global _bridge
    if _bridge is not None:
        return _bridge

    if interactive_ads_running():
        raise RuntimeError(
            "The interactive ADS GUI is running. ADS 2026 cannot safely load a second "
            "automation runtime in this configuration. Close ADS before using headless "
            "MCP operations, or use an in-ADS addon for GUI-session control."
        )

    ads_python = _find_ads_python()
    if ads_python is None:
        raise RuntimeError(
            "ADS installation not found. Set ADS_PATH or HPEESOF_DIR environment variable, "
            "or pass --ads-path to the server."
        )

    _bridge = AdsBridge(ads_python, _WORKER_PATH)
    if not _bridge.start():
        raise RuntimeError(
            f"Failed to start ADS worker. ADS Python found at: {ads_python}. "
            f"Ensure ADS 2024+ is installed correctly."
        )
    return _bridge


def _bridge_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call a method on the ADS bridge. Returns the bridge result dict.

    On error, returns {"ok": False, "error": "..."} rather than raising.
    """
    try:
        bridge = _get_bridge()
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    return bridge.call(method, params)


def _atomic_bridge_call(method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Use one worker for one complete operation, then release native state."""
    if interactive_ads_running():
        return {"ok": False, "error": "Close the interactive ADS GUI before running headless automation."}
    ads_python = _find_ads_python()
    if ads_python is None:
        return {"ok": False, "error": "ADS installation not found; set ADS_PATH or HPEESOF_DIR."}
    bridge = AdsBridge(ads_python, _WORKER_PATH)
    try:
        if not bridge.start():
            return {"ok": False, "error": "Failed to start the ADS automation worker."}
        return bridge.call(method, params)
    finally:
        bridge.stop()


def _format_result(result: dict[str, Any]) -> str:
    """Format a bridge result dict as a readable string for the MCP response."""
    if result.get("ok"):
        data = result.get("result", {})
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)
    else:
        return result.get("error", "Unknown error")


def _check_error(result: dict[str, Any]) -> str | None:
    """Return error message if the bridge call failed, otherwise None."""
    if not result.get("ok"):
        return result.get("error", "Unknown error")
    return None


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("ADS MCP Server", instructions="Control Keysight Advanced Design System (ADS)")


# ---------------------------------------------------------------------------
# P0: Connection & Workspace
# ---------------------------------------------------------------------------


@mcp.tool()
def ads_status() -> str:
    """Check ADS availability: running state, version, active workspace, open libraries and designs."""
    result = _bridge_call("status")
    return _format_result(result)


@mcp.tool()
def ads_execute_plan(plan_json: str) -> str:
    """Execute a complete ADS modeling plan atomically (recommended).

    The ADS GUI must be closed. The JSON value must be an array of objects with
    ``method`` and ``params`` keys. Use worker method names without the ``ads_``
    prefix, for example create_workspace, create_library, create_schematic,
    add_instance, add_wire, save_design, and generate_netlist.
    """
    try:
        steps = json.loads(plan_json)
    except json.JSONDecodeError as exc:
        return f"Error: invalid plan_json: {exc}"
    return _format_result(_atomic_bridge_call("execute_plan", {"steps": steps}))


@mcp.tool()
def ads_open_workspace(path: str) -> str:
    """Open an existing ADS workspace at the given absolute path.

    Args:
        path: Absolute path to the workspace directory (e.g., D:/projects/my_workspace_wrk)
    """
    result = _bridge_call("open_workspace", {"path": path})
    return _format_result(result)


@mcp.tool()
def ads_create_workspace(path: str) -> str:
    """Create and open a new ADS workspace at the given absolute path.

    Args:
        path: Absolute path where the new workspace should be created (e.g., D:/projects/new_wrk)
    """
    result = _bridge_call("create_workspace", {"path": path})
    return _format_result(result)


@mcp.tool()
def ads_close_workspace() -> str:
    """Close the currently open workspace. All unsaved changes will be lost."""
    result = _bridge_call("close_workspace")
    return _format_result(result)


# ---------------------------------------------------------------------------
# P1: Library Management
# ---------------------------------------------------------------------------


@mcp.tool()
def ads_list_libraries() -> str:
    """List all libraries in the active workspace with their paths and write permissions."""
    result = _bridge_call("list_libraries")
    return _format_result(result)


@mcp.tool()
def ads_create_library(name: str) -> str:
    """Create a new library in the active workspace.

    Args:
        name: Library name (e.g., 'RF_lib')
    """
    result = _bridge_call("create_library", {"name": name})
    return _format_result(result)


@mcp.tool()
def ads_open_library(name: str) -> str:
    """Open a library in the active workspace.

    Args:
        name: Library name to open
    """
    result = _bridge_call("open_library", {"name": name})
    return _format_result(result)


# ---------------------------------------------------------------------------
# P2: Design Operations
# ---------------------------------------------------------------------------


@mcp.tool()
def ads_list_designs(library: str) -> str:
    """List all cells and views within a library.

    Args:
        library: Name of the library to inspect
    """
    result = _bridge_call("list_designs", {"library": library})
    return _format_result(result)


@mcp.tool()
def ads_create_schematic(lcv: str) -> str:
    """Create a new schematic design.

    Args:
        lcv: Library:Cell:View string (e.g., 'MyLib:MyCell:schematic').
             The view 'schematic' is automatically appended if omitted.
    """
    if ":" not in lcv:
        return "Error: lcv must be in format 'Library:Cell' or 'Library:Cell:View'"
    result = _bridge_call("create_schematic", {"lcv": lcv})
    return _format_result(result)


@mcp.tool()
def ads_create_layout(lcv: str) -> str:
    """Create a new layout design.

    Args:
        lcv: Library:Cell:View string (e.g., 'MyLib:MyCell:layout').
             The view 'layout' is automatically appended if omitted.
    """
    if ":" not in lcv:
        return "Error: lcv must be in format 'Library:Cell' or 'Library:Cell:View'"
    result = _bridge_call("create_layout", {"lcv": lcv})
    return _format_result(result)


@mcp.tool()
def ads_open_design(library: str, cell: str, view: str = "schematic") -> str:
    """Open an existing design for editing.

    Args:
        library: Library name
        cell: Cell name
        view: View type (default 'schematic', or 'layout', 'symbol', etc.)
    """
    result = _bridge_call("open_design", {"library": library, "cell": cell, "view": view})
    return _format_result(result)


@mcp.tool()
def ads_save_design(design_key: str = "") -> str:
    """Save the current open design (or specify a design_key to save a specific one).

    Args:
        design_key: Optional. Design key in format 'Library::Cell::View'. If empty, saves current design.
    """
    params = {}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("save_design", params)
    return _format_result(result)


@mcp.tool()
def ads_close_design(design_key: str = "") -> str:
    """Close a design. If no design_key specified, closes the current design.

    Args:
        design_key: Optional. Design key in format 'Library::Cell::View'.
    """
    params = {}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("close_design", params)
    return _format_result(result)


# ---------------------------------------------------------------------------
# P3: Layout & Schematic Primitives
# ---------------------------------------------------------------------------


@mcp.tool()
def ads_add_rectangle(layer: str, x1: float, y1: float, x2: float, y2: float, design_key: str = "") -> str:
    """Add a rectangle to the current layout.

    Args:
        layer: Layer name or numeric layer ID
        x1, y1: First corner coordinates (user units, typically mils or mm)
        x2, y2: Opposite corner coordinates
        design_key: Optional. Target design key.
    """
    params = {"layer": layer, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_rectangle", params)
    return _format_result(result)


@mcp.tool()
def ads_add_polygon(layer: str, points_json: str, design_key: str = "") -> str:
    """Add a polygon to the current layout.

    Args:
        layer: Layer name or numeric ID
        points_json: JSON array of [x,y] pairs, e.g., '[[0,0],[10,0],[10,10],[0,10]]'
        design_key: Optional. Target design key.
    """
    points = json.loads(points_json)
    params = {"layer": layer, "points": points}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_polygon", params)
    return _format_result(result)


@mcp.tool()
def ads_add_line(layer: str, points_json: str, design_key: str = "") -> str:
    """Add a line or path to the current layout.

    Args:
        layer: Layer name or numeric ID
        points_json: JSON array of [x,y] pairs defining the path, e.g., '[[0,0],[5,0],[5,5]]'
        design_key: Optional. Target design key.
    """
    points = json.loads(points_json)
    params = {"layer": layer, "points": points}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_line", params)
    return _format_result(result)


@mcp.tool()
def ads_add_pin(net_name: str, layer: str, x: float, y: float, angle: float = 0.0, design_key: str = "") -> str:
    """Add a pin (port) to the current schematic or layout.

    Args:
        net_name: Net name for the pin (e.g., 'P1', 'Vdd')
        layer: Layer name or numeric ID
        x, y: Pin coordinates
        angle: Pin rotation angle in degrees (default 0)
        design_key: Optional. Target design key.
    """
    params = {"net_name": net_name, "layer": layer, "x": x, "y": y, "angle": angle}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_pin", params)
    return _format_result(result)


@mcp.tool()
def ads_add_instance(
    library: str,
    cell: str,
    x: float,
    y: float,
    view: str = "symbol",
    angle: float = 0.0,
    name: str = "",
    parameters_json: str = "{}",
    design_key: str = "",
) -> str:
    """Place a component instance in the current design.

    Args:
        library: Source library name (e.g., 'ads_rflib' for built-in RF components)
        cell: Source cell name (e.g., 'L' for inductor, 'C' for capacitor, 'Term' for terminal)
        x, y: Placement coordinates
        view: Source view type (default 'symbol')
        angle: Rotation angle in degrees
        name: Optional instance name (auto-generated if empty)
        parameters_json: Optional JSON object of component parameters, e.g. '{"L":"2 nH"}'
        design_key: Optional. Target design key.

    Examples:
        Place inductor: library='ads_rflib', cell='L'
        Place capacitor: library='ads_rflib', cell='C'
        Place S-param controller: library='ads_simulation', cell='S_Param'
        Place term: library='ads_simulation', cell='Term'
    """
    params = {"library": library, "cell": cell, "view": view, "x": x, "y": y, "angle": angle}
    if name:
        params["name"] = name
    try:
        parameters = json.loads(parameters_json)
    except json.JSONDecodeError as exc:
        return f"Error: invalid parameters_json: {exc}"
    if not isinstance(parameters, dict):
        return "Error: parameters_json must be a JSON object"
    if parameters:
        params["parameters"] = parameters
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_instance", params)
    return _format_result(result)


@mcp.tool()
def ads_add_wire(points_json: str, design_key: str = "") -> str:
    """Add a wire connecting points in a schematic.

    Args:
        points_json: JSON array of [x,y] pairs, e.g., '[[0,0],[5,0]]'
        design_key: Optional. Target design key.
    """
    points = json.loads(points_json)
    params = {"points": points}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_wire", params)
    return _format_result(result)


@mcp.tool()
def ads_add_text(
    layer: str,
    text: str,
    x: float,
    y: float,
    height: float = 10.0,
    font: str = "Ariel for CAE",
    alignment: str = "LOWER_LEFT",
    design_key: str = "",
) -> str:
    """Add a text label to the layout.

    Args:
        layer: Layer name or numeric ID
        text: Text content
        x, y: Text anchor coordinates
        height: Text height in user units (default 10)
        font: Font name (default 'Ariel for CAE')
        alignment: Text alignment — 'LOWER_LEFT', 'LOWER_RIGHT', 'UPPER_LEFT', or 'UPPER_RIGHT'
        design_key: Optional. Target design key.
    """
    params = {"layer": layer, "text": text, "x": x, "y": y, "height": height, "font": font, "alignment": alignment}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("add_text", params)
    return _format_result(result)


# ---------------------------------------------------------------------------
# P4: Parameters, Layers, Simulation
# ---------------------------------------------------------------------------


@mcp.tool()
def ads_list_parameters(design_key: str = "") -> str:
    """List all parameters (variables) of the current design with their values and types.

    Args:
        design_key: Optional. Target design key.
    """
    params = {}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("list_parameters", params)
    return _format_result(result)


@mcp.tool()
def ads_set_parameter(name: str, value: str, design_key: str = "") -> str:
    """Set a design parameter to a new value.

    Args:
        name: Parameter name (e.g., 'L1', 'freq')
        value: New value as a string (e.g., '10 nH', '2.4 GHz', '100 um')
        design_key: Optional. Target design key.
    """
    params = {"name": name, "value": value}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("set_parameter", params)
    return _format_result(result)


@mcp.tool()
def ads_list_layers(design_key: str = "") -> str:
    """List all layers available in the current design.

    Args:
        design_key: Optional. Target design key.
    """
    params = {}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("list_layers", params)
    return _format_result(result)


@mcp.tool()
def ads_generate_netlist(design_key: str = "") -> str:
    """Generate and return the netlist for the current design.

    Args:
        design_key: Optional. Target design key.
    """
    params = {}
    if design_key:
        params["design_key"] = design_key
    result = _bridge_call("generate_netlist", params)
    return _format_result(result)


@mcp.tool()
def ads_run_netlist(netlist_path: str, timeout_seconds: int = 300) -> str:
    """Run an existing ADS text netlist with hpeesofsim.

    Returns the simulator exit code, captured log, and datasets found beside the
    netlist. The ADS GUI does not need to be running.
    """
    path = os.path.abspath(os.path.expanduser(netlist_path))
    if not os.path.isfile(path):
        return f"Error: netlist does not exist: {path}"
    if timeout_seconds < 1 or timeout_seconds > 3600:
        return "Error: timeout_seconds must be between 1 and 3600"
    ads_python = _find_ads_python()
    if not ads_python:
        return "Error: ADS installation not found; set ADS_PATH or HPEESOF_DIR"
    root = _ads_root_from_python(ads_python)
    executable = os.path.join(root, "bin", "hpeesofsim.exe" if sys.platform == "win32" else "hpeesofsim")
    try:
        completed = subprocess.run(
            [executable, path],
            cwd=os.path.dirname(path),
            env=simulator_environment(root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return f"Error: simulation timed out after {timeout_seconds} seconds"
    datasets = [
        os.path.join(os.path.dirname(path), name)
        for name in os.listdir(os.path.dirname(path))
        if name.lower().endswith(".ds")
    ]
    return json.dumps(
        {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "datasets": datasets},
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# P5: Advanced / AEL bridge
# ---------------------------------------------------------------------------


@mcp.tool()
def ads_ael_call(function: str, args_json: str = "[]") -> str:
    """Call an AEL (Application Extension Language) function directly.

    This is the escape hatch for ADS operations not covered by other tools.
    Can call ANY AEL function in ADS.

    Args:
        function: AEL function name (e.g., 'db_get_layerid_for_layer_name')
        args_json: JSON array of arguments (e.g., '[1, "cond"]')
    """
    args = json.loads(args_json)
    result = _bridge_call("ael_call", {"function": function, "args": args})
    return _format_result(result)


# ---------------------------------------------------------------------------
# Entry point for python -m ads_mcp_server
# ---------------------------------------------------------------------------


def run():
    """Run the MCP server (stdio transport)."""
    print(f"[ads_mcp_server] Starting ADS MCP Server...", file=sys.stderr)
    # Do not import the ADS native runtime until a tool is called. Eager startup
    # can conflict with an already-running ADS GUI and trigger crash dialogs.
    mcp.run()
