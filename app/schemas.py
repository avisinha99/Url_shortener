from datetime import datetime

from pydantic import BaseModel


class ShortenRequest(BaseModel):
    url: str | None = None
    alias: str | None = None


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
