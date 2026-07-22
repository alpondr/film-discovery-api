from pydantic import BaseModel

from app.schemas.movie import MovieOut


class QuestionRequest(BaseModel):
    question: str
    limit: int = 5


class QuestionResponse(BaseModel):
    answer: str
    sources: list[MovieOut]
