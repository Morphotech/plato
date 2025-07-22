# Plato Microservice

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/31c109ed05314bb79a65c200026742fa)](https://app.codacy.com/gh/Morphotech/plato/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/31c109ed05314bb79a65c200026742fa)](https://app.codacy.com/gh/Morphotech/plato/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)

A python REST API for document composition through jsonschema.

## Getting Started

These instructions will get the project up and running on your local environment, so you can start contributing to the project.

### Prerequisites

- [Python 3.7+](https://www.python.org/)
- [Poetry 1.0+](https://python-poetry.org/)
- [Docker](https://docker.com)
- [Docker-compose](https://docs.docker.com/compose/)

The project depends on [weasyprint](https://weasyprint.org/) for writing PDF from HTML so make sure you have everything
weasyprint needs to run by following the instructions on this [page](https://weasyprint.readthedocs.io/en/latest/install.html#linux).

The instructions are also available below.

#### Debian/Ubuntu

```bash
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

```

#### MacOS

```bash
brew install weasyprint
```

Check if weasyprint is working:

```bash
weasyprint --info
```

If the above command does not work, or if it does work but Plato complains about fontconfig, then run the following command:

```bash
sudo mkdir -p /usr/local/lib
sudo cp $(brew --prefix fontconfig)/lib/libfontconfig.\* /usr/local/lib
```

Alternatively, if the above does not work, you can fetch the libfontconfig files directly from the Homebrew Cellar:

```bash
sudo cp /opt/homebrew/Cellar/fontconfig/<VERSION>/lib/libfontconfig.* /usr/local/lib
````

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
S3_BUCKET is the S3 Bucket you decide to use and TEMPLATE_DIRECTORY_NAME is the path to
the directory where your templates are stored.

e.g TEMPLATE_DIRECTORY_NAME=projects/templating

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

This will make the application available at http://localhost:8000/docs/
where you can use Swagger UI to interact with the application. 
You can also check the Bruno Collection supplied in the repository to test the API endpoints.

_Note_: If you run the app through a server instead of main, make sure you run `python app/cli.py refresh`
so it can obtain the most recent templates from S3.

## Running the tests

Locally:

```bash
poetry run pytest
```

Running tests inside the docker containers (you might need to build the plato docker image first):

```bash
docker-compose -f docker-compose.ci.yml up -d database

docker compose -f docker-compose.ci.yml run --rm test-plato

docker-compose -f docker-compose.ci.yml down

```

## Use Command Line Interface

You can use the CLI to manage templates directly from the command line. To use it, you need run the command `python app/cli.py <command> <args>`.

```bash
# Export a template to a file (will prompt for template id if not provided)
python app/cli.py export-template output.json --template-id=your_template_id

# Refresh local templates from file storage
python app/cli.py refresh
```

To see the available options for each command, you can run `python app/cli.py <command> --help`. To list all commands and get instructions, run `python app/cli.py --help`.

## Publishing a new image version

1. Guarantee the code is working and all tests are passing (especially in docker! If any test fails, fix it before proceeding):
    ```bash
    docker compose build plato-api
    docker compose -f docker-compose.ci.yml run --rm test-plato
    ```
   
2. Update the version in `pyproject.toml` file, according to the [Calendar Versioning](https://calver.org/) scheme.
3. (Skip if done previously) Login to the Docker registry with `docker login`. You need to have access to the Vizidox dockerhub account, which is on Keepass.
4. Build and push the docker image with the command:

    ```bash
    docker buildx build -f Dockerfile --platform linux/amd64,linux/arm64 -t 'vizidox/plato:<VERSION>' .
    docker push vizidox/plato:<VERSION>
    ```

    Note: At least on MacOS using Docker Desktop, you may need to activate "containerd for pulling and storing images", in the General settings. Also check if your builder includes both arm64 and amd64 platforms by running `docker buildx ls`.

## How to use in your project

You will need to add the Plato and Plato database container to your docker-compose file. The templating image is stored on Nexus.
Please check the detailed instructions on the [official documentation](https://plato.vizidox.com).

## Built With

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Poetry](https://python-poetry.org/) - Dependency Management
- [Jinja2](https://palletsprojects.com/p/jinja/) - For HTML composition
- [Weasyprint](https://weasyprint.org/) - For PDF generation from HTML

## Versioning

We use [Calendar Versioning](https://calver.org/).

## Authors

- **Tiago Santos** - _Initial work_
- **Rita Mariquitos** - Improvements - rita.mariquitos@morphotech.com
- **Joana Teixeira** - Improvements - joana.teixeira@morphotech.com
- **Fábio André Damas** - Upgrade to FastAPI - fabio.damas@morphotech.com
