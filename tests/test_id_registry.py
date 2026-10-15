import json
from dataclasses import replace

import pytest

from jinsey.errors import JinseyError
from jinsey.id_registry import IDRegistry
from jinsey.processor import normalize


def test_persistent_ids_reorder_insert_rename_retire(tmp_path, raw_case, fields):
    path = tmp_path / "ids.json"
    case = normalize({"test_cases": [raw_case]}, fields)[1][0]
    registry = IDRegistry(path)
    first, _ = registry.assign("TC", [case, replace(case, key="second")])
    assert [c.id for c in first] == ["TC-001", "TC-002"]
    assert not path.exists()  # Assignment is a preview until committed.
    registry.write(path)
    registry = IDRegistry(path)
    reordered, retired = registry.assign("TC", [replace(case, key="inserted"), replace(case, key="second", scenario="Renamed"), case])
    assert [c.id for c in reordered] == ["TC-003", "TC-002", "TC-001"]
    assert not retired
    result, retired = registry.assign("TC", [replace(case, key="new")])
    assert result[0].id == "TC-004" and retired == ["fictional-login", "inserted", "second"]
    assert registry.assign("TC", [case])[0][0].id == "TC-001"
    assert registry.assign("AUTH", [case])[0][0].id == "AUTH-001"


def test_width_over_999(tmp_path, raw_case, fields):
    case = normalize({"test_cases": [raw_case]}, fields)[1][0]
    registry = IDRegistry(tmp_path / "ids.json")
    registry.data["prefixes"]["TC"] = {"next": 1000, "ids": {"retired": "TC-999"}}
    assert registry.assign("TC", [case])[0][0].id == "TC-1000"
    with pytest.raises(JinseyError, match="duplicate"):
        registry.assign("TC", [case, case])


@pytest.mark.parametrize("data", [None, [], {}, {"version": 2, "prefixes": {}},
    {"version": True, "prefixes": {}}, {"version": 1, "prefixes": []},
    *[{"version": 1, "prefixes": {"TC": scope}} for scope in [
        [], {}, {"next": 0, "ids": {}}, {"next": True, "ids": {}},
        {"next": 2, "ids": {"x": 1}}, {"next": 2, "ids": {"x": "TC-000"}},
        {"next": 2, "ids": {"x": "TC-0001"}}, {"next": 1, "ids": {"x": "TC-001"}},
        {"next": 3, "ids": {"x": "TC-001", "y": "TC-001"}},
        {"next": 2, "ids": {" ": "TC-001"}},
    ]], {"version": 1, "prefixes": {"bad-prefix": {"next": 1, "ids": {}}}},
])
def test_malformed(tmp_path, data):
    path = tmp_path / "ids.json"
    path.write_text(json.dumps(data))
    with pytest.raises(JinseyError, match="Malformed ID registry"):
        IDRegistry(path)


@pytest.mark.parametrize("text", ['{"invalid":', '{"version":1,"version":1,"prefixes":{}}'])
def test_bad_json_and_duplicate_properties(tmp_path, text):
    path = tmp_path / "ids.json"
    path.write_text(text)
    with pytest.raises(JinseyError, match="Malformed ID registry"):
        IDRegistry(path)
