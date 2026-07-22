from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.movie import Movie
from app.models.search_log import SearchLog
from app.models.user import User
from app.schemas.movie import MovieOut
from app.schemas.qa import (
    DirectorStyleRequest,
    DirectorStyleResponse,
    QuestionRequest,
    QuestionResponse,
)
from app.services import groq_service
from app.services.embedding import embed_text

router = APIRouter(prefix="/qa", tags=["qa"])


def _build_context(movies: list[Movie]) -> str:
    lines = [
        f"- {m.title} ({m.release_year}, dir. {m.director}, {m.genres}): {m.overview}"
        for m in movies
    ]
    return "\n".join(lines)


@router.post("/ask", response_model=QuestionResponse)
def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_embedding = embed_text(request.question)

    # retrieval step: find the movies most relevant to the question
    movies = (
        db.query(Movie)
        .order_by(Movie.embedding.cosine_distance(query_embedding))
        .limit(request.limit)
        .all()
    )

    if not movies:
        answer = "I don't have any movies in the database yet to answer this question."
    else:
        # generation step: hand the retrieved movies to the LLM as context
        system_prompt = (
            "You are a knowledgeable film assistant. Answer the user's question using ONLY "
            "the movie information given below as context. Be concise and specific. If the "
            "context doesn't contain enough information, say so honestly instead of guessing.\n\n"
            f"Movie context:\n{_build_context(movies)}"
        )
        answer = groq_service.generate(system_prompt, request.question)

    db.add(SearchLog(user_id=current_user.id, query=request.question, response=answer))
    db.commit()

    return QuestionResponse(answer=answer, sources=[MovieOut.model_validate(m) for m in movies])


@router.post("/director-style", response_model=DirectorStyleResponse)
def director_style(
    request: DirectorStyleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movies = db.query(Movie).filter(Movie.director.ilike(request.director)).all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No movies found for director '{request.director}' - ingest their movies first",
        )

    system_prompt = (
        "You are a film critic. Based ONLY on the movies listed below, describe this "
        "director's stylistic signature - recurring themes, tone, and narrative techniques. "
        "Be specific and reference the movies where relevant.\n\n"
        f"Movies:\n{_build_context(movies)}"
    )
    style_summary = groq_service.generate(
        system_prompt, f"Describe {request.director}'s directing style."
    )

    db.add(SearchLog(
        user_id=current_user.id,
        query=f"director style: {request.director}",
        response=style_summary,
    ))
    db.commit()

    return DirectorStyleResponse(
        director=request.director,
        style_summary=style_summary,
        movies_analyzed=[MovieOut.model_validate(m) for m in movies],
    )
