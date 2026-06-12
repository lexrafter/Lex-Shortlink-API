# Lex-Shortlink-API
FastAPI URL shortener with Postgres, Redis caching, and click analytics

## Local development
Requirements: Python 3.11+
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn lex_shortlink_api.main:app --reload --app-dir src

## Docker
docker compose up --build
curl http://localhost:8000/health

## Make commands

make up       # start api + postgres + redis
make down     # stop containers
make test     # run pytest
make migrate  # run DB migrations (after Alembic is configured)
