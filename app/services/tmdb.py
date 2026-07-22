import time

import httpx

from app.core.config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"

# small delay between consecutive detail requests so we don't burst TMDb
REQUEST_DELAY_SECONDS = 0.25
MAX_RETRIES = 3


class TMDbError(Exception):
    pass


def _get(path: str, params: dict | None = None) -> dict:
    params = dict(params or {})
    params["api_key"] = settings.tmdb_api_key
    url = f"{TMDB_BASE_URL}{path}"

    for attempt in range(MAX_RETRIES):
        response = httpx.get(url, params=params, timeout=10)

        if response.status_code == 429:
            # TMDb is rate limiting us - back off and retry instead of failing outright
            retry_after = int(response.headers.get("Retry-After", 1))
            time.sleep(retry_after)
            continue

        if response.status_code != 200:
            raise TMDbError(f"TMDb request failed ({response.status_code}): {response.text}")

        return response.json()

    raise TMDbError(f"TMDb rate limit exceeded after {MAX_RETRIES} retries: {path}")


def search_person(name: str) -> dict | None:
    data = _get("/search/person", {"query": name})
    results = data.get("results", [])
    return results[0] if results else None


def get_director_movie_ids(person_id: int) -> list[int]:
    data = _get(f"/person/{person_id}/movie_credits")
    crew = data.get("crew", [])
    return [item["id"] for item in crew if item.get("job") == "Director"]


def get_movie_details(movie_id: int) -> dict:
    return _get(f"/movie/{movie_id}")


def _parse_release_year(release_date: str | None) -> int | None:
    if not release_date:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None


def fetch_movies_by_director(director_name: str, limit: int = 10) -> list[dict]:
    """Look up a director on TMDb and return details for their movies.

    Returns plain dicts shaped like the Movie model fields (minus embedding,
    which gets added later once we run the text through sentence-transformers).
    """
    person = search_person(director_name)
    if person is None:
        raise TMDbError(f"No TMDb person found for director '{director_name}'")

    movie_ids = get_director_movie_ids(person["id"])[:limit]

    movies = []
    for movie_id in movie_ids:
        details = get_movie_details(movie_id)
        time.sleep(REQUEST_DELAY_SECONDS)

        genre_names = ", ".join(g["name"] for g in details.get("genres", []))
        movies.append({
            "tmdb_id": details["id"],
            "title": details.get("title", ""),
            "director": director_name,
            "overview": details.get("overview", ""),
            "release_year": _parse_release_year(details.get("release_date")),
            "genres": genre_names,
        })

    return movies
