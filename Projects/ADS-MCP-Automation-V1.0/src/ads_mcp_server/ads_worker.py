"""ADS Worker — runs inside ADS Python, bridges JSON-RPC to keysight.ads SDK.

Reads JSON commands from stdin (one per line), executes them against the
keysight.ads API, and writes JSON results to stdout. All diagnostic output
goes to stderr.

Protocol:
    Request:  {"id": "<uuid>", "method": "<name>", "params": {...}}
    Success:  {"id": "<uuid>", "ok": true, "result": {...}}
    Error:    {"id": "<uuid>", "ok": false, "error": "<message>"}
"""

from __future__ import annotations

import json
import argparse
import os
import socket
import sys
import traceback
from uuid import uuid4

# ---------------------------------------------------------------------------
# Environment setup: ADS Python needs HPEESOF_DIR and the SDK on sys.path
# ---------------------------------------------------------------------------

_ADS_PATH = os.environ.get("HPEESOF_DIR", os.environ.get("ADS_PATH", ""))
if _ADS_PATH:
    _pkg_path = os.path.join(_ADS_PATH, "tools", "python", "packages")
    if _pkg_path not in sys.path:
        sys.path.insert(0, _pkg_path)


# ---------------------------------------------------------------------------
# Lazy imports — only attempt when ADS is actually needed
# ---------------------------------------------------------------------------

_de = None
_db_uu = None
_ael = None
_dds = None

# Track open designs: design_key -> Design object
_open_designs: dict[str, "object"] = {}
_current_design_key: str | None = None


def _import_ads():
    """Lazy-import keysight.ads modules. Returns (de, db_uu, ael, dds) or raises."""
    global _de, _db_uu, _ael, _dds
    if _de is not None:
        return _de, _db_uu, _ael, _dds
    try:
        from keysight.ads import ael as _ael_mod
        from keysight.ads import de as _de_mod
        from keysight.ads.de import db_uu as _db_uu_mod

        _de = _de_mod
        _db_uu = _db_uu_mod
        _ael = _ael_mod
        # dds may not always be importable if no DDS window
        try:
            from keysight.ads import dds as _dds_mod
            _dds = _dds_mod
        except Exception:
            _dds = None
        return _de, _db_uu, _ael, _dds
    except ImportError as e:
        raise RuntimeError(
            f"Cannot import keysight.ads SDK. "
            f"Check that HPEESOF_DIR is set correctly. Error: {e}"
        ) from e


def _ads_running() -> bool:
    """Return whether this code executes inside the interactive ADS GUI."""
    try:
        de, _, _, _ = _import_ads()
        return bool(de.is_pde_app())
    except Exception:
        return False


def _mk_design_key(library: str, cell: str, view: str) -> str:
    return f"{library}::{cell}::{view}"


def _get_design(key: str | None = None):
    """Get an open design by key, or the current design if key is None."""
    target = key or _current_design_key
    if target is None:
        raise RuntimeError("No design is open. Create or open a design first.")
    design = _open_designs.get(target)
    if design is None:
        raise RuntimeError(f"Design '{target}' is not open.")
    return target, design


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _status(params: dict) -> dict:
    """Get ADS connection status and workspace info."""
    result = {"ads_running": False, "ads_path": _ADS_PATH or "unknown"}

    try:
        de, _, _, _ = _import_ads()
        result["ads_sdk_available"] = True
        result["ads_version"] = de.product_version()
        result["execution_mode"] = "interactive" if de.is_pde_app() else "automation"
        result["automation_available"] = True

        result["ads_running"] = _ads_running()
        try:
            ws = de.active_workspace() if de.workspace_is_open() else None
            if ws:
                result["workspace"] = str(ws.path) if ws else None
                libs = []
                for name in ws.library_names:
                    try:
                        lib = de.get_open_library(name)
                        libs.append({
                            "name": name,
                            "writable": not de.library_is_read_only(name) if hasattr(de, "library_is_read_only") else True,
                        })
                    except Exception:
                        libs.append({"name": name, "writable": "unknown"})
                result["libraries"] = libs
            else:
                result["workspace"] = None
                result["libraries"] = []
        except Exception as e:
                result["workspace"] = f"(error reading: {e})"
                result["libraries"] = []
        result["open_designs"] = list(_open_designs.keys())
        result["current_design"] = _current_design_key
    except RuntimeError as e:
        result["ads_sdk_available"] = False
        result["ads_sdk_error"] = str(e)

    return result


def _open_workspace(params: dict) -> dict:
    path = params["path"]
    de, _, _, _ = _import_ads()
    if de.workspace_is_open():
        de.close_workspace()
    de.open_workspace(path)
    return {"workspace": path}


def _create_workspace(params: dict) -> dict:
    path = params["path"]
    de, _, _, _ = _import_ads()
    if de.workspace_is_open():
        de.close_workspace()
    de.create_workspace(path)
    de.open_workspace(path)
    return {"workspace": path}


def _close_workspace(params: dict) -> dict:
    de, _, _, _ = _import_ads()
    de.close_workspace()
    global _open_designs, _current_design_key
    _open_designs.clear()
    _current_design_key = None
    return {"closed": True}


def _list_libraries(params: dict) -> dict:
    de, _, _, _ = _import_ads()
    ws = de.active_workspace()
    libs = []
    for name in ws.library_names:
        try:
            lib = de.get_open_library(name)
            info = {
                "name": name,
                "path": de.get_path_to_open_library(name),
                "writable": not de.library_is_read_only(name),
            }
        except Exception:
            info = {"name": name, "path": "unknown", "writable": "unknown"}
        libs.append(info)
    return {"libraries": libs}


def _create_library(params: dict) -> dict:
    de, _, _, _ = _import_ads()
    name = params["name"]
    ws = de.active_workspace()
    ws_path = str(ws.path)
    lib_path = os.path.join(ws_path, name)
    de.create_new_library(name, lib_path)
    ws.add_library(name, lib_path, de.LibraryMode.SHARED)
    return {"library": name, "path": lib_path}


def _open_library(params: dict) -> dict:
    de, _, _, _ = _import_ads()
    name = params["name"]
    lib = de.get_open_library(name)
    return {"library": name, "writable": not de.library_is_read_only(name)}


def _list_designs(params: dict) -> dict:
    de, _, _, _ = _import_ads()
    lib_name = params["library"]
    lib = de.get_open_library(lib_name)
    if lib is None:
        raise RuntimeError(f"Library '{lib_name}' is not open.")
    designs = []
    for cell in lib.cells:
        cell_name = cell.name
        for view in cell.views:
            designs.append({"cell": cell_name, "view": view.name})
    return {"library": lib_name, "designs": designs}


def _create_schematic(params: dict) -> dict:
    _, db_uu, _, _ = _import_ads()
    lcv = params["lcv"]
    design = db_uu.create_schematic(lcv)
    key = _mk_design_key(design.library.name, design.cell.name, "schematic")
    _open_designs[key] = design
    global _current_design_key
    _current_design_key = key
    design.save_design()
    return {"design_key": key, "cell": design.cell.name, "library": design.library.name}


def _create_layout(params: dict) -> dict:
    _, db_uu, _, _ = _import_ads()
    lcv = params["lcv"]
    design = db_uu.create_layout(lcv)
    key = _mk_design_key(design.library.name, design.cell.name, "layout")
    _open_designs[key] = design
    global _current_design_key
    _current_design_key = key
    design.save_design()
    return {"design_key": key, "cell": design.cell.name, "library": design.library.name}


def _open_design(params: dict) -> dict:
    de, db_uu, _, _ = _import_ads()
    library = params["library"]
    cell = params["cell"]
    view = params.get("view", "schematic")
    cvr = de.CellviewRef(library, cell, view)
    if not de.design_exists(cvr):
        raise RuntimeError(f"Design '{library}:{cell}:{view}' does not exist.")
    design = db_uu.open_design(cvr, de.db.DesignMode.APPEND)
    key = _mk_design_key(library, cell, view)
    _open_designs[key] = design
    global _current_design_key
    _current_design_key = key
    return {"design_key": key, "library": library, "cell": cell, "view": view}


def _save_design(params: dict) -> dict:
    key = params.get("design_key")
    target_key, design = _get_design(key)
    design.save_design()
    return {"design_key": target_key, "saved": True}


def _close_design(params: dict) -> dict:
    global _current_design_key
    key = params.get("design_key")
    target_key, design = _get_design(key)
    design.close_design()
    del _open_designs[target_key]
    if _current_design_key == target_key:
        _current_design_key = None
        if _open_designs:
            _current_design_key = next(reversed(_open_designs))
    return {"design_key": target_key, "closed": True}


def _add_rectangle(params: dict) -> dict:
    _, _, key, design = _get_design_and_layer(params)
    layer_id = _resolve_layer(design, params["layer"])
    rect = design.add_rectangle(layer_id, (params["x1"], params["y1"]), (params["x2"], params["y2"]))
    return {"design_key": key, "added": "rectangle"}


def _add_polygon(params: dict) -> dict:
    _, _, key, design = _get_design_and_layer(params)
    layer_id = _resolve_layer(design, params["layer"])
    points = [(p[0], p[1]) for p in params["points"]]
    design.add_polygon(layer_id, points)
    return {"design_key": key, "added": "polygon", "num_points": len(points)}


def _add_line(params: dict) -> dict:
    _, _, key, design = _get_design_and_layer(params)
    layer_id = _resolve_layer(design, params["layer"])
    points = [(p[0], p[1]) for p in params["points"]]
    design.add_line(layer_id, points)
    return {"design_key": key, "added": "line", "num_points": len(points)}


def _add_pin(params: dict) -> dict:
    _, db_uu, key, design = _get_design_and_layer(params)
    layer_id = _resolve_layer(design, params["layer"])
    net_name = params["net_name"]
    net = design.find_or_add_net(net_name)
    term = design.add_term(net, net_name, db_uu.TermType.INPUT)
    x, y = params["x"], params["y"]
    dot = design.add_dot(layer_id, (x, y))
    angle = params.get("angle", 0.0)
    pin = design.add_pin(term, dot, angle=angle)
    return {"design_key": key, "added": "pin", "net": net_name, "pin_name": pin.term.name}


def _add_instance(params: dict) -> dict:
    _, db_uu, key, design = _get_design_and_layer(params)
    inst_lib = params["library"]
    inst_cell = params["cell"]
    inst_view = params.get("view", "symbol")
    x, y = params["x"], params["y"]
    angle = params.get("angle", 0.0)
    inst_name = params.get("name", None)

    lcv = f"{inst_lib}:{inst_cell}:{inst_view}"
    de, _, _, _ = _import_ads()
    instance = design.add_instance(
        de.LCVName(inst_lib, inst_cell, inst_view),
        (x, y),
        name=inst_name,
        angle=angle,
    )
    applied = {}
    for parameter, value in params.get("parameters", {}).items():
        instance.parameters[parameter].value = str(value)
        applied[parameter] = str(value)
    return {
        "design_key": key,
        "added": "instance",
        "of": lcv,
        "instance_name": instance.name,
        "parameters": applied,
    }


def _add_wire(params: dict) -> dict:
    _, _, key, design = _get_design_and_layer(params)
    points = [(p[0], p[1]) for p in params["points"]]
    design.add_wire(points)
    return {"design_key": key, "added": "wire", "num_points": len(points)}


def _add_text(params: dict) -> dict:
    _, _, key, design = _get_design_and_layer(params)
    layer_id = _resolve_layer(design, params["layer"])
    text = params["text"]
    x, y = params["x"], params["y"]
    height = params.get("height", 10.0)
    font = params.get("font", "Ariel for CAE")
    db_uu = _import_ads()[1]
    alignment = params.get("alignment", "LOWER_LEFT")
    align_map = {
        "LOWER_LEFT": db_uu.TextAlignment.LOWER_LEFT,
        "LOWER_RIGHT": db_uu.TextAlignment.LOWER_RIGHT,
        "UPPER_LEFT": db_uu.TextAlignment.UPPER_LEFT,
        "UPPER_RIGHT": db_uu.TextAlignment.UPPER_RIGHT,
    }
    text_obj = design.add_text(layer_id, text, (x, y), font, height, align_map.get(alignment, db_uu.TextAlignment.LOWER_LEFT))
    return {"design_key": key, "added": "text"}


def _list_parameters(params: dict) -> dict:
    key = params.get("design_key")
    _, design = _get_design(key)
    props = []
    for prop in design.props:
        props.append({"name": prop.name, "value": str(prop.value), "type": str(prop.type)})
    return {"design_key": key, "parameters": props}


def _set_parameter(params: dict) -> dict:
    key = params.get("design_key")
    _, design = _get_design(key)
    name = params["name"]
    value = params["value"]
    prop = design.find_prop(name)
    if prop is None:
        raise RuntimeError(f"Parameter '{name}' not found in design.")
    prop.set_value(value)
    return {"design_key": key, "parameter": name, "set_to": value}


def _list_layers(params: dict) -> dict:
    _, _, key, design = _get_design_and_layer(params)
    layers = []
    try:
        for layer in design.layers:
            layers.append({"name": layer.name, "id": layer.id, "purpose": str(layer.purpose)})
    except Exception:
        # Fallback: iterate layer list differently
        for i, layer in enumerate(design.layers):
            try:
                layers.append({"name": str(layer), "id": i})
            except Exception:
                pass
    return {"design_key": key, "layers": layers}


def _generate_netlist(params: dict) -> dict:
    _import_ads()
    key = params.get("design_key")
    _, design = _get_design(key)
    netlist = design.generate_netlist()
    return {"design_key": key, "netlist": netlist}


def _ael_call(params: dict) -> dict:
    _, _, ael, _ = _import_ads()
    func = params["function"]
    args = params.get("args", [])
    result = ael.call(func, *args)
    return {"function": func, "result": str(result)}


def _execute_plan(params: dict) -> dict:
    """Execute a bounded sequence in one ADS runtime.

    This is the preferred automation entry point because open design objects do
    not need to survive across worker processes.
    """
    steps = params.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps must be a non-empty JSON array")
    if len(steps) > 200:
        raise ValueError("a plan may contain at most 200 steps")
    forbidden = {"execute_plan", "ael_call"}
    results = []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            raise ValueError(f"step {index} must be an object")
        method = step.get("method", "")
        if method in forbidden or method not in METHODS:
            raise ValueError(f"step {index} uses unsupported method: {method}")
        step_params = step.get("params", {})
        if not isinstance(step_params, dict):
            raise ValueError(f"step {index} params must be an object")
        try:
            value = METHODS[method](step_params)
        except Exception as exc:
            raise RuntimeError(f"plan failed at step {index} ({method}): {exc}") from exc
        results.append({"step": index, "method": method, "result": value})
    return {"completed": len(results), "results": results}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_design_and_layer(params: dict):
    """Helper for layout tools: get the open design and validate layer param.

    Returns (de, db_uu, design_key, design). Layer is resolved separately.
    """
    de, db_uu, _, _ = _import_ads()
    key = params.get("design_key")
    target_key, design = _get_design(key)
    return de, db_uu, target_key, design


def _resolve_layer(design, layer_spec):
    """Resolve a layer specification (name string or numeric id) to a layer ID object."""
    # Try numeric ID first
    if isinstance(layer_spec, (int, float)):
        return int(layer_spec)

    # Try as layer name
    layer_name = str(layer_spec)
    for layer in design.layers:
        if hasattr(layer, "name") and layer.name == layer_name:
            return layer
        if str(layer) == layer_name:
            return layer

    # Fallback: try to find via library tech
    try:
        de, _, _, _ = _import_ads()
        lib = design.library
        if lib and hasattr(lib, "tech") and lib.tech:
            for layer in lib.tech.layers:
                if hasattr(layer, "name") and layer.name == layer_name:
                    return layer
                if str(layer) == layer_name:
                    return layer
    except Exception:
        pass

    raise RuntimeError(f"Layer '{layer_spec}' not found in design or library technology.")


# ---------------------------------------------------------------------------
# Method dispatch
# ---------------------------------------------------------------------------

METHODS = {
    "status": _status,
    "open_workspace": _open_workspace,
    "create_workspace": _create_workspace,
    "close_workspace": _close_workspace,
    "list_libraries": _list_libraries,
    "create_library": _create_library,
    "open_library": _open_library,
    "list_designs": _list_designs,
    "create_schematic": _create_schematic,
    "create_layout": _create_layout,
    "open_design": _open_design,
    "save_design": _save_design,
    "close_design": _close_design,
    "add_rectangle": _add_rectangle,
    "add_polygon": _add_polygon,
    "add_line": _add_line,
    "add_pin": _add_pin,
    "add_instance": _add_instance,
    "add_wire": _add_wire,
    "add_text": _add_text,
    "list_parameters": _list_parameters,
    "set_parameter": _set_parameter,
    "list_layers": _list_layers,
    "generate_netlist": _generate_netlist,
    "ael_call": _ael_call,
    "execute_plan": _execute_plan,
}


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main():
    """Read JSON commands from stdin, write JSON results to stdout. Loop forever."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--connect")
    parser.add_argument("--token")
    args, _ = parser.parse_known_args()
    control_socket = None
    if args.connect:
        host, port = args.connect.rsplit(":", 1)
        control_socket = socket.create_connection((host, int(port)), timeout=30)
        control_socket.settimeout(None)
        reader = control_socket.makefile("r", encoding="utf-8", newline="\n")
        writer = control_socket.makefile("w", encoding="utf-8", newline="\n")
        writer.write(json.dumps({"token": args.token}) + "\n")
        writer.flush()
    else:
        reader, writer = sys.stdin, sys.stdout
    # Signal readiness
    ready_msg = json.dumps({"id": str(uuid4()), "ok": True, "result": "ads_worker ready"})
    writer.write(ready_msg + "\n")
    writer.flush()

    for line in reader:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            err = json.dumps({"id": "", "ok": False, "error": f"Invalid JSON: {e}"})
            writer.write(err + "\n")
            writer.flush()
            continue

        req_id = request.get("id", "")
        method = request.get("method", "")
        params = request.get("params", {})

        handler = METHODS.get(method)
        if handler is None:
            resp = {"id": req_id, "ok": False, "error": f"Unknown method: {method}. Available: {list(METHODS)}"}
        else:
            try:
                result = handler(params)
                resp = {"id": req_id, "ok": True, "result": result}
            except Exception as e:
                tb = traceback.format_exc()
                print(f"[ads_worker] Error in {method}: {tb}", file=sys.stderr, flush=True)
                resp = {"id": req_id, "ok": False, "error": f"{type(e).__name__}: {e}"}

        writer.write(json.dumps(resp, default=str) + "\n")
        writer.flush()

    print("[ads_worker] control channel closed, exiting", file=sys.stderr, flush=True)
    if control_socket:
        control_socket.close()
    # ADS 2026 native modules can crash during CPython interpreter teardown in
    # automation mode, which launches the ADS crash-report dialog even after a
    # successful command. The OS has already reclaimed workspace handles here;
    # bypass native module finalizers to avoid that false crash report.
    os._exit(0)


if __name__ == "__main__":
    main()
