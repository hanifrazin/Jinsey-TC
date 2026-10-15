"""Shared spreadsheet column names and XML text constraints."""
import re

COLS = [("id", "ID", 16), ("key", "Key", 32), ("feature", "Feature", 16),
        ("scenario", "Scenario", 48), ("precondition", "Preconditions", 45),
        ("steps", "Steps", 60), ("expected", "Expected Result", 55),
        ("priority", "Priority", 14), ("tags", "Tags", 25),
        ("test_data", "Test Data", 40), ("test_type", "Test Type", 20)]

INVALID_XML_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
