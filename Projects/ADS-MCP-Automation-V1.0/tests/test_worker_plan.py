import pytest

import ads_mcp_server.ads_worker as worker


def test_execute_plan_runs_steps_in_order(monkeypatch):
    monkeypatch.setitem(worker.METHODS, "first", lambda params: {"value": params["value"]})
    monkeypatch.setitem(worker.METHODS, "second", lambda params: {"done": True})
    result = worker._execute_plan({"steps": [
        {"method": "first", "params": {"value": 7}},
        {"method": "second", "params": {}},
    ]})
    assert result["completed"] == 2
    assert result["results"][0]["result"] == {"value": 7}


def test_execute_plan_reports_failing_step(monkeypatch):
    def fail(_params):
        raise ValueError("bad parameter")

    monkeypatch.setitem(worker.METHODS, "fail", fail)
    with pytest.raises(RuntimeError, match=r"step 1 \(fail\): bad parameter"):
        worker._execute_plan({"steps": [{"method": "fail", "params": {}}]})


def test_execute_plan_rejects_ael():
    with pytest.raises(ValueError, match="unsupported method"):
        worker._execute_plan({"steps": [{"method": "ael_call", "params": {}}]})
