"""ADS Bridge — detect ADS installation and manage worker subprocess.

Handles:
- Auto-detection of ADS installation path (env vars, registry, common paths)
- Starting/stopping the ads_worker subprocess (runs inside ADS Python)
- Sending commands to the worker and receiving results via JSON pipe
- Worker crash recovery (max 3 restarts)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import queue
import socket
import threading
import uuid
from typing import Any


# ---------------------------------------------------------------------------
# ADS auto-detection
# ---------------------------------------------------------------------------


def _find_ads_python(override_path: str | None = None) -> str | None:
    """Find the ADS Python executable.

    Resolution order:
    1. override_path (from CLI --ads-path)
    2. ADS_PATH or HPEESOF_DIR environment variables
    3. Windows registry (HKLM\\SOFTWARE\\Keysight\\ADS)
    4. Common install paths (Windows + Linux)

    Returns path to python.exe (Win) or python (Linux), or None.
    """
    candidates: list[str] = []

    # 1. CLI override
    if override_path:
        candidates.append(override_path)

    # 2. Environment variables
    for var in ("ADS_PATH", "HPEESOF_DIR"):
        val = os.environ.get(var, "")
        if val:
            candidates.append(val)

    # 3. Windows registry
    if sys.platform == "win32":
        ads_dirs = _scan_registry()
        candidates.extend(ads_dirs)

    # 4. Common paths
    if sys.platform == "win32":
        for drive in ("D:", "C:"):
            patterns = [
                f"{drive}\\ADS*",
                f"{drive}\\Program Files\\Keysight\\ADS*",
            ]
            candidates.extend(_glob_dirs(drive, patterns))
    else:
        candidates.extend(_glob_dirs("/", ["/usr/local/Keysight/ADS*", "/opt/Keysight/ADS*"]))

    # Verify each candidate
    for candidate in candidates:
        result = _verify_ads_path(candidate)
        if result:
            return result

    return None


def _scan_registry() -> list[str]:
    """Scan Windows registry for ADS installations. Returns list of ADS root dirs."""
    try:
        import winreg
    except ImportError:
        return []

    ads_paths = []
    for hive_name, hive in [("HKLM", winreg.HKEY_LOCAL_MACHINE), ("HKCU", winreg.HKEY_CURRENT_USER)]:
        try:
            key = winreg.OpenKey(hive, r"SOFTWARE\Keysight\ADS")
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    # Parse version number from subkey name (e.g., "6.30" -> ADS 2026)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        root_path, _ = winreg.QueryValueEx(subkey, "RootPath")
                        if os.path.isdir(root_path):
                            ads_paths.append(root_path)
                    except OSError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            continue

    # Also try the simpler key
    for hive_name, hive in [("HKLM", winreg.HKEY_LOCAL_MACHINE), ("HKCU", winreg.HKEY_CURRENT_USER)]:
        for subpath in [r"SOFTWARE\Keysight\EEsof", r"SOFTWARE\Keysight"]:
            try:
                key = winreg.OpenKey(hive, subpath)
                try:
                    root_path, _ = winreg.QueryValueEx(key, "HPEESOF_DIR")
                    if os.path.isdir(root_path) and root_path not in ads_paths:
                        ads_paths.append(root_path)
                except OSError:
                    pass
                finally:
                    winreg.CloseKey(key)
            except OSError:
                continue

    return ads_paths


def _glob_dirs(base: str, patterns: list[str]) -> list[str]:
    """Glob for directories matching patterns under base."""
    import glob
    result = []
    for pattern in patterns:
        try:
            for path in glob.glob(pattern):
                if os.path.isdir(path):
                    result.append(path)
        except Exception:
            pass
    return result


def _verify_ads_path(ads_path: str) -> str | None:
    """Verify an ADS root path has a usable Python interpreter.

    Accepts either an ADS root path (e.g., D:\\ADS 2026) or a direct python path.
    Returns the Python executable path, or None.
    """
    # If it points directly to a python executable
    if os.path.isfile(ads_path):
        name = os.path.basename(ads_path).lower()
        if "python" in name:
            return ads_path

    # Try tools/python/python.exe (Win) or tools/python/python (Linux)
    python_name = "python.exe" if sys.platform == "win32" else "python"
    python_path = os.path.join(ads_path, "tools", "python", python_name)
    if os.path.isfile(python_path):
        return python_path

    # ADS 2026 alternative layout
    python_path = os.path.join(ads_path, "python", python_name)
    if os.path.isfile(python_path):
        return python_path

    return None


def _ads_root_from_python(python_path: str) -> str:
    """Infer the ADS root without assuming a single bundled-Python layout."""
    current = os.path.abspath(os.path.dirname(python_path))
    for _ in range(5):
        if os.path.isfile(os.path.join(current, "bin", "hpeesofsim.exe")) or os.path.isdir(os.path.join(current, "oalibs")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    # Legacy tools/python/python layout fallback.
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(python_path))))


def interactive_ads_running() -> bool:
    """Detect the ADS Design Environment GUI before starting automation mode."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq hpeesofde.exe", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "hpeesofde.exe" in result.stdout.lower()
        result = subprocess.run(["pgrep", "-x", "hpeesofde"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def simulator_environment(ads_root: str) -> dict[str, str]:
    """Build the documented runtime environment for hpeesofsim."""
    root = os.path.abspath(ads_root)
    arch = "win32_64" if sys.platform == "win32" else "linux_x86_64"
    env = os.environ.copy()
    env.update(HPEESOF_DIR=root, COMPL_DIR=root, SIMARCH=arch, TIBURON_HOME=os.path.join(root, "tiburonda"))
    runtime_paths = [
        os.path.join(root, "bin"),
        os.path.join(root, "lib", arch),
        os.path.join(root, f"circuit/lib.{arch}"),
        os.path.join(root, f"adsptolemy/lib.{arch}"),
        os.path.join(root, "tools", "python"),
    ]
    env["PATH"] = os.pathsep.join(runtime_paths) + os.pathsep + env.get("PATH", "")
    return env


# ---------------------------------------------------------------------------
# Worker subprocess management
# ---------------------------------------------------------------------------

MAX_RESTARTS = 3
START_TIMEOUT = float(os.environ.get("ADS_MCP_START_TIMEOUT", "45"))
CMD_TIMEOUT = float(os.environ.get("ADS_MCP_COMMAND_TIMEOUT", "60"))


class AdsBridge:
    """Manages the ads_worker subprocess and provides a call() method."""

    def __init__(self, ads_python_path: str, worker_path: str):
        self._ads_python = ads_python_path
        self._worker_path = worker_path
        self._process: subprocess.Popen | None = None
        self._restart_count = 0
        self._ready = False
        self._stdout_queue: queue.Queue[str | None] = queue.Queue()
        self._stderr_tail: list[str] = []
        self._io_lock = threading.Lock()
        self._socket: socket.socket | None = None
        self._socket_file = None

    def _read_stdout(self) -> None:
        assert self._process and self._process.stdout
        for line in self._process.stdout:
            self._stdout_queue.put(line)
        self._stdout_queue.put(None)

    def _read_stderr(self) -> None:
        assert self._process and self._process.stderr
        for line in self._process.stderr:
            line = line.rstrip()
            if line:
                self._stderr_tail.append(line)
                del self._stderr_tail[:-20]
                print(f"[ads_worker] {line}", file=sys.stderr)

    def _next_line(self, timeout: float) -> str:
        try:
            line = self._stdout_queue.get(timeout=timeout)
        except queue.Empty as exc:
            detail = " | ".join(self._stderr_tail[-3:])
            raise TimeoutError(f"ADS worker timed out after {timeout:g}s" + (f": {detail}" if detail else "")) from exc
        if line is None:
            raise RuntimeError("ADS worker closed stdout unexpectedly")
        return line

    def _next_response(self, request_id: str, timeout: float) -> dict[str, Any]:
        """Read through incidental ADS stdout until the matching JSON response arrives."""
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"ADS worker timed out after {timeout:g}s")
            line = self._next_line(remaining)
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                print(f"[ads_worker stdout] {line.rstrip()}", file=sys.stderr)
                continue
            if response.get("id") == request_id:
                return response
            print(f"[ads_bridge] Ignoring response with unexpected id: {response.get('id')}", file=sys.stderr)

    @property
    def available(self) -> bool:
        return self._ready

    def start(self) -> bool:
        """Launch the ads_worker subprocess. Returns True on success."""
        env = os.environ.copy()
        ads_root = _ads_root_from_python(self._ads_python)
        env["HPEESOF_DIR"] = ads_root
        env["ADS_PATH"] = ads_root

        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            listener.settimeout(START_TIMEOUT)
            port = listener.getsockname()[1]
            token = uuid.uuid4().hex
            self._process = subprocess.Popen(
                [self._ads_python, "-u", self._worker_path, "--connect", f"127.0.0.1:{port}", "--token", token],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=env,
                cwd=os.path.dirname(self._worker_path),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            self._stdout_queue = queue.Queue()
            threading.Thread(target=self._read_stdout, daemon=True).start()
            threading.Thread(target=self._read_stderr, daemon=True).start()
            self._socket, _ = listener.accept()
            listener.close()
            self._socket.settimeout(START_TIMEOUT)
            self._socket_file = self._socket.makefile("rw", encoding="utf-8", newline="\n")
            auth = json.loads(self._socket_file.readline())
            if auth.get("token") != token:
                raise RuntimeError("ADS worker authentication failed")
            ready_line = self._socket_file.readline()
            ready_msg = json.loads(ready_line)
            if ready_msg.get("ok"):
                self._ready = True
                return True
        except Exception as exc:
            print(f"[ads_bridge] Failed to start worker: {exc}", file=sys.stderr)
            self._ready = False
            self.stop()

        return False

    def stop(self):
        """Terminate the worker subprocess."""
        if self._process:
            try:
                if self._socket_file:
                    self._socket_file.close()
                if self._socket:
                    self._socket.close()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
            self._ready = False
            self._socket = None
            self._socket_file = None

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a command to the worker and return the result.

        Returns a dict with either {"ok": True, "result": ...} or
        {"ok": False, "error": ...}.
        """
        if not self._ready:
            return {"ok": False, "error": "ADS worker is not running. Is ADS installed?"}

        req_id = str(uuid.uuid4())
        request = {"id": req_id, "method": method, "params": params or {}}

        try:
            with self._io_lock:
                if not self._process or not self._socket_file or not self._socket:
                    raise RuntimeError("ADS worker process is unavailable")
                self._socket.settimeout(CMD_TIMEOUT)
                self._socket_file.write(json.dumps(request) + "\n")
                self._socket_file.flush()
                response_line = self._socket_file.readline()
                if not response_line:
                    raise RuntimeError("ADS worker closed its control socket")
                response = json.loads(response_line)
                if response.get("id") != req_id:
                    return {"ok": False, "error": "ADS worker returned a mismatched response id"}
                return response

        except (TimeoutError, socket.timeout) as e:
            print(f"[ads_bridge] {e}", file=sys.stderr)
            self.stop()
            return {"ok": False, "error": f"{e}. The worker was stopped; retry to restart it."}

        except (BrokenPipeError, RuntimeError) as e:
            # Worker crashed — try restart
            print(f"[ads_bridge] Worker communication error: {e}", file=sys.stderr)
            return self._handle_crash()

        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"Invalid JSON from worker: {e}"}

        except Exception as e:
            return {"ok": False, "error": f"Bridge error: {e}"}

    def _handle_crash(self) -> dict[str, Any]:
        """Attempt to restart the worker after a crash."""
        self._ready = False
        self._process = None
        self._restart_count += 1

        if self._restart_count > MAX_RESTARTS:
            return {"ok": False, "error": f"ADS worker crashed {self._restart_count} times. Giving up."}

        print(f"[ads_bridge] Worker crashed, restarting (attempt {self._restart_count}/{MAX_RESTARTS})...", file=sys.stderr)
        time.sleep(1)  # Brief delay before restart
        if self.start():
            return {"ok": False, "error": f"ADS worker was restarted after crash (attempt {self._restart_count}). Please retry."}
        else:
            return {"ok": False, "error": f"ADS worker restart failed (attempt {self._restart_count})."}
