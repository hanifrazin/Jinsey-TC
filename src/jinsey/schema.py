"""Shared choice configuration and normalized test case contract."""
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from jinsey.errors import JinseyError
from jinsey.parsing import strict_yaml_load


@dataclass(frozen=True)
class ChoiceField:
    options: tuple[str, ...]
    default: str
    required: bool = True


def load_fields(path: Path) -> dict[str, ChoiceField]:
    try:
        raw = strict_yaml_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise JinseyError(f"Field configuration {path}: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {"fields"} or not isinstance(raw["fields"], dict):
        raise JinseyError("Field configuration must contain a fields mapping")
    if set(raw["fields"]) != {"priority"}:
        raise JinseyError("Field configuration must define only the supported field: priority")
    result = {}
    for name, spec in raw["fields"].items():
        if not isinstance(spec, dict) or spec.get("type") != "select":
            raise JinseyError(f"Field {name}: type must be select")
        options = spec.get("options")
        if (not isinstance(options, list) or not options
                or any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in options)
                or len(set(options)) != len(options)):
            raise JinseyError(f"Field {name}: options must be unique nonempty strings")
        if spec.get("default") not in options or not isinstance(spec.get("required", True), bool):
            raise JinseyError(f"Field {name}: default must be an option and required must be boolean")
        result[name] = ChoiceField(tuple(options), spec["default"], spec.get("required", True))
    return result


@dataclass(frozen=True)
class TestCase:
    key: str
    feature: str
    scenario: str
    steps: str
    expected: str
    precondition: str = ""
    priority: str = "P2"
    tags: tuple[str, ...] = ()
    test_data: Any = None
    test_type: str = ""
    id: str = ""
    prefix: str = "TC"

    def with_id(self, display_id: str) -> "TestCase":
        return replace(self, id=display_id)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data


@dataclass(frozen=True)
class CaseSheet:
    name: str
    source: str
    cases: list[TestCase]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "source": self.source,
                "test_cases": [case.to_dict() for case in self.cases]}


def validate_sheet_names(names: list[str]) -> None:
    if not names:
        raise JinseyError("Workbook must contain at least one test case sheet")
    seen = set()
    for name in names:
        if (not name.strip() or len(name) > 31 or not name.isprintable()
                or re.search(r"[\[\]:*?/\\]", name) or name.startswith("'") or name.endswith("'")):
            raise JinseyError(f"Invalid sheet name {name!r}: rename the .j2 file; use 1–31 printable characters without []:*?/\\ or surrounding apostrophes")
        if name.casefold() == "_choices":
            raise JinseyError("Sheet name '_choices' is reserved for dropdown options; rename the .j2 file")
        if name.casefold() in seen:
            raise JinseyError(f"Duplicate sheet name {name!r} (case-insensitive); rename one .j2 file")
        seen.add(name.casefold())
