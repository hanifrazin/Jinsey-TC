---
name: jinsey
description: Build and maintain Jinsey, a Python-powered Jinja2 test case authoring and export tool. Use when implementing test case templates, reusable steps, deterministic IDs, validation, YAML/Excel export, or Google Sheets integration.
---

# Jinsey — Jinja to Test Cases using Python

## Role and objective
Act as the lead Python engineer and QA tooling architect for **Jinsey**. Build a maintainable, local-first test case generator where users author test cases in Jinja2, then produce **one YAML file and one Excel workbook** per generation run. Google Sheets synchronization is an optional, separately configured adapter.

This is a **test case authoring/export tool**, not a test runner or a full test management system. Keep the initial domain strictly fictional: **Login, Register, Logout**. Never import, reference, alter, or infer test cases, endpoints, identifiers, or business rules from any past employer or workplace.

## Non-negotiable design rules
1. Keep concerns separated: **authoring templates → render → parse → validate/normalize → assign stable IDs → export**. Never embed spreadsheet code in Jinja2.
2. Users may define **1–N test cases in one `.j2` file**, with unique internal `key` values; one rendering produces a list of structured test case objects.
3. Preserve ergonomic multiline authoring:
   ```jinja2
   {% set steps %}
   Buka halaman Login
   Masukkan email valid
   Klik Login
   {% endset %}
   ```
   No manual `\n`, JSON quoting, or step numbers required in authored steps.
4. Test cases may have different numbers of steps, different expected results, test data, preconditions, tags, priorities, and test types. Do not force a shared workflow on unrelated cases.
5. Reuse via Jinja2 `macro` or `include` for common steps and preconditions; use `for`/`if` for data-driven cases. Keep reusable fragments **unnumbered**. When concatenating fragments, ensure a newline boundary; strip blank-only lines before numbering.
6. Separate the **stable identity** (`key`, authored by user) from the **display ID** (`TC-001`, generated). Default prefix: `TC`; user can configure another prefix. Numbering starts at 001 with minimum width 3 and can exceed 999.
7. ID assignment must be **persistent across runs**, independent of ordering and changes to scenario titles. Use an ID registry keyed by stable `key` (scope by prefix if needed). Never silently reuse retired IDs or overwrite an existing mapping. Detect duplicate keys, invalid prefixes, and malformed registries. Only commit registry changes after validation and successful output generation; write atomically.
8. Produce `output/testcases.yaml` and `output/testcases.xlsx` from the **same normalized collection**, in the same run and order. Preserve IDs as strings (leading zeros intact).
9. Preserve newlines in Excel cells with wrap text and a readable column layout. Each test case occupies **one row**, with `Steps`, `Preconditions`, and `Expected Result` multiline within their cells. Freeze header row, use filters and sensible widths.
10. Excel dropdowns are implemented by the **Excel exporter**, not by Jinja2. Definitions reside in a single field configuration shared by validation/export. Initial `Priority` options: `P0`, `P1`, `P2`, default `P2`; add other fields only when required. Prevent invalid authored values before writing output. `openpyxl` DataValidation should include an error prompt; Excel client behavior may vary.
11. Optional Google Sheets adapter must use the same normalized data and choice definitions via Google Sheets API, update by stable ID/key mapping (not row position), preserve manual execution statuses/evidence in dedicated columns or tabs, avoid destructive full-sheet overwrites, and require explicit sync invocation. Never include secrets or credentials in source control.
12. Prefer **Python + uv**, with reproducible `pyproject.toml` and `uv.lock`. Commands should work without manually activating a virtual environment.
13. Fail with specific, actionable messages for template syntax errors, missing required fields, duplicate keys, malformed YAML/JSON, and invalid dropdown values. Do not silently fabricate business expectations.
14. Add unit tests for core processing and a small end-to-end fixture. Keep code readable, type-hinted and modular; avoid premature web UI/database complexity.

## Recommended repository structure
```text
jinsey/
├── SKILL.md
├── pyproject.toml
├── uv.lock
├── config/
│   └── fields.yaml
├── templates/
│   ├── testcases.j2
│   └── shared/
│       ├── login_steps.j2
│       └── preconditions.j2
├── src/jinsey/
│   ├── cli.py
│   ├── renderer.py
│   ├── schema.py
│   ├── processor.py
│   ├── id_registry.py
│   └── exporters/
│       ├── yaml_exporter.py
│       ├── excel_exporter.py
│       └── google_sheets_exporter.py  # optional; don't require for local runs
├── tests/
└── output/                         # generated artifacts
```

## Data contract
A rendered `.j2` file must yield JSON compatible with this envelope. Python validates and converts it to the normalized schema (then exports YAML):
```json
{
  "prefix": "TC",
  "test_cases": [
    {
      "key": "login-valid-credentials",
      "feature": "Login",
      "scenario": "Memastikan login berhasil dengan kredensial valid",
      "precondition": "Akun terdaftar dan aktif",
      "steps": "Buka halaman Login\nMasukkan email valid\nMasukkan password valid\nKlik Login",
      "expected": "Pengguna berhasil masuk ke halaman utama",
      "priority": "P1",
      "tags": ["smoke", "positive"]
    }
  ]
}
```
Required fields: `key`, `feature`, `scenario`, `steps`, `expected`. Optional: `precondition`, `priority`, `tags`, `test_data`, `test_type`. The Python processor owns generated `id`; reject user-provided conflicting display IDs. Keep `steps`/`expected` strings multiline by default; do not infer that expected outcomes correspond one-to-one to steps. Normalize whitespace without erasing intentional line breaks. Use strict Jinja undefined-variable behavior (`StrictUndefined`) for early feedback.

## Example authoring: multiple cases with different steps
`templates/shared/login_steps.j2`:
```jinja2
{% macro open_login() -%}
Buka halaman Login
Pastikan formulir login ditampilkan
{%- endmacro %}
```

`templates/testcases.j2` (single rendered JSON envelope; this is a working pattern):
```jinja2
{% import "shared/login_steps.j2" as login %}
{% set ns = namespace(cases=[]) %}

{% set steps %}
{{ login.open_login() | trim }}
Masukkan email valid
Masukkan password valid
Klik tombol Login
{% endset %}
{% set expected %}
Pengguna berhasil masuk
Halaman utama ditampilkan
{% endset %}
{% set _ = ns.cases.append({
  "key": "login-success",
  "feature": "Login",
  "scenario": "Memastikan login berhasil",
  "precondition": "Akun sudah terdaftar dan aktif",
  "steps": steps | trim,
  "expected": expected | trim,
  "priority": "P1"
}) %}

{% set steps %}
Buka halaman Register
Masukkan email berformat tidak valid
Isi field wajib lainnya
Klik tombol Register
{% endset %}
{% set _ = ns.cases.append({
  "key": "register-invalid-email",
  "feature": "Register",
  "scenario": "Memastikan validasi email tidak valid",
  "steps": steps | trim,
  "expected": "Pesan validasi email ditampilkan",
  "priority": "P2"
}) %}

{{ {"prefix": "TC", "test_cases": ns.cases} | tojson }}
```
For many similar scenarios, assemble `ns.cases` via loops. For substantially different cases, use separate multiline `set` blocks in the same file. Shared blocks may be imported and reused selectively.

## Field configuration
`config/fields.yaml`:
```yaml
fields:
  priority:
    type: select
    options: [P0, P1, P2]
    default: P2
    required: true
```
Read choice constraints here rather than duplicating in the template and spreadsheet exporter. Provide dropdowns for the actual Priority column by header lookup, not hard-coded column letters. The exporter may use an inline list formula for short options; for long lists use a hidden lookup sheet and named ranges.

## CLI contract
Support (or implement incrementally with tests):
```bash
uv sync
uv run jinsey generate --template templates/testcases.j2 --format all
uv run jinsey generate --format yaml
uv run jinsey generate --format excel
uv run jinsey validate --template templates/testcases.j2
```
Defaults: template=`templates/testcases.j2`, format=`all`, output directory=`output/`, prefix=`TC` when absent. A CLI prefix override should take precedence when explicitly provided. `validate` must not modify ID registries or outputs. `generate` must report counts, artifact paths, and validation errors.

## ID registry and export safety
Store `.id_registry.json` in a documented persistent location (not a disposable temp directory). Give each test case a stable internal `key`; never derive registry identity solely from scenario title or file position. When generating, preview new IDs in memory and validate all objects first. Write temp YAML/XLSX artifacts, then atomically replace generated outputs and persist the registry only when all operations succeed; account for multi-file commit failure with backup/rollback or an equivalent recoverable design. Support a dry-run mode if practical. Warn if a key disappears from templates; do not recycle its ID automatically. Ensure successive runs are idempotent.

## Acceptance criteria
- One `.j2` file can contain 10 different Login/Register/Logout test cases with different step counts.
- First five Login cases can share initial steps while having different subsequent steps; other cases may use unrelated steps.
- Shared preconditions are reused where relevant, without coupling unrelated cases.
- No ID specified → `TC-001` onward; user prefix `AUTH` → `AUTH-001` onward.
- Inserting or reordering cases does not change previously assigned IDs for stable keys.
- Generated YAML has valid, multiline test steps and expected results.
- Generated `.xlsx` has 10 rows of test cases, formatted multiline cells, and a working Priority validation dropdown `P0/P1/P2`.
- Editing Jinja2 steps changes both output formats consistently without edits to exporters.
- Bad priority, duplicate key, missing required field, or invalid Jinja2 fails with a helpful error.
- `uv run jinsey ...` runs without users activating `.venv` manually.
- No real employer/workplace-specific content appears in fixtures, examples, or docs.

## Implementation approach for coding agents
Inspect existing files before modifying; preserve working functionality. Implement the smallest coherent slice, run tests, and verify output files rather than claiming success from code alone. Favor a simple, functional CLI over speculative integrations. Document new options and behavior in README. Do not add Google Sheets as a blocking dependency for local Excel/YAML generation. Never claim a sync or run succeeded without actual execution evidence.
