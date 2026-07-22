from fastapi import FastAPI

from app.routers import auth, movies, qa

app = FastAPI(title="Film Discovery API")

app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(qa.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
