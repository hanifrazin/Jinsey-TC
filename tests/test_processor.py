import pytest

from jinsey.errors import JinseyError
from jinsey.processor import normalize, normalize_text, validate_prefix


def test_normalization_defaults(raw_case, fields):
    prefix, cases = normalize({"test_cases": [raw_case]}, fields)
    assert prefix == "TC"
    case = cases[0]
    assert case.steps == "1. Buka Login\n2. Klik Login"
    assert case.expected == "Berhasil\nHalaman utama"
    assert case.priority == "P2" and case.id == "" and case.precondition == ""
    assert normalize_text("\r\n a\r\n\t\n b\n") == "a\nb"
    assert case.with_id("TC-001").to_dict()["tags"] == []


def test_optional_fields_and_prefix(raw_case, fields):
    raw_case.update(precondition=" a\n b", tags=[" smoke "], test_type="positive", test_data={"a": [1, True]})
    prefix, cases = normalize({"prefix": "OLD", "test_cases": [raw_case]}, fields, "AUTH")
    assert prefix == "AUTH"
    assert cases[0].precondition == "a\nb" and cases[0].tags == ("smoke",)
    assert cases[0].test_data == {"a": [1, True]}


@pytest.mark.parametrize("field,value,message", [
    ("priority", "P9", "invalid priority"), ("priority", ["P0"], "invalid priority"),
    ("id", "TC-001", "id is generated"), ("scenario", " ", "required field scenario"),
    ("steps", None, "required field steps"), ("tags", "smoke", "tags"),
    ("tags", [1], "tags"), ("precondition", [], "precondition must"),
    ("test_type", False, "test_type must"), ("key", " padded ", "single line"),
    ("key", "a\nb", "single line"), ("unknown", True, "unknown fields"),
    ("test_data", float("nan"), "valid JSON"),
])
def test_invalid_cases(raw_case, fields, field, value, message):
    raw_case[field] = value
    with pytest.raises(JinseyError, match=message):
        normalize({"test_cases": [raw_case]}, fields)


@pytest.mark.parametrize("field", ["key", "feature", "scenario", "steps", "expected"])
def test_missing_required(raw_case, fields, field):
    raw_case.pop(field)
    with pytest.raises(JinseyError, match=f"required field {field}"):
        normalize({"test_cases": [raw_case]}, fields)


@pytest.mark.parametrize("raw,message", [
    ({}, "nonempty list"), ({"test_cases": []}, "nonempty list"),
    ({"test_cases": [1]}, "expected an object"),
    ({"test_cases": [], "extra": 1}, "unsupported fields"),
])
def test_invalid_envelope(fields, raw, message):
    with pytest.raises(JinseyError, match=message):
        normalize(raw, fields)


def test_duplicate(raw_case, fields):
    with pytest.raises(JinseyError, match="duplicate key"):
        normalize({"test_cases": [raw_case, raw_case]}, fields)


@pytest.mark.parametrize("prefix", ["tc", "", "A-B", "1TC", "A" * 33, None])
def test_bad_prefix(prefix):
    with pytest.raises(JinseyError, match="Invalid prefix"):
        validate_prefix(prefix)
