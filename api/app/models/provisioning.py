from datetime import datetime
from typing import List

from pydantic import BaseModel


class InterfaceRow(BaseModel):
    pri_id: int
    pri_cellular_number: str
    pri_status: str
    pri_action_date: datetime
    pri_error_code: str | None = None
    pri_message_error: str | None = None
    pri_ne_service: str | None = None


class InterfacesResponse(BaseModel):
    total_count: int
    rows: List[InterfaceRow]


class StatsItem(BaseModel):
    group_key: str | None = None
    total: int
