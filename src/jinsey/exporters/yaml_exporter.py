from pathlib import Path

import yaml

from jinsey.schema import CaseSheet, TestCase


class MultilineDumper(yaml.SafeDumper):
    pass


def _string(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|" if "\n" in value else None)


MultilineDumper.add_representer(str, _string)


def export_yaml(cases: list[TestCase], path: Path) -> None:
    path.write_text(yaml.dump({"test_cases": [case.to_dict() for case in cases]},
                             Dumper=MultilineDumper, allow_unicode=True, sort_keys=False), encoding="utf-8")


def export_yaml_sheets(sheets: list[CaseSheet], path: Path) -> None:
    path.write_text(yaml.dump({"sheets": [sheet.to_dict() for sheet in sheets]},
                             Dumper=MultilineDumper, allow_unicode=True, sort_keys=False), encoding="utf-8")
