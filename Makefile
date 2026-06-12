.PHONY: up down test migrate

up:
	docker compose up --build

down:
	docker compose down

test:
	pytest

migrate:
	@echo "Alembic not set up yet — run P1-2.1 first, then replace this with:"
	@echo "  docker compose exec api alembic upgrade head"