from pydantic import BaseModel

from app.schemas.movie import MovieOut


class QuestionRequest(BaseModel):
    question: str
    limit: int = 5


class QuestionResponse(BaseModel):
    answer: str
    sources: list[MovieOut]


class DirectorStyleRequest(BaseModel):
    director: str


class DirectorStyleResponse(BaseModel):
    director: str
    style_summary: str
    movies_analyzed: list[MovieOut]
