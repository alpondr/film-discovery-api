from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user, get_current_user
from app.database.session import get_db
from app.models.movie import Movie
from app.models.search_log import SearchLog
from app.models.user import User
from app.schemas.movie import IngestRequest, MovieOut, SearchQuery, SearchResult
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


@router.post("/search", response_model=list[SearchResult])
def semantic_search(
    request: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_embedding = embed_text(request.query)

    # cosine_distance ranges 0 (identical) - 2 (opposite); similarity = 1 - distance
    rows = (
        db.query(Movie, Movie.embedding.cosine_distance(query_embedding).label("distance"))
        .order_by("distance")
        .limit(request.limit)
        .all()
    )

    results = [
        SearchResult(movie=MovieOut.model_validate(movie), similarity=round(1 - distance, 4))
        for movie, distance in rows
    ]

    db.add(SearchLog(
        user_id=current_user.id,
        query=request.query,
        response=", ".join(r.movie.title for r in results),
    ))
    db.commit()

    return results
