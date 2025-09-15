from datetime import datetime
from typing import Any, Dict, List, Optional

from .oracle import fetch_all, fetch_one


def list_interfaces(
    filters: Dict[str, Any],
    sort_by: str,
    sort_dir: str,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    where = ["1=1"]
    params: Dict[str, Any] = {}
    if msisdn := filters.get("msisdn"):
        where.append("pri_cellular_number = :msisdn")
        params["msisdn"] = msisdn
    if status := filters.get("status"):
        where.append("pri_status = :status")
        params["status"] = status
    if error_code := filters.get("error_code"):
        where.append("pri_error_code = :error_code")
        params["error_code"] = error_code
    if ne_service := filters.get("ne_service"):
        where.append("pri_ne_service = :ne_service")
        params["ne_service"] = ne_service
    if date_from := filters.get("from"):
        where.append("pri_action_date >= :date_from")
        params["date_from"] = date_from
    if date_to := filters.get("to"):
        where.append("pri_action_date <= :date_to")
        params["date_to"] = date_to

    base = " FROM provisioning_interface WHERE " + " AND ".join(where)
    total = fetch_one("SELECT COUNT(*) as cnt" + base, params) or {"cnt": 0}
    rows = fetch_all(
        f"SELECT *{base} ORDER BY {sort_by} {sort_dir}",
        params,
        limit=limit,
        offset=offset,
    )
    return {"total_count": total["cnt"], "rows": rows}


def get_interface(pri_id: int) -> Optional[Dict[str, Any]]:
    return fetch_one(
        "SELECT * FROM provisioning_interface WHERE pri_id = :pri_id",
        {"pri_id": pri_id},
    )


def stats(
    group_by: str, date_from: datetime, date_to: datetime
) -> List[Dict[str, Any]]:
    query = (
        f"SELECT pri_{group_by} as group_key, COUNT(*) as total "
        "FROM provisioning_interface "
        "WHERE pri_action_date BETWEEN :date_from AND :date_to "
        f"GROUP BY pri_{group_by}"
    )
    params = {"date_from": date_from, "date_to": date_to}
    return fetch_all(query, params)
