from hfss_automation.tolerance_plan import latin_hypercube


def test_plan_is_deterministic_and_bounded():
    first = latin_hypercube(["height", "gap"], [0.05, 0.1], 20, 42)
    second = latin_hypercube(["height", "gap"], [0.05, 0.1], 20, 42)
    assert first == second
    assert len(first) == 20
    assert len({row["run_id"] for row in first}) == 20
    assert all(abs(float(row["height"].removesuffix("mm"))) <= 0.05 for row in first)
    assert all(abs(float(row["gap"].removesuffix("mm"))) <= 0.1 for row in first)

