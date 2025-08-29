"""Utility helpers for the dashboard project."""

import re
from datetime import date, datetime
from numbers import Real
from typing import Any, Dict

import pandas as pd


def normalize_error_message(message):
    """Return a generic error message without variable identifiers.

    Many error messages include dynamic information such as user IDs or
    other numbers. To group errors effectively we strip any digits and
    collapse extra whitespace so that messages differing only by those
    identifiers map to the same generic text.

    Parameters
    ----------
    message: str or any
        Original error message. Non-string values are returned as-is.

    Returns
    -------
    str or any
        Normalized error message with digits removed and consecutive
        whitespace collapsed. Non-string inputs are returned unchanged.
    """

    if not isinstance(message, str):
        return message

    # Remove any sequence of digits and collapse multiple spaces
    normalized = re.sub(r"\d+", "", message)
    normalized = " ".join(normalized.split())
    return normalized


def _to_oracle_to_date(value: datetime) -> str:
    """Format a datetime-like value into an Oracle ``TO_DATE`` call."""

    if not isinstance(value, (datetime, date, pd.Timestamp)):
        raise TypeError("value must be a date or datetime")

    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())

    return "TO_DATE('{}', 'DD-MM-YYYY HH24:MI:SS')".format(
        value.strftime("%d-%m-%Y %H:%M:%S")
    )


def _format_sql_value(value: Any) -> str:
    """Return a SQL literal for ``value`` following project conventions."""

    if pd.isna(value):
        return "NULL"

    if isinstance(value, (datetime, date, pd.Timestamp)):
        return _to_oracle_to_date(pd.to_datetime(value))

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.upper().startswith("TO_DATE("):
            return stripped

        if re.match(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$", stripped):
            try:
                parsed = pd.to_datetime(stripped)
            except ValueError:
                pass
            else:
                return _to_oracle_to_date(parsed)

        return "'" + stripped.replace("'", "''") + "'"

    if isinstance(value, Real):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    return "'" + str(value).replace("'", "''") + "'"


def generar_insert(row: Dict[str, Any], tabla: str = "swp_provisioning_interfaces") -> str:
    """Build an ``INSERT`` statement for ``tabla`` from ``row`` data."""

    columnas = ", ".join(row.keys())
    valores = []
    for col, valor in row.items():
        if col.lower() == "pri_id":
            valores.append(
                f"(SELECT NVL(MAX(pri_id), 0) + 1 FROM {tabla})"
            )
        else:
            if col.lower() == "pri_request" and isinstance(valor, str):
                valor = valor.replace("\n", "").replace("\r", "")
            valores.append(_format_sql_value(valor))

    return f"INSERT INTO {tabla} ({columnas}) VALUES ({', '.join(valores)});"

