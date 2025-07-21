FROM python:3.13-slim

RUN mkdir /plato

RUN apt update && apt install -y build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
RUN pip install poetry==2.1.2

COPY ./app /plato/app
COPY ./tests /plato/tests
COPY pyproject.toml /plato/pyproject.toml
COPY poetry.lock /plato/poetry.lock

ENV PYTHONPATH=:/plato

WORKDIR /plato
RUN poetry install

CMD ["poetry", "run" ,"uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
