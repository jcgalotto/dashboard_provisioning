from typing import Any, Dict, List, Optional

try:
    import oracledb as cx_Oracle  # thin mode
except Exception:  # pragma: no cover
    import cx_Oracle  # type: ignore

from ..core.config import get_settings

settings = get_settings()

try:
    pool = cx_Oracle.SessionPool(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=settings.ORACLE_DSN,
        min=settings.ORACLE_POOL_MIN,
        max=settings.ORACLE_POOL_MAX,
        increment=1,
        threaded=True,
        getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT,
    )
except Exception:  # pragma: no cover - if client not installed
    pool = None


def fetch_all(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if pool is None:
        return []
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or {})
            columns = [col[0].lower() for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_one(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if pool is None:
        return None
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or {})
            row = cursor.fetchone()
            if row:
                columns = [col[0].lower() for col in cursor.description]
                return dict(zip(columns, row))
    return None


def fetch_page(query: str, params: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
    if pool is None:
        return []
    paginated_query = (
        f"SELECT * FROM (SELECT q.*, ROWNUM rn FROM ({query}) q WHERE ROWNUM <= :limit_plus)" " WHERE rn > :offset"
    )
    params = dict(params)
    params.update({"limit_plus": offset + limit, "offset": offset})
    return fetch_all(paginated_query, params)
