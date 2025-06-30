# Plato Microservice

A python REST API for document composition through jsonschema.

## Getting Started

These instructions will get the project up and running on your local environment, so you can start contributing to the project.

### Prerequisites

- [Python 3.7+](https://www.python.org/)
- [Poetry 1.0+](https://python-poetry.org/)
- [Docker](https://docker.com)
- [Docker-compose](https://docs.docker.com/compose/)

The project depends on [weasyprint](https://weasyprint.org/) for writing PDF from HTML so make sure you have everything
weasy print needs to run by following the instructions on this [page](https://weasyprint.readthedocs.io/en/latest/install.html#linux).

The instructions are also available below.

#### Debian/Ubuntu

```bash
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### Installing

The first thing you should set up is your local .env file.

Do so by copying the template .env by following the step below.

```bash
cp .env.local .env
```

Make sure you fill in the Template directory with an absolute path.
You may use a subdirectory inside your DATA_DIR.

First, make sure you actually _have_ a DATA_DIR, by creating a folder named 'data' within the main project directory.

e.g TEMPLATE_DIRECTORY=/home/carloscoda/projects/plato/data/templates

A couple more environment variables need to be filled as well.
S3_BUCKET is the S3 Bucket you decide to use and S3_TEMPLATE_DIR is the path to
the directory where your templates are stored.

e.g S3_TEMPLATE_DIR=projects/templating

Make sure the bucket is accessible by providing credentials to the service by
storing the S3 AWS credentials in your DATA_DIR/aws/.

#### Database

The templating service uses Postgresql.
To set up local servers you may use the docker-compose file supplied. Then spin up the container by running:

```bash
docker-compose up -d database
```

To do the same for the database you may try accessing it through

```
postgresql://templating:template-pass@localhost:5455/templating
```

Then you have to initialize the DB, which is done through [Alembic](https://alembic.sqlalchemy.org).

```bash
poetry run alembic upgrade head
```

You can then run the application by running:

```bash
poetry run fastapi dev
```

This will make the application available at http://localhost:5000/apidocs/
where you can use swagger-ui to interact with the application.

_Note_: If you run the app through a server instead of main, make sure you run `flask refresh`
so it can obtain the most recent templates from S3.

## Running the tests

Locally:

```bash
poetry run pytest
```

Running tests inside the docker containers (you might need to build the plato docker image first):

```bash
docker-compose -f tests/docker/docker-compose.build.test.yml up -d database

docker-compose -f tests/docker/docker-compose.build.test.yml run --rm test-plato pytest --cov=micro_templating
```

## Use Command Line Interface

```bash
flask <command>
```

## How to use in your project

You will need to add the Plato and Plato database container to your docker-compose file. The templating image is stored on Nexus.
Please check the detailed instructions on the [official documentation](https://plato.vizidox.com).

## Built With

- [Flask](https://palletsprojects.com/p/flask/) - Web framework
- [Flasgger](https://github.com/flasgger/flasgger) - Swagger 2 specification
- [Poetry](https://python-poetry.org/) - Dependency Management
- [Jinja2](https://palletsprojects.com/p/jinja/) - For HTML composition
- [Weasyprint](https://weasyprint.org/) - For PDF generation from HTML

## Versioning

We use [Calendar Versioning](https://calver.org/).

## Authors

- **Tiago Santos** - _Initial work_ - tiago.santos@vizidox.com
- **Rita Mariquitos** - rita.mariquitos@morphotech.co.uk
- **Joana Teixeira** - joana.teixeira@vizidox.com
