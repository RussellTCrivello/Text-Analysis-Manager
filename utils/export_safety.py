"""Safety helpers for user-controlled spreadsheet exports.

Spreadsheet applications may interpret cell text beginning with ``=``, ``+``,
``-`` or ``@`` as a formula when a CSV/XLSX file is opened.  Research data is
user-controlled, so exports must preserve the visible value without allowing a
crafted record to execute a formula in the recipient's spreadsheet.
"""
from typing import Any, Dict


_FORMULA_PREFIXES = ("=", "+", "-", "@")


def sanitize_spreadsheet_value(value: Any) -> Any:
    """Return a spreadsheet-safe representation of one exported value.

    Non-string values retain their type.  Strings that could be interpreted as
    formulas are prefixed with an apostrophe, which spreadsheet applications
    display as text rather than evaluating.  Leading whitespace is considered
    when detecting a formula because spreadsheet programs commonly trim it.
    """
    if not isinstance(value, str):
        return value

    if value.lstrip().startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def sanitize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize every value in a dictionary row for CSV/XLSX output."""
    return {key: sanitize_spreadsheet_value(value) for key, value in row.items()}
