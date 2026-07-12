import sys
import textwrap
from pathlib import Path

import ads_mcp_server.ads_bridge as bridge_module
from ads_mcp_server.ads_bridge import AdsBridge, _ads_root_from_python, _verify_ads_path, simulator_environment


def _worker(tmp_path, body: str):
    path = tmp_path / "worker.py"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(path)


def test_verify_ads_root_and_direct_python(tmp_path):
    executable = tmp_path / "tools" / "python" / ("python.exe" if sys.platform == "win32" else "python")
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"")
    assert _verify_ads_path(str(tmp_path)) == str(executable)
    assert _verify_ads_path(sys.executable) == sys.executable


def test_ads_root_inference(tmp_path):
    executable = tmp_path / "python" / ("python.exe" if sys.platform == "win32" else "python")
    executable.parent.mkdir()
    executable.write_bytes(b"")
    simulator = tmp_path / "bin" / "hpeesofsim.exe"
    simulator.parent.mkdir()
    simulator.write_bytes(b"")
    assert _ads_root_from_python(str(executable)) == str(tmp_path)


def test_simulator_environment_contains_required_paths(tmp_path):
    env = simulator_environment(str(tmp_path))
    assert env["HPEESOF_DIR"] == str(tmp_path)
    assert env["COMPL_DIR"] == str(tmp_path)
    assert str(tmp_path / "tools" / "python") in env["PATH"]


def test_bridge_round_trip_and_stderr_drain(tmp_path):
    worker = str(Path(__file__).parents[1] / "src" / "ads_mcp_server" / "ads_worker.py")
    bridge = AdsBridge(sys.executable, worker)
    try:
        assert bridge.start()
        response = bridge.call("not_a_method", {"value": 42})
        assert response["ok"] is False
        assert "Unknown method" in response["error"]
    finally:
        bridge.stop()


def test_command_timeout_stops_worker(tmp_path, monkeypatch):
    worker = _worker(tmp_path, """
        import argparse, json, socket, time
        p=argparse.ArgumentParser(); p.add_argument('--connect'); p.add_argument('--token'); a=p.parse_args()
        host,port=a.connect.rsplit(':',1); s=socket.create_connection((host,int(port)))
        f=s.makefile('rw', encoding='utf-8', newline='\\n')
        f.write(json.dumps({'token':a.token})+'\\n'); f.write(json.dumps({'ok':True})+'\\n'); f.flush()
        for line in f:
            time.sleep(10)
    """)
    monkeypatch.setattr(bridge_module, "CMD_TIMEOUT", 0.1)
    bridge = AdsBridge(sys.executable, worker)
    assert bridge.start()
    response = bridge.call("hang")
    assert response["ok"] is False
    assert "timed out" in response["error"]
    assert bridge.available is False
