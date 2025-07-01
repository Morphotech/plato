FROM python:3.13-alpine

WORKDIR /plato

RUN apk add cairo-dev pango pango-dev
RUN pip install poetry
COPY ./app /plato/app
COPY pyproject.toml /plato/pyproject.toml
COPY poetry.lock /plato/poetry.lock
RUN poetry install 

CMD ["poetry", "run" ,"uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
