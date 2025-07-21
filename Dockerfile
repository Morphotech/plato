FROM python:3.13-alpine

RUN mkdir /plato

RUN apk add cairo-dev pango pango-dev
RUN pip install poetry==2.1.2

COPY ./app /plato/app
COPY ./tests /plato/tests
COPY pyproject.toml /plato/pyproject.toml
COPY poetry.lock /plato/poetry.lock

ENV PYTHONPATH=:/plato

WORKDIR /plato
RUN poetry install

CMD ["poetry", "run" ,"uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
