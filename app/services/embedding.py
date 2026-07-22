from functools import lru_cache

from sentence_transformers import SentenceTransformer

# 384-dim output, matches Movie.embedding column (see app/models/movie.py)
MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # loaded once per process - downloads from huggingface on first run, then cached locally
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
