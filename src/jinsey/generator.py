"""Orchestrate pure processing and transactional local output."""
from dataclasses import dataclass, replace
from pathlib import Path

from jinsey.collection import load_collection
from jinsey.errors import JinseyError
from jinsey.exporters.excel_exporter import export_excel, export_excel_sheets
from jinsey.exporters.yaml_exporter import export_yaml, export_yaml_sheets
from jinsey.id_registry import IDRegistry
from jinsey.schema import CaseSheet, TestCase, load_fields
from jinsey.transaction import registry_lock, staged_files
from jinsey.verification import (
    verify_excel,
    verify_excel_sheets,
    verify_yaml,
    verify_yaml_sheets,
)


@dataclass(frozen=True)
class GenerationResult:
    cases: list[TestCase]
    artifacts: list[Path]
    retired_keys: list[str]
    sheets: list[CaseSheet]


def validate(template: Path, field_config: Path, prefix: str | None = None) -> tuple[str, list[TestCase]]:
    default_prefix, sheets = load_collection(template, load_fields(field_config), prefix)
    return default_prefix, [case for sheet in sheets for case in sheet.cases]


def generate(template: Path, field_config: Path, output: Path, registry_path: Path,
             format: str = "all", prefix: str | None = None, dry_run: bool = False) -> GenerationResult:
    if format not in {"all", "yaml", "excel"}:
        raise JinseyError(f"Unsupported format {format!r}; choose all, yaml, excel")
    # Resolve before locking so aliases of the registry share a lock and state file.
    registry_path = registry_path.resolve()
    fields = load_fields(field_config)
    protected = {field_config.resolve()}
    _, sheet_inputs = load_collection(template, fields, prefix, protected)
    normalized = [case for sheet in sheet_inputs for case in sheet.cases]
    directory = template.is_dir()
    artifacts = []
    if format in {"all", "yaml"}:
        artifacts.append(output / "testcases.yaml")
    if format in {"all", "excel"}:
        artifacts.append(output / "testcases.xlsx")
    lock_path = registry_path.with_suffix(registry_path.suffix + ".lock")
    if any(path.resolve() in protected for path in [*artifacts, registry_path, lock_path]):
        raise JinseyError("Output/registry/lock paths must not overwrite template sources or field configuration")

    def run() -> GenerationResult:
        registry = IDRegistry(registry_path)
        groups: dict[str, list[TestCase]] = {}
        for case in normalized:
            groups.setdefault(case.prefix, []).append(case)
        by_key: dict[str, TestCase] = {}
        retired = []
        for scope, group in groups.items():
            assigned, absent = registry.assign(scope, group)
            by_key.update((case.key, case) for case in assigned)
            retired.extend(f"{scope}:{key}" for key in absent)
        # Group only for counter assignment; preserve authored order in both exports.
        cases = [by_key[case.key] for case in normalized]
        sheets = [replace(sheet, cases=[by_key[case.key] for case in sheet.cases]) for sheet in sheet_inputs]
        if dry_run:
            return GenerationResult(cases, artifacts, retired, sheets)
        with staged_files([*artifacts, registry_path]) as staged:
            for target in artifacts:
                if target.suffix == ".yaml":
                    if directory:
                        export_yaml_sheets(sheets, staged[target])
                        verify_yaml_sheets(staged[target], sheets)
                    else:
                        export_yaml(cases, staged[target])
                        verify_yaml(staged[target], cases)
                else:
                    if directory:
                        export_excel_sheets(sheets, staged[target], fields)
                        verify_excel_sheets(staged[target], sheets, fields)
                    else:
                        export_excel(cases, staged[target], fields)
                        verify_excel(staged[target], cases, fields)
            registry.write(staged[registry_path])
        return GenerationResult(cases, artifacts, retired, sheets)

    if dry_run:
        return run()
    with registry_lock(registry_path):
        return run()
