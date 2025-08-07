
"""Helpers to construct SQL queries with optional filters."""

DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
ORACLE_DATE_FORMAT = "DD-MM-YYYY HH24:MI:SS"


def build_query(fecha_ini, fecha_fin=None, ne_id=None, actions=None):
    """Load base SQL and inject formatted filters.

    The base query contains the placeholders ``:fecha_ini`` and
    ``:fecha_fin``. This function replaces those placeholders with Oracle
    ``TO_DATE`` expressions formatted as ``DD-MM-YYYY HH24:MI:SS``. If
    ``fecha_fin`` is not provided, the ``:fecha_fin`` placeholder is
    replaced with ``SYSDATE``. When ``ne_id`` or a list of ``actions`` are
    provided, respective ``AND`` clauses are appended using the ``:ne_id``
    and ``:action`` placeholders defined in ``sql/base_query.sql``.
    """

    with open("sql/base_query.sql", "r", encoding="utf-8") as f:
        query = f.read()

    fecha_ini_str = fecha_ini.strftime(DATE_FORMAT)
    query = query.replace(
        ":fecha_ini",
        f"TO_DATE('{fecha_ini_str}', '{ORACLE_DATE_FORMAT}')",
    )

    if fecha_fin:
        fecha_fin_str = fecha_fin.strftime(DATE_FORMAT)
        query = query.replace(
            ":fecha_fin",
            f"TO_DATE('{fecha_fin_str}', '{ORACLE_DATE_FORMAT}')",
        )
    else:
        query = query.replace(":fecha_fin", "SYSDATE")

    if ne_id:
        query = query.replace(
            ":ne_id",
            f"AND a.pri_ne_id = '{ne_id}'",
        )
    else:
        query = query.replace(":ne_id", "")

    if actions:
        formatted_actions = "', '".join(actions)
        query = query.replace(
            ":action",
            f"AND a.pri_action IN ('{formatted_actions}')",
        )
    else:
        query = query.replace(":action", "")

    return query
