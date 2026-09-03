FROM python:3.13 AS builder

RUN pip install poetry==2.1.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /plato
COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

FROM python:3.13-slim AS runtime

RUN apt update && apt install --no-install-recommends -y \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-xlib-2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /plato
ENV VIRTUAL_ENV=/plato/.venv \
    PATH="/plato/.venv/bin:$PATH" \
    PYTHONPATH=:/plato

COPY --from=builder /plato/pyproject.toml /plato/pyproject.toml
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./alembic.ini /plato/alembic.ini
COPY ./migrations /plato/migrations
COPY ./app /plato/app
