from fastapi import FastAPI

app = FastAPI(
    title="Lex Shortlink API",
    version="0.1.0",
    description="URL shortener with analytics (work in progress).",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check for local dev, Docker, and load balancers."""
    return {"status": "ok"}