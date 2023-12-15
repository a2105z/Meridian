"""
Pydantic schemas for Atlas API.
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    first_name: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=64)
    birthday: date
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str
    last_name: str
    birthday: date
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class EntryBase(BaseModel):
    category: str
    date: date
    details: str = Field(..., min_length=1, max_length=5000)


class EntryCreate(EntryBase):
    pass


class EntryUpdate(BaseModel):
    category: Optional[str] = None
    date: Optional[date] = None
    details: Optional[str] = Field(None, min_length=1, max_length=5000)


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category: str
    date: date
    details: str
    created_at: datetime


class EntryListResponse(BaseModel):
    entries: List[EntryOut]
    total_count: int


class AnalyticsSummary(BaseModel):
    username: str
    total_entries: int
    entries_per_category: Dict[str, int]
    first_entry_date: Optional[date]
    last_entry_date: Optional[date]


class TimelineGroup(BaseModel):
    period: str
    count: int


class TimelineReport(BaseModel):
    username: str
    group_by: str
    groups: List[TimelineGroup]


class ByCategoryReport(BaseModel):
    username: str
    by_category: Dict[str, int]


class ActivitySummaryReport(BaseModel):
    username: str
    total_entries: int
    first_entry_date: Optional[date]
    last_entry_date: Optional[date]
    entries_per_category: Dict[str, int]
    timeline_by_month: List[TimelineGroup]


class HealthResponse(BaseModel):
    status: str
    database: str
