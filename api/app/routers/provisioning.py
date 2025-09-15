from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..core.deps import get_current_user
from ..db import queries
from ..models.provisioning import InterfaceRow, InterfacesResponse, StatsItem

router = APIRouter(prefix="/provisioning", tags=["provisioning"])


@router.get("/interfaces", response_model=InterfacesResponse)
def list_interfaces(
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "pri_action_date",
    sort_dir: str = "desc",
    msisdn: str | None = None,
    status: str | None = None,
    error_code: str | None = None,
    ne_service: str | None = None,
    date_from: Optional[datetime] = Query(None, alias="from"),
    date_to: Optional[datetime] = Query(None, alias="to"),
    user: str = Depends(get_current_user),
) -> InterfacesResponse:
    filters = {
        "msisdn": msisdn,
        "status": status,
        "error_code": error_code,
        "ne_service": ne_service,
        "from": date_from,
        "to": date_to,
    }
    offset = (page - 1) * page_size
    result = queries.list_interfaces(filters, sort_by, sort_dir, page_size, offset)
    rows = [InterfaceRow(**row) for row in result["rows"]]
    return InterfacesResponse(total_count=result["total_count"], rows=rows)


@router.get("/interfaces/{pri_id}", response_model=InterfaceRow | None)
def get_interface(pri_id: int, user: str = Depends(get_current_user)):
    row = queries.get_interface(pri_id)
    return InterfaceRow(**row) if row else None


@router.get("/interfaces/stats", response_model=list[StatsItem])
def get_stats(
    group_by: str = Query("status", pattern="^(status|error_code|ne_service)$"),
    date_from: datetime = Query(..., alias="from"),
    date_to: datetime = Query(..., alias="to"),
    user: str = Depends(get_current_user),
) -> list[StatsItem]:
    rows = queries.stats(group_by, date_from, date_to)
    return [StatsItem(**row) for row in rows]
