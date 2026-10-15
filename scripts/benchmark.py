"""Repeatable synthetic timings; uses temporary output and never touches user IDs."""
import argparse
import json
import platform
import statistics
import tempfile
from pathlib import Path
from time import perf_counter

from jinsey.exporters.excel_exporter import export_excel
from jinsey.generator import generate
from jinsey.processor import normalize
from jinsey.schema import load_fields


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[10, 1000, 3000])
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    if args.repeat < 1 or any(size < 1 for size in args.sizes):
        parser.error("sizes and repeat must be positive integers")
    config = Path(__file__).resolve().parents[1] / "config/fields.yaml"
    fields = load_fields(config)
    results = []
    with tempfile.TemporaryDirectory(prefix="jinsey-benchmark-") as scratch:
        work = Path(scratch)
        for size in args.sizes:
            raw = [{"key": f"fictional-{i}", "feature": "Login", "scenario": "Fictional scenario",
                    "steps": "Open Login\nClick Login", "expected": "Expected fictional result"}
                   for i in range(size)]
            envelope = {"test_cases": raw}
            template = work / "benchmark.j2"
            template.write_text(json.dumps(envelope), encoding="utf-8")
            normalized = normalize(envelope, fields)[1]
            cases = [case.with_id(f"TC-{i:03d}") for i, case in enumerate(normalized, 1)]
            excel_times, full_times = [], []
            for repeat in range(args.repeat):
                started = perf_counter()
                export_excel(cases, work / "export.xlsx", fields)
                excel_times.append(perf_counter() - started)
                started = perf_counter()
                generate(template, config, work / "out", work / f"registry-{size}-{repeat}.json")
                full_times.append(perf_counter() - started)
            results.append({"cases": size,
                            "excel_export_median_seconds": round(statistics.median(excel_times), 4),
                            "full_pipeline_median_seconds": round(statistics.median(full_times), 4)})
    print(json.dumps({"os": platform.system(), "python": platform.python_version(),
                      "repeats": args.repeat, "results": results}, indent=2))


if __name__ == "__main__":
    main()
