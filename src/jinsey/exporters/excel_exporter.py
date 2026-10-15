import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from jinsey.columns import COLS, INVALID_XML_TEXT
from jinsey.schema import CaseSheet, ChoiceField, TestCase, validate_sheet_names

MAX_DATA_ROWS = 1_048_575


def cell_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, tuple):
        return ", ".join(value)
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def sheet_dropdowns(cases: list[TestCase]) -> dict[str, tuple[str, ...]]:
    options: dict[str, list[str]] = {}
    spelling: dict[str, str] = {}
    for case in cases:
        for name, spec in case.dropdown.items():
            canonical = spelling.setdefault(name.casefold(), name)
            if canonical != name:
                raise ValueError(f"Dropdown column names must use consistent spelling: {canonical!r}, {name!r}")
            choices = options.setdefault(name, [])
            for option in ([spec] if isinstance(spec, str) else spec["options"]):
                if option not in choices:
                    choices.append(option)
    return {name: tuple(values) for name, values in options.items()}


def sheet_columns(cases: list[TestCase]) -> list[tuple[str, str, int]]:
    return [*COLS, *((name, name, 24) for name in sheet_dropdowns(cases))]


def case_cell_value(case: TestCase, field: str) -> str:
    if field in case.dropdown:
        spec = case.dropdown[field]
        return spec if isinstance(spec, str) else spec["value"]
    return cell_value(getattr(case, field, ""))


def _choice_formula(wb: Workbook, options: tuple[str, ...], name: str) -> str:
    inline = ",".join(options)
    if len(inline) <= 253 and all(not any(c in option for c in ',"\n\r') for option in options):
        return f'"{inline}"'
    if name not in wb.defined_names:
        lookup = wb["_choices"] if "_choices" in wb.sheetnames else wb.create_sheet("_choices")
        column = len(wb.defined_names) + 1
        letter = get_column_letter(column)
        for index, option in enumerate(options, 1):
            lookup.cell(index, column, option).data_type = "s"
        lookup.sheet_state = "hidden"
        wb.defined_names.add(DefinedName(name, attr_text=f"'_choices'!${letter}$1:${letter}${len(options)}"))
    return name


def _populate_sheet(wb: Workbook, ws: Worksheet, cases: list[TestCase], fields: dict[str, ChoiceField]) -> None:
    if len(cases) > MAX_DATA_ROWS:
        raise ValueError(f"Excel supports at most {MAX_DATA_ROWS} test cases plus the header")
    columns = sheet_columns(cases)
    if len(columns) > 16384:
        raise ValueError("Excel supports at most 16384 columns")
    ws.append([header for _, header, _ in columns])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="263D57")
    wrapped = Alignment(wrap_text=True, vertical="top")
    for row_index, case in enumerate(cases, 2):
        values = [case_cell_value(case, field) for field, _, _ in columns]
        # Excel's cell limit must fail explicitly instead of silently truncating content.
        if any(len(value) > 32767 for value in values):
            raise ValueError(f"Test case {case.key}: Excel cells cannot exceed 32767 characters")
        for value, (field, _, _) in zip(values, columns, strict=True):
            if INVALID_XML_TEXT.search(value):
                raise ValueError(f"Test case {case.key}: {field} contains characters forbidden in Excel XML")
        ws.append(values)
        for column in range(1, len(columns) + 1):
            cell = ws.cell(row_index, column)
            cell.data_type = "s"  # Preserve IDs and prevent authored formulas from executing.
            cell.alignment = wrapped
        ws.row_dimensions[row_index].height = min(409, max(45, 15 * max(v.count("\n") + 1 for v in values)))
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for i, (_, _, width) in enumerate(columns, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    headers = {cell.value: cell.column_letter for cell in ws[1]}
    dropdowns = {"Priority": fields["priority"].options, **sheet_dropdowns(cases)}
    for header, options in dropdowns.items():
        name = "PriorityOptions" if header == "Priority" else f"DropdownOptions{wb.index(ws)}_{headers[header]}"
        formula = _choice_formula(wb, options, name)
        validation = DataValidation(type="list", formula1=formula, allow_blank=header != "Priority")
        validation.showDropDown = False
        validation.showErrorMessage = True
        validation.errorStyle = "stop"
        validation.errorTitle = f"Invalid {header}"[:32]
        validation.error = "Choose a value from the dropdown."
        validation.showInputMessage = True
        validation.promptTitle = header[:32]
        validation.prompt = "Select a value from the dropdown."
        ws.add_data_validation(validation)
        validation.add(f"{headers[header]}2:{headers[header]}{max(2, len(cases) + 1)}")


def export_excel_sheets(sheets: list[CaseSheet], path: Path, fields: dict[str, ChoiceField]) -> None:
    validate_sheet_names([sheet.name for sheet in sheets])
    wb = Workbook()
    wb.remove(wb.active)
    try:
        for sheet in sheets:
            ws = wb.create_sheet(sheet.name)
            _populate_sheet(wb, ws, sheet.cases, fields)
        wb.save(path)
    finally:
        wb.close()


def export_excel(cases: list[TestCase], path: Path, fields: dict[str, ChoiceField]) -> None:
    export_excel_sheets([CaseSheet("Test Cases", "", cases)], path, fields)
