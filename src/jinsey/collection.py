"""Load one template or direct child templates as an ordered sheet collection."""
from pathlib import Path

from jinsey.errors import JinseyError
from jinsey.processor import normalize
from jinsey.renderer import render_template
from jinsey.schema import CaseSheet, ChoiceField, validate_sheet_names


def load_collection(path: Path, fields: dict[str, ChoiceField], prefix: str | None = None,
                    sources: set[Path] | None = None) -> tuple[str, list[CaseSheet]]:
    directory = path.is_dir()
    if directory:
        files = sorted((child for child in path.iterdir() if child.is_file()
                        and child.suffix.lower() == ".j2" and not child.name.startswith(".")),
                       key=lambda item: (item.name.casefold(), item.name))
        if not files:
            raise JinseyError(f"No .j2 files directly inside {path}; put helpers in a shared/ subfolder")
        for file in files:
            if not file.resolve().is_relative_to(path.resolve()):
                raise JinseyError(f"Template {file} resolves outside input directory")
        validate_sheet_names([file.stem for file in files])
    else:
        files = [path]
    seen: dict[str, Path] = {}
    sheets = []
    default_prefix = "TC"
    for file in files:
        try:
            default_prefix, cases = normalize(render_template(file, sources=sources), fields, prefix)
        except JinseyError as exc:
            raise JinseyError(f"{file}: {exc}") from exc
        for case in cases:
            if case.key in seen:
                raise JinseyError(f"Duplicate key {case.key!r} in {seen[case.key]} and {file}; keys must be unique across the folder")
            seen[case.key] = file
        sheets.append(CaseSheet(file.stem if directory else "Test Cases", file.name, cases))
    return default_prefix, sheets
