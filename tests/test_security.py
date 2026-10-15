"""Regression checks for template execution, parsing and artifact integrity."""
import json
from dataclasses import replace
from zipfile import ZipFile

import pytest
import yaml
from openpyxl import load_workbook

from jinsey.errors import JinseyError
from jinsey.exporters.excel_exporter import export_excel
from jinsey.generator import generate
from jinsey.parsing import strict_json_loads, strict_yaml_load
from jinsey.processor import normalize
from jinsey.renderer import render_template


@pytest.mark.parametrize("source", [
    '{{ cycler.__init__.__globals__.os.getcwd() }}',
    '{{ lipsum.__globals__["os"].getcwd() }}',
    '{{ "".__class__.__mro__ }}',
])
def test_template_cannot_introspect_python(tmp_path, source):
    path = tmp_path / "attack.j2"
    path.write_text(source)
    with pytest.raises(JinseyError, match="Template.*unsafe"):
        render_template(path)


def test_template_context_cannot_contain_callable(tmp_path):
    path = tmp_path / "context.j2"
    path.write_text('{{ action() }}')
    called = []
    with pytest.raises(JinseyError, match="JSON data only"):
        render_template(path, {"action": lambda: called.append(True)})
    assert called == []


def test_template_symlink_cannot_read_outside_root(tmp_path):
    root = tmp_path / "templates"
    root.mkdir()
    secret = tmp_path / "private.txt"
    secret.write_text("private sentinel")
    try:
        (root / "leak.j2").symlink_to(secret)
    except OSError:
        pytest.skip("Symlink creation is unavailable for this OS/user")
    path = root / "attack.j2"
    path.write_text('{% include "leak.j2" %}')
    with pytest.raises(JinseyError, match="escapes template directory"):
        render_template(path)


def test_template_parent_traversal_blocked(tmp_path):
    root = tmp_path / "templates"
    root.mkdir()
    (tmp_path / "private.j2").write_text("sentinel")
    path = root / "attack.j2"
    path.write_text('{% include "../private.j2" %}')
    with pytest.raises(JinseyError, match="Template"):
        render_template(path)


def test_template_limits_and_runtime_error(tmp_path, monkeypatch):
    path = tmp_path / "large.j2"
    path.write_text('x' * 100)
    monkeypatch.setattr("jinsey.renderer.MAX_TEMPLATE_BYTES", 50)
    with pytest.raises(JinseyError, match="source exceeds"):
        render_template(path)
    path.write_text('{{ "x" * 20 }}')
    monkeypatch.setattr("jinsey.renderer.MAX_RENDERED_CHARACTERS", 10)
    with pytest.raises(JinseyError, match="rendered output exceeds"):
        render_template(path)
    path.write_text('{{ 1 / 0 }}')
    with pytest.raises(JinseyError, match="Template.*division"):
        render_template(path)


@pytest.mark.parametrize("source", [
    '{"test_cases": [], "test_cases": [1]}',
    '{"test_cases": [], "x": NaN}',
    '{"x": Infinity}', '{"x": -Infinity}', '{"x": 1e999}',
])
def test_ambiguous_or_nonstandard_json_rejected(tmp_path, source):
    path = tmp_path / "bad.j2"
    path.write_text(source)
    with pytest.raises(JinseyError, match="Rendered JSON"):
        render_template(path)


def test_json_normal_nested_values():
    assert strict_json_loads('{"x":[0.25,true,null]}') == {"x": [0.25, True, None]}


def test_control_characters_rejected_in_keys(raw_case, fields):
    with pytest.raises(JinseyError, match="control characters"):
        normalize({"test_cases": [{**raw_case, "key": "login-\x1b[2J"}]}, fields)


@pytest.mark.parametrize("source", [
    'fields:\n  priority: P0\n  priority: P1',
    '!!python/object/apply:os.getcwd []',
    '? [unhashable, key]\n: value',
])
def test_yaml_duplicate_keys_and_object_construction_rejected(source):
    with pytest.raises(yaml.YAMLError):
        strict_yaml_load(source)


@pytest.mark.parametrize("source_kind", ["imported_registry", "imported_output", "lock"])
def test_artifacts_and_locks_cannot_overwrite_sources(root, tmp_path, raw_case, source_kind):
    template = tmp_path / "cases.j2"
    output = tmp_path / "out"
    registry = tmp_path / "ids.json"
    source = tmp_path / "shared.j2"
    if source_kind == "imported_registry":
        registry = source
    elif source_kind == "imported_output":
        source = output / "testcases.yaml"
    else:
        source = registry.with_suffix(".json.lock")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('{% macro shared() %}Shared text{% endmacro %}')
    template.write_text('{% import "' + source.relative_to(tmp_path).as_posix() + '" as shared %}'
                        + json.dumps({"test_cases": [raw_case]}))
    before = source.read_bytes()
    with pytest.raises(JinseyError, match="must not overwrite"):
        generate(template, root / "config/fields.yaml", output, registry)
    assert source.read_bytes() == before
    assert not (output / "testcases.xlsx").exists()


@pytest.mark.parametrize("text", ['=HYPERLINK("https://example.test", "x")', '+1+1', '-1+2', '@SUM(1,2)', '#N/A'])
def test_excel_authored_values_remain_literal_text(tmp_path, raw_case, fields, text):
    case = normalize({"test_cases": [raw_case]}, fields)[1][0]
    case = replace(case, scenario=text)
    path = tmp_path / "literal.xlsx"
    export_excel([case], path, fields)
    workbook = load_workbook(path)
    assert workbook.active['D2'].value == text
    assert workbook.active['D2'].data_type == 's'
    workbook.close()
    with ZipFile(path) as archive:
        assert b'<f>' not in archive.read('xl/worksheets/sheet1.xml')
        assert not any(name.startswith('xl/externalLinks/') for name in archive.namelist())


@pytest.mark.parametrize("character", ['\x00', '\x01', '\ufffe', '\ud800'])
def test_excel_rejects_invalid_xml_text(tmp_path, raw_case, fields, character):
    case = normalize({"test_cases": [raw_case]}, fields)[1][0]
    with pytest.raises(ValueError, match="scenario contains characters forbidden"):
        export_excel([replace(case, scenario='text' + character)], tmp_path / "bad.xlsx", fields)


def test_excel_row_limit_checked_before_writing(tmp_path, raw_case, fields, monkeypatch):
    monkeypatch.setattr('jinsey.exporters.excel_exporter.MAX_DATA_ROWS', 1)
    cases = normalize({"test_cases": [raw_case, {**raw_case, "key": "second"}]}, fields)[1]
    with pytest.raises(ValueError, match="at most 1 test cases"):
        export_excel(cases, tmp_path / "bad.xlsx", fields)
    assert not (tmp_path / "bad.xlsx").exists()


def test_bad_excel_input_does_not_commit_ids_or_outputs(root, tmp_path, template, raw_case):
    config, output, registry = root / "config/fields.yaml", tmp_path / "out", tmp_path / "ids.json"
    result = generate(template, config, output, registry)
    before = {path: path.read_bytes() for path in [*result.artifacts, registry]}
    template.write_text(json.dumps({"test_cases": [{**raw_case, "key": "new", "scenario": "bad\x00text"}]}))
    with pytest.raises(ValueError, match="forbidden in Excel"):
        generate(template, config, output, registry)
    assert all(path.read_bytes() == contents for path, contents in before.items())


def test_registry_symlink_alias_shares_persistent_ids(root, tmp_path, template, raw_case):
    config, registry = root / "config/fields.yaml", tmp_path / "ids.json"
    generate(template, config, tmp_path / "out", registry)
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(registry)
    except OSError:
        pytest.skip("Symlink creation is unavailable for this OS/user")
    template.write_text(json.dumps({"test_cases": [raw_case, {**raw_case, "key": "new-case"}]}))
    result = generate(template, config, tmp_path / "out", alias)
    assert alias.is_symlink()
    assert [case.id for case in result.cases] == ["TC-001", "TC-002"]
    assert json.loads(registry.read_text())["prefixes"]["TC"]["ids"]["new-case"] == "TC-002"
    assert generate(template, config, tmp_path / "out", registry).cases == result.cases
