import pytest

from jinsey.errors import JinseyError
from jinsey.renderer import render_template


@pytest.mark.parametrize("filename", ["testcases.j2", "testcases_clean.j2"])
def test_real_templates(root, filename):
    data = render_template(root / "data/input" / filename)
    assert len(data["test_cases"]) == 10
    assert {c["feature"] for c in data["test_cases"]} == {"Login", "Register", "Logout"}
    common = [c["steps"].strip().splitlines()[:2] for c in data["test_cases"][:5]]
    assert all(lines == common[0] for lines in common)
    assert len({c["steps"] for c in data["test_cases"][:5]}) == 5
    assert len({c["precondition"] for c in data["test_cases"][:5]}) == 1
    assert data["test_cases"][5]["precondition"] != data["test_cases"][0]["precondition"]


@pytest.mark.parametrize("source, message", [
    ("{% if %}", "Template"), ("{{ absent }}", "undefined"),
    ('{"test_cases": [}', "Rendered JSON"), ("[]", "must be an object"),
    ('{% include "missing.j2" %}', "Template"),
])
def test_bad_template(tmp_path, source, message):
    path = tmp_path / "bad.j2"
    path.write_text(source)
    with pytest.raises(JinseyError, match=message):
        render_template(path)


def test_context_and_if(tmp_path):
    path = tmp_path / "context.j2"
    path.write_text('{% if enabled %}{{ {"test_cases": items} | tojson }}{% endif %}')
    assert render_template(path, {"enabled": True, "items": []}) == {"test_cases": []}
