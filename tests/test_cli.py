import json
import subprocess
import sys

import pytest

from jinsey.cli import main


def options(root, tmp_path, template):
    return ["--template", str(template), "--fields", str(root / "config/fields.yaml")]


def test_validate_cli(root, tmp_path, template, capsys):
    assert main(["validate", *options(root, tmp_path, template)]) == 0
    assert "Valid: 1" in capsys.readouterr().out


def test_generate_cli_and_retired_warning(root, tmp_path, template, raw_case, capsys):
    args = ["generate", *options(root, tmp_path, template), "--output-dir", str(tmp_path / "out"),
            "--registry", str(tmp_path / "ids.json")]
    assert main(args) == 0
    assert "Generated and verified 1" in capsys.readouterr().out
    raw_case["key"] = "new-key"
    template.write_text(json.dumps({"test_cases": [raw_case]}))
    assert main(args) == 0
    assert "absent keys" in capsys.readouterr().err
    assert main([*args, "--dry-run"]) == 0
    assert "TC-002: new-key" in capsys.readouterr().out


def test_cli_error(root, tmp_path, template, capsys):
    assert main(["validate", *options(root, tmp_path, template), "--prefix", "bad"]) == 1
    assert "Invalid prefix" in capsys.readouterr().err


def test_bad_arguments():
    with pytest.raises(SystemExit) as exc:
        main(["generate", "--format", "csv"])
    assert exc.value.code == 2


def test_module_invocation(root):
    result = subprocess.run([sys.executable, "-m", "jinsey.cli", "validate"], cwd=root, text=True, capture_output=True)
    assert result.returncode == 0 and "Valid: 10" in result.stdout
