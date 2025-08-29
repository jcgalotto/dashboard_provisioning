"""Utility functions for SQL generation."""

import re
from datetime import date, datetime
from numbers import Real
from typing import Any, Dict, Union

import pandas as pd


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
        s = value.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        s = re.sub(r"\s+", " ", s).strip()
        if s.upper().startswith("TO_DATE("):
            return s

        if re.match(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$", s):
            try:
                parsed = pd.to_datetime(s)
            except ValueError:
                pass
            else:
                return _to_oracle_to_date(parsed)

        return "'" + s.replace("'", "''") + "'"

    if isinstance(value, Real):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    return "'" + str(value).replace("'", "''") + "'"


def generar_insert(
    tabla_or_row: Union[str, Dict[str, Any]],
    row: Dict[str, Any] | None = None,
) -> str:
    """Build an ``INSERT`` statement.

    Call ``generar_insert(row)`` to use the default table
    ``swp_provisioning_interfaces`` or ``generar_insert(tabla, row)`` to
    specify a custom table name.
    """

    if row is None:
        row = tabla_or_row  # type: ignore[assignment]
        tabla = "swp_provisioning_interfaces"
    else:
        tabla = tabla_or_row  # type: ignore[assignment]

    columnas = ", ".join(row.keys())
    valores = []
    for col, valor in row.items():
        if col.lower() == "pri_id":
            valores.append(
                f"(SELECT NVL(MAX(pri_id), 0) + 1 FROM {tabla})"
            )
        else:
            valores.append(_format_sql_value(valor))

    return f"INSERT INTO {tabla} ({columnas}) VALUES ({', '.join(valores)});"

