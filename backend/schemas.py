from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EndpointCreate(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[dict] = None
    interval_minutes: int = 5
    tags: Optional[str] = None
    ignore_array_order: bool = False

class EndpointRead(BaseModel):
    id: int
    url: str
    method: str
    interval_minutes: int
    is_active: bool
    tags: Optional[str]
    last_checked_at: Optional[datetime]
    last_status: Optional[str]
    last_status_code: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class DiffRead(BaseModel):
    id: int
    endpoint_id: int
    diff_json: Optional[str]
    severity: str
    created_at: datetime
    snapshot_before_id: int
    snapshot_after_id: int

    class Config:
        from_attributes = True