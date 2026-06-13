from contextlib import asynccontextmanager

from fastapi import FastAPI

from lex_shortlink_api.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()
    yield

app = FastAPI(
    title="Lex Shortlink API",
    version="0.1.0",
    description="URL shortener with analytics (work in progress).",
)

@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check for local dev, Docker, and load balancers."""
    return {"status": "ok"}