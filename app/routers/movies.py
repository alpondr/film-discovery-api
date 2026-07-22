from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user
from app.database.session import get_db
from app.models.movie import Movie
from app.models.user import User
from app.schemas.movie import IngestRequest, MovieOut
from app.services import tmdb
from app.services.embedding import embed_text

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("/ingest", response_model=list[MovieOut], status_code=status.HTTP_201_CREATED)
def ingest_movies_by_director(
    request: IngestRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    try:
        fetched = tmdb.fetch_movies_by_director(request.director, limit=request.limit)
    except tmdb.TMDbError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    saved_movies = []
    for movie_data in fetched:
        existing = db.query(Movie).filter(Movie.tmdb_id == movie_data["tmdb_id"]).first()
        if existing:
            saved_movies.append(existing)
            continue

        embedding_source = f"{movie_data['title']}. {movie_data['overview']}"
        movie = Movie(**movie_data, embedding=embed_text(embedding_source))
        db.add(movie)
        db.flush()
        saved_movies.append(movie)

    db.commit()
    for movie in saved_movies:
        db.refresh(movie)

    return saved_movies
