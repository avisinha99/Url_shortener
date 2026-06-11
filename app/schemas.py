from datetime import datetime

from pydantic import BaseModel, Field


class ShortenRequest(BaseModel):
    url: str = Field(min_length=1)
    alias: str | None = Field(default=None, max_length=32)


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    code: str
    original_url: str
    click_count: int
    created_at: datetime
    last_clicked_at: datetime | None
