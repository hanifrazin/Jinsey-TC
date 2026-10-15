"""Input lookup, automatic per-template destinations and explicit overrides."""
import json
from pathlib import Path

import pytest
import yaml

from jinsey.cli import main


@pytest.fixture
def workspace(root, tmp_path, raw_case, monkeypatch):
    inputs = tmp_path / "data/input"
    inputs.mkdir(parents=True)
    for name in ["testcases.j2", "testcases_clean.j2"]:
        (inputs / name).write_text(json.dumps({"test_cases": [raw_case]}))
    monkeypatch.chdir(tmp_path)
    return ["--fields", str(root / "config/fields.yaml")]


def test_default_source_and_destination(workspace, capsys):
    assert main(["generate", *workspace]) == 0
    stdout = capsys.readouterr().out
    assert f"Template: {Path('data/input/testcases.j2')}" in stdout
    assert str(Path("data/output/testcases/testcases.yaml")) in stdout
    assert Path("data/output/testcases/testcases.xlsx").is_file()
    assert Path(".id_registry.json").is_file()


def test_filename_selects_separate_output_and_shares_registry(workspace, capsys):
    assert main(["generate", *workspace]) == 0
    first_path = Path("data/output/testcases/testcases.yaml")
    before = first_path.read_bytes()
    registry_before = Path(".id_registry.json").read_bytes()
    assert main(["generate", "--template", "testcases_clean.j2", *workspace]) == 0
    assert f"Template: {Path('data/input/testcases_clean.j2')}" in capsys.readouterr().out
    assert Path("data/output/testcases_clean/testcases.xlsx").is_file()
    assert first_path.read_bytes() == before
    assert Path("data/output/testcases_clean/testcases.yaml").read_bytes() == before
    assert Path(".id_registry.json").read_bytes() == registry_before


@pytest.mark.parametrize("kind", ["relative", "absolute", "dot_relative"])
def test_explicit_template_path(workspace, kind, raw_case, tmp_path):
    if kind == "dot_relative":
        template = "./custom.j2"
    else:
        Path("elsewhere").mkdir()
        template = str(tmp_path / "elsewhere/custom.j2") if kind == "absolute" else "elsewhere/custom.j2"
    Path(template).write_text(json.dumps({"test_cases": [raw_case]}))
    assert main(["generate", "--template", template, *workspace]) == 0
    result = yaml.safe_load(Path("data/output/custom/testcases.yaml").read_text())
    assert result["test_cases"][0]["id"] == "TC-001"


def test_full_input_path_and_explicit_output_override(workspace):
    assert main(["generate", "--template", "data/input/testcases_clean.j2",
                 "--output-dir", "custom-output", *workspace]) == 0
    assert Path("custom-output/testcases.yaml").is_file()
    assert not Path("data/output").exists()


def test_missing_filename_reports_resolved_location(workspace, capsys):
    Path("missing.j2").write_text("{}")  # Bare names must select the input directory.
    assert main(["generate", "--template", "missing.j2", *workspace]) == 1
    assert f"Template not found: {Path('data/input/missing.j2')}" in capsys.readouterr().err
    assert not Path("data/output").exists()
    assert not Path(".id_registry.json").exists()


@pytest.mark.parametrize("command", [["validate"], ["generate", "--dry-run"]])
def test_readonly_commands_with_filename(workspace, command, capsys):
    before = set(Path.cwd().rglob("*"))
    assert main([*command, "--template", "testcases_clean.j2", *workspace]) == 0
    stdout = capsys.readouterr().out
    assert f"Template: {Path('data/input/testcases_clean.j2')}" in stdout
    if "--dry-run" in command:
        assert f"Planned output directory: {Path('data/output/testcases_clean')}" in stdout
    assert set(Path.cwd().rglob("*")) == before
