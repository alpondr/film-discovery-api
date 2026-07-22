# Film Discovery API

A backend project for exploring movies through semantic search and a small
RAG pipeline. You can ask things like "a whimsical family adventure" or
"what do these Tarantino movies have in common" instead of searching by
exact keywords.

Built with FastAPI, PostgreSQL + pgvector, and a local embedding model, with
Groq as the LLM for the RAG part.

## Stack

- FastAPI
- PostgreSQL + pgvector (vector similarity search)
- SQLAlchemy + Alembic
- sentence-transformers (`all-MiniLM-L6-v2`) for embeddings - runs locally, no API key
- Groq API for the LLM (question answering, director style analysis)
- TMDb API for movie data
- JWT auth (python-jose + passlib)

## Setup

1. Copy `.env.example` to `.env` and fill in your own values:
   - `TMDB_API_KEY` - get one free at themoviedb.org
   - `GROQ_API_KEY` - get one free at console.groq.com
   - `SECRET_KEY` - any random string, used to sign JWTs

2. Start the database:
   ```
   docker compose up -d
   ```

3. Install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Run migrations (this also enables the pgvector extension):
   ```
   alembic upgrade head
   ```

5. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

API docs are at `http://localhost:8000/docs`.

## Endpoints

| Endpoint | Method | Auth | What it does |
|---|---|---|---|
| `/auth/register` | POST | - | create an account |
| `/auth/login` | POST | - | get a JWT access token |
| `/movies/ingest` | POST | admin | fetch a director's movies from TMDb, embed and save them |
| `/movies/search` | POST | user | semantic search over saved movies |
| `/qa/ask` | POST | user | RAG question answering about the movies in the database |
| `/qa/director-style` | POST | user | LLM summary of a director's style, based on their ingested movies |
| `/history` | GET | user | paginated list of your own past searches/questions |

There's no endpoint to make a user admin - that's done manually in the
database (`UPDATE users SET is_admin = true ...`). Didn't want a
self-promotion endpoint sitting in the API.

## Notes on design decisions

- **Why pgvector instead of a separate vector DB (Pinecone, Weaviate, etc.)**:
  didn't want to run and pay for a second database just for vectors. Postgres
  already stores the movie rows, so keeping the embedding as just another
  column means one query can filter on normal fields (genre, director) and
  order by similarity at the same time, instead of stitching results from
  two systems together.

- **Why `all-MiniLM-L6-v2` for embeddings**: it's small (~80MB), runs fine on
  CPU, and is free/local - no API key or per-request cost. 384 dimensions is
  enough for this project's scale (a few hundred movies), and a bigger model
  would mostly just mean slower embedding for no real gain here.

- **RAG instead of just asking the LLM directly**: an LLM alone would happily
  make up plot details or attribute quotes to the wrong movie. Retrieving the
  actual TMDb overview first and forcing the LLM to answer "only using this
  context" cuts down on that a lot - it's not perfect, but it's a real
  difference from a plain chat completion.

- **Ingestion is idempotent by `tmdb_id`**: re-ingesting a director you
  already have doesn't create duplicate rows or re-run the embedding model
  on movies you already embedded. Useful since embedding a batch of movies
  isn't instant and there's no reason to redo it.

- **Search history is scoped to `current_user.id` from the JWT, never from
  a URL/body parameter**: otherwise one user could page through another
  user's search history just by changing an id somewhere in the request.
