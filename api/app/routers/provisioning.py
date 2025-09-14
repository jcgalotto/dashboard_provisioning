from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..core.deps import get_current_user
from ..db import oracle, queries

router = APIRouter(prefix="/provisioning", tags=["provisioning"])


@router.get("/interfaces")
def list_interfaces(
    page: int = 1,
    page_size: int = 10,
    sort: str = "pri_id",
    msisdn: Optional[str] = None,
    status: Optional[str] = None,
    error_code: Optional[str] = None,
    ne_service: Optional[str] = None,
    user: str = Depends(get_current_user),
):
    filters = []
    params: dict[str, object] = {}
    if msisdn:
        filters.append("AND pri_cellular_number = :msisdn")
        params["msisdn"] = msisdn
    if status:
        filters.append("AND pri_status = :status")
        params["status"] = status
    if error_code:
        filters.append("AND pri_error_code = :error_code")
        params["error_code"] = error_code
    if ne_service:
        filters.append("AND pri_ne_service = :ne_service")
        params["ne_service"] = ne_service
    query = queries.LIST_PROVISIONING.format(
        msisdn_filter=" ".join(f for f in filters if 'msisdn' in f),
        status_filter=" ".join(f for f in filters if 'status' in f),
        error_filter=" ".join(f for f in filters if 'error_code' in f),
        ne_service_filter=" ".join(f for f in filters if 'ne_service' in f),
        date_filter="",
        order_column=sort,
        order_dir="ASC",
    )
    offset = (page - 1) * page_size
    data = oracle.fetch_page(query, params, limit=page_size, offset=offset)
    return {"data": data}


@router.get("/interfaces/{pri_id}")
def get_interface(pri_id: int, user: str = Depends(get_current_user)):
    return oracle.fetch_one(queries.DETAIL_PROVISIONING, {"pri_id": pri_id})


@router.get("/interfaces/stats")
def get_stats(
    group_by: str = Query("status", regex="^(status|error_code|ne_service)$"),
    _from: str = Query(..., alias="from"),
    to: str = Query(...),
    user: str = Depends(get_current_user),
):
    query = queries.STATS_PROVISIONING.format(group_by=f"pri_{group_by}")
    params = {"from": _from, "to": to}
    return oracle.fetch_all(query, params)
