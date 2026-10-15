"""Command line interface; invoke through uv run jinsey."""
import argparse
import sys
from pathlib import Path

from jinsey.errors import JinseyError
from jinsey.generator import generate, validate


def resolve_template(value: str) -> Path:
    """Resolve files/folders; bare names select data/input, explicit paths win."""
    path = Path(value)
    if path.name == value:
        path = Path("data/input") / path
    elif (not path.exists() and not path.is_absolute()
          and not value.startswith(("./", "../", ".\\", "..\\"))):
        candidate = Path("data/input") / path
        if candidate.exists():
            path = candidate
    if not (path.is_file() or path.is_dir()):
        raise JinseyError(
            f"Template not found: {path}. Put the file in data/input/ "
            "and use --template filename.j2, or supply an explicit path."
        )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jinsey", description="Render fictional test cases from Jinja2")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "validate"):
        command = commands.add_parser(name)
        inputs = command.add_mutually_exclusive_group()
        inputs.add_argument("--template", default="testcases.j2",
                            help="File/folder in data/input/ or explicit path (default: testcases.j2)")
        inputs.add_argument("--input-dir", help="Folder of .j2 files: one worksheet per file")
        command.add_argument("--fields", type=Path, default=Path("config/fields.yaml"))
        command.add_argument("--prefix", help="Override every case/file prefix, e.g. AUTH")
        if name == "generate":
            command.add_argument("--format", choices=("all", "yaml", "excel"), default="all")
            command.add_argument("--output-dir", type=Path,
                                 help="Destination (default: data/output/<file stem or folder name>/)")
            command.add_argument("--registry", type=Path, default=Path(".id_registry.json"))
            command.add_argument("--dry-run", action="store_true", help="Preview IDs without writing files")
    args = parser.parse_args(argv)
    try:
        template = resolve_template(args.input_dir if args.input_dir is not None else args.template)
        if args.input_dir is not None and not template.is_dir():
            raise JinseyError(f"--input-dir must refer to a folder: {template}")
        directory = template.is_dir()
        print(f"{'Input directory' if directory else 'Template'}: {template}")
        if args.command == "validate":
            _, cases = validate(template, args.fields, args.prefix)
            prefixes = ", ".join(dict.fromkeys(case.prefix for case in cases))
            print(f"Valid: {len(cases)} test cases; prefix {prefixes}. No files modified.")
        else:
            output_name = template.name if directory else template.stem
            output = args.output_dir if args.output_dir is not None else Path("data/output") / output_name
            result = generate(template, args.fields, output, args.registry,
                              args.format, args.prefix, args.dry_run)
            if result.retired_keys:
                print("Warning: absent keys retained in registry: " + ", ".join(result.retired_keys), file=sys.stderr)
            if directory:
                print("Sheets: " + ", ".join(f"{sheet.name} ({len(sheet.cases)} TC)" for sheet in result.sheets))
            if args.dry_run:
                print(f"Dry run: {len(result.cases)} test cases. No files modified.")
                print(f"Planned output directory: {output}")
                for case in result.cases:
                    print(f"{case.id}: {case.key}")
            else:
                print(f"Generated and verified {len(result.cases)} test cases:")
                for artifact in result.artifacts:
                    print(artifact)
                print(f"ID registry: {args.registry}")
        return 0
    except (JinseyError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
