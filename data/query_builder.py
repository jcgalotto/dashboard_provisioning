
"""Helpers to construct SQL queries with date filters."""


def build_query(fecha_ini, fecha_fin):
    """Load base SQL and inject formatted dates.

    The base query contains the placeholders ``:fecha_ini`` and
    ``:fecha_fin``. This function replaces those placeholders with Oracle
    ``TO_DATE`` expressions formatted as ``YYYY-MM-DD HH24:MI:SS``.
    """

    with open("sql/base_query.sql", "r", encoding="utf-8") as f:
        query = f.read()

    fecha_ini_str = fecha_ini.strftime("%Y-%m-%d %H:%M:%S")
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d %H:%M:%S")

    query = query.replace(
        ":fecha_ini",
        f"TO_DATE('{fecha_ini_str}', 'YYYY-MM-DD HH24:MI:SS')",
    )
    query = query.replace(
        ":fecha_fin",
        f"TO_DATE('{fecha_fin_str}', 'YYYY-MM-DD HH24:MI:SS')",
    )

    return query
