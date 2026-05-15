from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Endpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    method: str = "GET"
    headers: Optional[str] = None
    body: Optional[str] = None
    interval_minutes: int = 5
    is_active: bool = True
    tags: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_status_code: Optional[int] = None
    ignore_array_order: bool = False

class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint_id: int = Field(foreign_key="endpoint.id")
    response_body: Optional[str] = None
    status_code: int
    response_time_ms: int
    content_hash: str
    captured_at: datetime = Field(default_factory=datetime.utcnow)

class DiffRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint_id: int = Field(foreign_key="endpoint.id")
    snapshot_before_id: int
    snapshot_after_id: int
    diff_json: Optional[str] = None
    severity: str = "INFO"
    created_at: datetime = Field(default_factory=datetime.utcnow)