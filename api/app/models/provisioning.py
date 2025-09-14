from datetime import datetime
from pydantic import BaseModel


class Provisioning(BaseModel):
    pri_id: int
    pri_cellular_number: str
    pri_status: str
    pri_action_date: datetime
    pri_error_code: str | None = None
    pri_message_error: str | None = None
    pri_ne_service: str | None = None


class ProvisioningFilter(BaseModel):
    msisdn: str | None = None
    status: str | None = None
    error_code: str | None = None
    ne_service: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
