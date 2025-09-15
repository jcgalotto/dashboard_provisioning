from typing import Any, Dict, List, Optional

try:
    import oracledb as cx_Oracle  # thin mode
except Exception:  # pragma: no cover
    import cx_Oracle  # type: ignore

from ..core.config import get_settings

settings = get_settings()

try:  # pragma: no cover - no client in tests
    pool: cx_Oracle.SessionPool | None = cx_Oracle.SessionPool(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=settings.ORACLE_DSN,
        min=settings.ORACLE_POOL_MIN,
        max=settings.ORACLE_POOL_MAX,
        increment=1,
        threaded=True,
        getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT,
    )
except Exception:  # pragma: no cover
    pool = None


def _execute(query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    if pool is None:
        return []
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [c[0].lower() for c in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_all(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Dict[str, Any]]:
    params = params or {}
    if limit is not None or offset is not None:
        try:
            paginated = f"{query} OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
            params = {**params, "offset": offset or 0, "limit": limit or 0}
            return _execute(paginated, params)
        except Exception:  # pragma: no cover
            inner = f"SELECT q.*, ROW_NUMBER() OVER (ORDER BY 1) rn FROM ({query}) q"
            paginated = (
                "SELECT * FROM ("
                + inner
                + ") WHERE rn > :offset AND rn <= :offset_plus"
            )
            params = {
                **params,
                "offset": offset or 0,
                "offset_plus": (offset or 0) + (limit or 0),
            }
            return _execute(paginated, params)
    return _execute(query, params)


def fetch_one(
    query: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    params = params or {}
    rows = fetch_all(query, params)
    return rows[0] if rows else None
