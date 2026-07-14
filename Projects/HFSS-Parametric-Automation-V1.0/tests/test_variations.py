from pathlib import Path

import pytest

from hfss_automation.variations import (
    load_plan,
    prepare_run_directory,
    variable_assignments,
)


def test_loads_bom_csv_and_assignments(tmp_path: Path):
    plan = tmp_path / "plan.csv"
    plan.write_text("run_id,h,offset,notes\ncase_1,3mm,,ok\n", encoding="utf-8-sig")
    rows = load_plan(plan)
    assert rows[0]["run_id"] == "case_1"
    assert variable_assignments(rows[0]) == {"h": "3mm"}


@pytest.mark.parametrize("run_id", ["../escape", "a/b", "", "white space"])
def test_rejects_unsafe_run_ids(tmp_path: Path, run_id: str):
    plan = tmp_path / "plan.csv"
    plan.write_text(f"run_id,h\n{run_id},3mm\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_plan(plan)


def test_existing_run_requires_explicit_overwrite(tmp_path: Path):
    first = prepare_run_directory(tmp_path, "case", overwrite=False)
    (first / "keep.txt").write_text("user data", encoding="utf-8")
    with pytest.raises(FileExistsError):
        prepare_run_directory(tmp_path, "case", overwrite=False)
    second = prepare_run_directory(tmp_path, "case", overwrite=True)
    assert second == first
    assert not (second / "keep.txt").exists()

