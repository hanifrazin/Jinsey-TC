import os
import subprocess
import sys

import pytest
from filelock import FileLock

from jinsey.errors import JinseyError
from jinsey.transaction import registry_lock, staged_files


def test_registry_lock_excludes_another_process(tmp_path):
    registry = tmp_path / "state/ids.json"
    lock_path = registry.with_suffix(".json.lock")
    script = """
import sys
from filelock import FileLock, Timeout
try:
    with FileLock(sys.argv[1], timeout=0):
        pass
except Timeout:
    sys.exit(23)
"""
    with registry_lock(registry):
        blocked = subprocess.run([sys.executable, "-c", script, str(lock_path)], timeout=10)
        assert blocked.returncode == 23
    released = subprocess.run([sys.executable, "-c", script, str(lock_path)], timeout=10)
    assert released.returncode == 0
    assert not registry.exists()


def test_registry_lock_released_after_failure(tmp_path):
    registry = tmp_path / "ids.json"
    with pytest.raises(ValueError):
        with registry_lock(registry):
            raise ValueError("generation failed")
    with FileLock(str(registry.with_suffix(".json.lock")), timeout=0):
        pass


def test_busy_registry_has_actionable_timeout(tmp_path, monkeypatch):
    registry = tmp_path / "ids.json"
    monkeypatch.setattr("jinsey.transaction.LOCK_TIMEOUT_SECONDS", 0)
    with FileLock(str(registry.with_suffix(".json.lock"))):
        with pytest.raises(JinseyError, match="Registry is busy.*retry"):
            with registry_lock(registry):
                pytest.fail("Busy lock was acquired")


@pytest.mark.parametrize("existing", [True, False])
def test_rollback_on_partial_commit(tmp_path, monkeypatch, existing):
    a, b = tmp_path / "a.yaml", tmp_path / "registry.json"
    if existing:
        a.write_text("old a")
        b.write_text("old b")
    real_replace = os.replace
    calls = 0

    def fail_second(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated registry commit failure")
        return real_replace(source, target)

    monkeypatch.setattr("jinsey.transaction.os.replace", fail_second)
    with pytest.raises(OSError, match="simulated"):
        with staged_files([a, b]) as staged:
            staged[a].write_text("new a")
            staged[b].write_text("new b")
    if existing:
        assert a.read_text() == "old a" and b.read_text() == "old b"
    else:
        assert not a.exists() and not b.exists()
    assert not list(tmp_path.glob(".jinsey-*"))


def test_retains_backups_when_rollback_fails(tmp_path, monkeypatch):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_text("old")
    real_replace = os.replace
    calls = 0

    def fail(source, target):
        nonlocal calls
        calls += 1
        if calls >= 2:
            raise OSError("simulated disk failure")
        return real_replace(source, target)

    monkeypatch.setattr("jinsey.transaction.os.replace", fail)
    with pytest.raises(JinseyError, match="Backups retained"):
        with staged_files([a, b]) as staged:
            staged[a].write_text("new")
            staged[b].write_text("new")
    assert next(tmp_path.glob(".jinsey-*/original.bak")).read_text() == "old"


def test_bad_destinations(tmp_path):
    with pytest.raises(JinseyError, match="distinct"):
        with staged_files([tmp_path / "a", tmp_path / "a"]):
            pass
    with pytest.raises(JinseyError, match="regular file"):
        with staged_files([tmp_path]):
            pass


def test_staging_failure_leaves_original(tmp_path):
    path = tmp_path / "a"
    path.write_text("original")
    with pytest.raises(ValueError):
        with staged_files([path]) as staged:
            staged[path].write_text("new")
            raise ValueError("failed export")
    assert path.read_text() == "original"
