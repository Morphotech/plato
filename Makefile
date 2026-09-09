include .env

run:
	poetry run fastapi dev app/main.py

tox:
	poetry run tox

pytest:
	poetry run pytest

coverage:
	poetry run coverage erase
	poetry run coverage run --source=app -m pytest
	poetry run coverage report

mypy:
	poetry run mypy app

ruff:
	poetry run ruff check app tests

ruff-format:
	poetry run ruff format app tests

alembic-upgrade:
	poetry run alembic upgrade head

alembic-downgrade:
	@read -p "Version: " version; \
	poetry run alembic downgrade $$version

alembic-revision:
	@read -p "Revision description: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

alembic-merge:
	@read -p "Revision description: " msg; \
	poetry run alembic merge heads -m "$$msg"
