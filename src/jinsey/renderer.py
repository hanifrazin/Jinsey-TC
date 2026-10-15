"""Render authoring templates to a JSON envelope; no export concerns here."""
import json
from pathlib import Path
from typing import Any

from jinja2 import FileSystemLoader, StrictUndefined, TemplateError
from jinja2.loaders import split_template_path
from jinja2.sandbox import SandboxedEnvironment, SecurityError

from jinsey.errors import JinseyError
from jinsey.parsing import strict_json_loads

MAX_TEMPLATE_BYTES = 4 * 1024 * 1024
MAX_RENDERED_CHARACTERS = 32 * 1024 * 1024


class TemplateLoader(FileSystemLoader):
    def __init__(self, root: Path, sources: set[Path]):
        super().__init__(str(root))
        self.root = root
        self.sources = sources

    def get_source(self, environment: SandboxedEnvironment, template: str) -> tuple:
        target = self.root.joinpath(*split_template_path(template)).resolve()
        if not target.is_relative_to(self.root):
            raise SecurityError(f"Template import escapes template directory: {template}")
        if target.is_file() and target.stat().st_size > MAX_TEMPLATE_BYTES:
            raise SecurityError(f"Template source exceeds {MAX_TEMPLATE_BYTES} bytes: {template}")
        source, filename, uptodate = super().get_source(environment, template)
        self.sources.add(Path(filename).resolve())
        return source, filename, uptodate


def render_template(path: Path, context: dict[str, Any] | None = None,
                    sources: set[Path] | None = None) -> dict:
    # Data-only context avoids exposing Python objects with side-effecting methods.
    try:
        safe_context = strict_json_loads(json.dumps(context or {}, allow_nan=False))
        if not isinstance(safe_context, dict):
            raise ValueError("context must be a JSON object")
    except (ValueError, TypeError, RecursionError) as exc:
        raise JinseyError(f"Template context must contain JSON data only: {exc}") from exc
    resolved = path.resolve()
    env = SandboxedEnvironment(
        loader=TemplateLoader(resolved.parent, sources if sources is not None else set()),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    try:
        chunks = []
        size = 0
        for chunk in env.get_template(resolved.name).generate(**safe_context):
            size += len(chunk)
            if size > MAX_RENDERED_CHARACTERS:
                raise JinseyError(f"Template {path}: rendered output exceeds {MAX_RENDERED_CHARACTERS} characters")
            chunks.append(chunk)
        rendered = "".join(chunks)
    except (TemplateError, ValueError, TypeError, ArithmeticError, RecursionError) as exc:
        raise JinseyError(f"Template {path}: {exc}") from exc
    try:
        envelope = strict_json_loads(rendered)
    except json.JSONDecodeError as exc:
        raise JinseyError(f"Rendered JSON from {path}, line {exc.lineno}: {exc.msg}") from exc
    except (ValueError, RecursionError) as exc:
        raise JinseyError(f"Rendered JSON from {path}: {exc}") from exc
    if not isinstance(envelope, dict):
        raise JinseyError("Rendered JSON must be an object with a test_cases list")
    return envelope
