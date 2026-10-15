"""Persistent identities, including retained mappings for retired keys."""
import json
import re
from pathlib import Path

from jinsey.errors import JinseyError
from jinsey.parsing import strict_json_loads
from jinsey.processor import validate_prefix
from jinsey.schema import TestCase


class IDRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict = {"version": 1, "prefixes": {}}
        if path.exists():
            try:
                self.data = strict_json_loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, RecursionError) as exc:
                raise JinseyError(f"Malformed ID registry {path}: {exc}") from exc
        self._validate()

    def _validate(self) -> None:
        try:
            if not isinstance(self.data, dict) or set(self.data) != {"version", "prefixes"}:
                raise ValueError("expected version and prefixes")
            if type(self.data["version"]) is not int or self.data["version"] != 1 or not isinstance(self.data["prefixes"], dict):
                raise ValueError("expected version 1 and prefixes mapping")
            for prefix, scope in self.data["prefixes"].items():
                validate_prefix(prefix)
                if not isinstance(scope, dict) or set(scope) != {"next", "ids"}:
                    raise ValueError(f"{prefix}: expected next and ids")
                if type(scope["next"]) is not int or scope["next"] < 1 or not isinstance(scope["ids"], dict):
                    raise ValueError(f"{prefix}: invalid next counter or ids mapping")
                numbers = []
                for key, value in scope["ids"].items():
                    if not isinstance(key, str) or not key.strip() or key != key.strip() or not key.isprintable():
                        raise ValueError("invalid stable key")
                    if not isinstance(value, str) or not re.fullmatch(re.escape(prefix) + r"-\d{3,}", value):
                        raise ValueError(f"invalid ID {value!r}")
                    number = int(value[len(prefix) + 1:])
                    if number < 1 or value != f"{prefix}-{number:03d}":
                        raise ValueError(f"noncanonical ID {value!r}")
                    numbers.append(number)
                if len(set(numbers)) != len(numbers) or scope["next"] <= max(numbers, default=0):
                    raise ValueError(f"{prefix}: duplicate IDs or unsafe next counter")
        except (ValueError, JinseyError) as exc:
            raise JinseyError(f"Malformed ID registry {self.path}: {exc}") from exc

    def assign(self, prefix: str, cases: list[TestCase]) -> tuple[list[TestCase], list[str]]:
        validate_prefix(prefix)
        scope = self.data["prefixes"].setdefault(prefix, {"next": 1, "ids": {}})
        keys = [case.key for case in cases]
        if len(set(keys)) != len(keys):
            raise JinseyError("Cannot assign IDs: duplicate keys")
        retired = sorted(set(scope["ids"]) - set(keys))
        assigned = []
        for case in cases:
            if case.key not in scope["ids"]:
                scope["ids"][case.key] = f"{prefix}-{scope['next']:03d}"
                scope["next"] += 1
            assigned.append(case.with_id(scope["ids"][case.key]))
        return assigned, retired

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
