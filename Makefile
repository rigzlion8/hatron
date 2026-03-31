.PHONY: dev up down db-up migrate revision seed test lint format

# Development
dev:
	uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Docker
up:
	docker compose up -d

down:
	docker compose down

db-up:
	docker compose up -d db redis

# Database
migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(msg)"

downgrade:
	uv run alembic downgrade -1

seed:
	uv run python -m scripts.seed_data

# Testing
test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=backend --cov-report=html

# Code quality
lint:
	uv run ruff check backend/ tests/

format:
	uv run ruff format backend/ tests/

# Utilities
shell:
	uv run python -c "import asyncio; asyncio.run(__import__('backend.core.database', fromlist=['async_session']).async_session())"
