import json
from pathlib import Path

import pytest

from jinsey.schema import load_fields

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root():
    return ROOT


@pytest.fixture
def fields():
    return load_fields(ROOT / "config/fields.yaml")


@pytest.fixture
def raw_case():
    return {"key": "fictional-login", "feature": "Login", "scenario": "Login fiktif",
            "steps": "\n Buka Login \n\n Klik Login\n", "expected": "Berhasil\nHalaman utama"}


@pytest.fixture
def template(tmp_path, raw_case):
    path = tmp_path / "cases.j2"
    path.write_text(json.dumps({"test_cases": [raw_case]}), encoding="utf-8")
    return path
