import pytest
import yaml

from jinsey.errors import JinseyError
from jinsey.schema import load_fields


def test_load(fields):
    assert fields["priority"].options == ("P0", "P1", "P2")
    assert fields["priority"].default == "P2"


@pytest.mark.parametrize("spec", [None, [], {"fields": []}, {"fields": {}},
    {"fields": {"priority": {"type": "text"}}},
    *[{"fields": {"priority": {"type": "select", "options": opts, "default": "P2"}}}
      for opts in [[], [1], [""], [" P2 "], ["P2", "P2"], ["P0"]]],
    {"fields": {"priority": {"type": "select", "options": ["P2"], "default": "P2", "required": "true"}}},
])
def test_bad_config(tmp_path, spec):
    path = tmp_path / "fields.yaml"
    path.write_text(yaml.safe_dump(spec))
    with pytest.raises(JinseyError, match="[Ff]ield"):
        load_fields(path)


def test_bad_yaml_and_missing(tmp_path):
    path = tmp_path / "fields.yaml"
    with pytest.raises(JinseyError, match="configuration"):
        load_fields(path)
    path.write_text("fields: [invalid")
    with pytest.raises(JinseyError, match="configuration"):
        load_fields(path)
