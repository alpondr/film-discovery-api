from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MovieOut(BaseModel):
    id: int
    tmdb_id: int
    title: str
    director: str | None = None
    overview: str | None = None
    release_year: int | None = None
    genres: str | None = None
    created_at: datetime

    # embedding is intentionally excluded - internal detail, never exposed via API
    model_config = ConfigDict(from_attributes=True)


class IngestRequest(BaseModel):
    director: str
    limit: int = 10
