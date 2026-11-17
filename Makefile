.PHONY: up down migrate seed ingest test eval eval-record lint

up:
	docker compose up -d

down:
	docker compose down -v

migrate:
	alembic upgrade head

seed:
	python -m app.seed

ingest:
	python -m app.retrieval.ingest

test:
	pytest -v

eval:
	python -m evals.run

eval-record:
	LLM_MODE=record python -m evals.run

lint:
	ruff check .
