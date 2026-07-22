from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database.session import Base

# all-MiniLM-L6-v2 (sentence-transformers) outputs 384-dim vectors
EMBEDDING_DIM = 384


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False, index=True)
    director = Column(String, index=True)
    overview = Column(Text)
    release_year = Column(Integer)
    genres = Column(String)
    embedding = Column(Vector(EMBEDDING_DIM))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
