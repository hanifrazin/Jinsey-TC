"""Stage artifacts beside their destinations; rollback a failed multi-file commit."""
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from filelock import FileLock, Timeout

from jinsey.errors import JinseyError

LOCK_TIMEOUT_SECONDS = 30


@contextmanager
def registry_lock(registry: Path) -> Iterator[None]:
    """Serialize registry readers/writers across concurrent generation processes."""
    registry.parent.mkdir(parents=True, exist_ok=True)
    lock_path = registry.with_suffix(registry.suffix + ".lock")
    lock = FileLock(str(lock_path))
    try:
        lock.acquire(timeout=LOCK_TIMEOUT_SECONDS)
    except Timeout as exc:
        raise JinseyError(f"Registry is busy: {lock_path}; retry after the other generator finishes") from exc
    try:
        yield
    finally:
        lock.release()


@contextmanager
def staged_files(targets: list[Path]) -> Iterator[dict[Path, Path]]:
    resolved = [path.resolve() for path in targets]
    if len(set(resolved)) != len(resolved):
        raise JinseyError("Artifact and registry paths must be distinct")
    workspaces: list[Path] = []
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path | None] = {}
    changed: list[Path] = []
    preserve = False
    try:
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not target.is_file():
                raise JinseyError(f"Destination must be a regular file: {target}")
            workspace = Path(tempfile.mkdtemp(prefix=".jinsey-", dir=target.parent))
            workspaces.append(workspace)
            staged[target] = workspace / target.name
            backup = workspace / "original.bak"
            if target.exists():
                shutil.copy2(target, backup)
                backups[target] = backup
            else:
                backups[target] = None
        yield staged
        # All exporters and verification have succeeded before any destination changes.
        for target in targets:
            with staged[target].open("rb") as handle:
                os.fsync(handle.fileno())
        for target in targets:
            os.replace(staged[target], target)
            changed.append(target)
    except BaseException as original:
        failures = []
        for target in reversed(changed):
            try:
                backup = backups[target]
                if backup is None:
                    target.unlink(missing_ok=True)
                else:
                    os.replace(backup, target)
            except OSError as exc:
                failures.append(f"{target}: {exc}")
        if failures:
            preserve = True
            raise JinseyError(
                f"Commit failed ({original}); rollback needs recovery: {'; '.join(failures)}. "
                f"Backups retained in {', '.join(map(str, workspaces))}"
            ) from original
        raise
    finally:
        if not preserve:
            for workspace in workspaces:
                shutil.rmtree(workspace)
