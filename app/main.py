from fastapi import FastAPI

app = FastAPI(title="Film Discovery API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
