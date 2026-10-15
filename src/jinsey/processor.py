"""Validate raw cases, normalize text, and number steps exactly once."""
import json
import re
from typing import Any

from jinsey.errors import JinseyError
from jinsey.schema import ChoiceField, TestCase


def validate_prefix(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,31}", value):
        raise JinseyError("Invalid prefix: use 1–32 uppercase letters, digits or underscores, starting with a letter")
    return value


def normalize_text(value: str) -> str:
    return "\n".join(line.strip() for line in value.splitlines() if line.strip())


def normalize(envelope: dict, fields: dict[str, ChoiceField], prefix_override: str | None = None) -> tuple[str, list[TestCase]]:
    if set(envelope) - {"prefix", "test_cases"}:
        raise JinseyError("Envelope contains unsupported fields; allowed: prefix, test_cases")
    prefix = validate_prefix(prefix_override if prefix_override is not None else envelope.get("prefix", "TC"))
    raw_cases = envelope.get("test_cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise JinseyError("test_cases must be a nonempty list")
    seen: set[str] = set()
    cases = []
    required = {"key", "feature", "scenario", "steps", "expected"}
    allowed = required | {"precondition", "priority", "tags", "test_data", "test_type", "prefix"}
    for index, raw in enumerate(raw_cases, 1):
        label = f"Test case #{index}"
        if not isinstance(raw, dict):
            raise JinseyError(f"{label}: expected an object")
        label = f"Test case {raw.get('key', '#' + str(index))!r}"
        if "id" in raw:
            raise JinseyError(f"{label}: id is generated; author a stable key instead")
        if set(raw) - allowed:
            raise JinseyError(f"{label}: unknown fields: {', '.join(sorted(set(raw) - allowed))}")
        for name in required:
            if not isinstance(raw.get(name), str) or not raw[name].strip():
                raise JinseyError(f"{label}: missing or invalid required field {name}")
        key = raw["key"]
        if key != key.strip() or not key.isprintable():
            raise JinseyError(f"{label}: key must be a single line without control characters or surrounding whitespace")
        if key in seen:
            raise JinseyError(f"{label}: duplicate key {key!r}")
        seen.add(key)
        try:
            case_prefix = validate_prefix(
                prefix_override if prefix_override is not None else raw.get("prefix", prefix)
            )
        except JinseyError as exc:
            raise JinseyError(f"{label}: {exc}") from exc
        priority = raw.get("priority", fields["priority"].default)
        if priority not in fields["priority"].options:
            raise JinseyError(f"{label}: invalid priority {priority!r}; choose {', '.join(fields['priority'].options)}")
        for name in ("precondition", "test_type"):
            if name in raw and not isinstance(raw[name], str):
                raise JinseyError(f"{label}: {name} must be a string")
        tags = raw.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise JinseyError(f"{label}: tags must be a list of nonempty strings")
        test_data = raw.get("test_data")
        try:
            json.dumps(test_data, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as exc:
            raise JinseyError(f"{label}: test_data must be valid JSON data") from exc
        steps = normalize_text(raw["steps"])
        cases.append(TestCase(
            key=key, feature=normalize_text(raw["feature"]), scenario=normalize_text(raw["scenario"]),
            steps="\n".join(f"{i}. {line}" for i, line in enumerate(steps.splitlines(), 1)),
            expected=normalize_text(raw["expected"]), precondition=normalize_text(raw.get("precondition", "")),
            priority=priority, tags=tuple(tag.strip() for tag in tags), test_data=test_data,
            test_type=normalize_text(raw.get("test_type", "")),
            prefix=case_prefix,
        ))
    return prefix, cases
