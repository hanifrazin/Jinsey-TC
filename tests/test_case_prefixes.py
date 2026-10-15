"""Independent prefix counters, fallback, stable identities and export parity."""
import json

import pytest

from jinsey.cli import main
from jinsey.errors import JinseyError
from jinsey.generator import generate, validate
from jinsey.processor import normalize
from jinsey.verification import verify_excel, verify_yaml


@pytest.mark.parametrize("file_prefix,expected", [(None, "TC"), ("AUTH", "AUTH")])
def test_case_prefix_and_fallback(raw_case, fields, file_prefix, expected):
    envelope = {"test_cases": [raw_case, {**raw_case, "key": "other", "prefix": "LOGIN"}]}
    if file_prefix is not None:
        envelope["prefix"] = file_prefix
    _, cases = normalize(envelope, fields)
    assert [case.prefix for case in cases] == [expected, "LOGIN"]
    _, overridden = normalize(envelope, fields, "OVERRIDE")
    assert [case.prefix for case in overridden] == ["OVERRIDE", "OVERRIDE"]


@pytest.mark.parametrize("bad", ["", "login", "A-B", None, 123, []])
def test_bad_case_prefix_is_actionable(raw_case, fields, bad):
    with pytest.raises(JinseyError, match="fictional-login.*Invalid prefix"):
        normalize({"test_cases": [{**raw_case, "prefix": bad}]}, fields)


def test_duplicate_keys_across_prefixes_rejected(raw_case, fields):
    with pytest.raises(JinseyError, match="duplicate key"):
        normalize({"test_cases": [{**raw_case, "prefix": "LOGIN"}, {**raw_case, "prefix": "REGISTER"}]}, fields)


def test_mixed_prefix_counters_reorder_insert_retire(root, tmp_path, raw_case, fields):
    config = root / "config/fields.yaml"
    template = tmp_path / "mixed.j2"
    registry = tmp_path / "registry.json"
    output = tmp_path / "out"
    authored = [
        {**raw_case, "key": "login-one", "prefix": "LOGIN"},
        {**raw_case, "key": "register-one", "prefix": "REGISTER"},
        {**raw_case, "key": "login-two", "prefix": "LOGIN"},
        {**raw_case, "key": "fallback"},
        {**raw_case, "key": "logout-one", "prefix": "LOGOUT"},
    ]

    def write(cases):
        template.write_text(json.dumps({"test_cases": cases}))

    write(authored)
    before_files = set(tmp_path.rglob("*"))
    preview = generate(template, config, output, registry, dry_run=True)
    assert set(tmp_path.rglob("*")) == before_files
    expected = ["LOGIN-001", "REGISTER-001", "LOGIN-002", "TC-001", "LOGOUT-001"]
    assert [case.id for case in preview.cases] == expected
    result = generate(template, config, output, registry)
    assert [case.key for case in result.cases] == [case["key"] for case in authored]
    assert [case.id for case in result.cases] == expected
    verify_yaml(output / "testcases.yaml", result.cases)
    verify_excel(output / "testcases.xlsx", result.cases, fields)
    old_registry = registry.read_bytes()
    assert generate(template, config, output, registry).cases == result.cases
    assert registry.read_bytes() == old_registry

    inserted = {**raw_case, "key": "login-new", "prefix": "LOGIN"}
    write([inserted, *reversed(authored)])
    reordered = generate(template, config, output, registry)
    assert [case.id for case in reordered.cases] == ["LOGIN-003", *reversed(expected)]
    # Retire a key within LOGIN, then create another: LOGIN-001 cannot be reused.
    write([authored[2], {**inserted, "key": "login-another"}])
    retired = generate(template, config, output, registry)
    assert [case.id for case in retired.cases] == ["LOGIN-002", "LOGIN-004"]
    assert "LOGIN:login-one" in retired.retired_keys
    assert json.loads(registry.read_text())["prefixes"]["LOGIN"]["ids"]["login-one"] == "LOGIN-001"
    # Other prefix scopes remain present even when unused in this run.
    assert "REGISTER" in json.loads(registry.read_text())["prefixes"]


@pytest.mark.parametrize("name", ["testcases.j2", "testcases_clean.j2"])
def test_example_templates_use_separate_prefixes(root, tmp_path, fields, name):
    config = root / "config/fields.yaml"
    result = generate(root / "data/input" / name, config, tmp_path / "out", tmp_path / "ids.json")
    assert [case.id for case in result.cases] == [
        *[f"LOGIN-{i:03d}" for i in range(1, 6)],
        *[f"REGISTER-{i:03d}" for i in range(1, 4)],
        "LOGOUT-001", "LOGOUT-002",
    ]
    verify_excel(tmp_path / "out/testcases.xlsx", result.cases, fields)
    verify_yaml(tmp_path / "out/testcases.yaml", result.cases)
    overridden = generate(root / "data/input" / name, config, tmp_path / "out", tmp_path / "ids.json", prefix="AUTH")
    assert [case.id for case in overridden.cases] == [f"AUTH-{i:03d}" for i in range(1, 11)]


def test_templates_still_match(root):
    config = root / "config/fields.yaml"
    assert validate(root / "data/input/testcases.j2", config) == validate(root / "data/input/testcases_clean.j2", config)


def test_mixed_prefix_failure_does_not_commit(root, tmp_path, raw_case, monkeypatch):
    template = tmp_path / "mixed.j2"
    config = root / "config/fields.yaml"
    registry, output = tmp_path / "ids.json", tmp_path / "out"
    template.write_text(json.dumps({"test_cases": [raw_case]}))
    generate(template, config, output, registry)
    paths = [registry, output / "testcases.yaml", output / "testcases.xlsx"]
    before = {path: path.read_bytes() for path in paths}
    template.write_text(json.dumps({"test_cases": [raw_case, {**raw_case, "key": "new", "prefix": "LOGIN"}]}))

    def fail(*args):
        raise OSError("simulated export failure")

    monkeypatch.setattr("jinsey.generator.export_excel", fail)
    with pytest.raises(OSError, match="simulated"):
        generate(template, config, output, registry)
    assert all(path.read_bytes() == old for path, old in before.items())


def test_cli_reports_all_effective_prefixes(root, capsys):
    assert main(["validate", "--template", str(root / "data/input/testcases.j2"),
                 "--fields", str(root / "config/fields.yaml")]) == 0
    assert "prefix LOGIN, REGISTER, LOGOUT" in capsys.readouterr().out
