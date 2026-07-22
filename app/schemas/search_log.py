from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SearchLogOut(BaseModel):
    id: int
    query: str
    response: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedSearchLogs(BaseModel):
    items: list[SearchLogOut]
    total: int
    page: int
    size: int
    pages: int
