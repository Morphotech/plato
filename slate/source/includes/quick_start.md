# Quick Start

Plato is a microservice that should be added directly to your deployment environment. A docker image is available on
Docker Hub, and this guide will show you how to integrate Plato with your existing project. 

## Requirements

* S3 bucket and respective AWS credentials.
* Docker compose file.
* At least one template. Read on how to create one [here](#create-template).

## Steps

### Configure S3 Bucket

You will need to create an S3 Bucket if your project doesn't already have one, and fetch its credentials. Plato 
will need the AWS credentials so it can access the S3 Bucket and load the templates and static content to the machine.
The AWS credentials need to be passed into the Plato container as a volume - an example docker-compose file is available 
later in this [tutorial](#docker-configuration).

Also, please take into consideration that the bucket's structure will need to follow a specific set of rules:

* You require a main, base directory for all the templating files. This can be called anything you want (ex: plato), 
 and does not have to be localized in the base bucket directory. 
* Inside the main directory, two subdirectories are required with very specific names and structures:
  * **templates** directory, where the HTML files of the templates are stored. Each template HTML file is stored within
  a folder that is named the same as the template ID. Furthermore, the HTML file should also be named the same and
  should not contain an extension (.html).
  * **static** directory, where the template static files are stored. Similarly to the templates folder, all static files
  for a template are stored in a folder with the same name as the template ID. The static content can have any name or
  structure, as long as they are correctly imported in the HTML file.
  
For example:

  * `plato/static/example_template/image.png`
  * `plato/templates/example_template/example_template`

### Docker configuration

```yaml
plato:
  image: plato-api:<VERSION>
  environment:
    DATA_DIR: /plato-data/
    TEMPLATE_DIRECTORY: /plato-data/templating/
    DB_HOST: plato-database
    DB_PORT: <PORT>
    DB_USERNAME: <USER>
    DB_PASSWORD: <PASSWORD>
    DB_DATABASE: <DB>
    S3_BUCKET: <PLATO_BUCKET>
    STORAGE_TYPE: <STORAGE_TYPE>
    POSTGRES_VER: <{POSTGRES_VER>
  depends_on:
    - plato-database
  volumes:
    - <AWS_CREDENTIALS>:/root/.aws
  ports:
    - 80:80

plato-database:
  image: postgres:<VERSION>
  volumes:
    - <DATABASE_DIR>/plato-db:/data/db
  environment:
    POSTGRES_USER: <USER>
    POSTGRES_PASSWORD: <PASSWORD>
    POSTGRES_DB: <DB>
    PGDATA: /data/db/
  ports:
    - 5455:5432
```

<aside class="notice">
    We recommend using a docker-compose file for the Plato configuration, and this tutorial will follow that approach. However, Plato also works with plain Docker.
</aside>

Plato requires a Postgres database to work with; we recommend configuring it via Docker, but you can also use any external
database already available on your project. Plato is currently developed with Postgres version 9.6.3, and has been successfully 
used with Postgres up to version 17.5. The database contains a single table called *Template* where all templates are stored. 
The *Alembic* table can be ignored, since it is used for migrations.

You can directly copy the accompanying docker-compose configuration to your project, but make sure to fill in the missing variables:

* S3_BUCKET: The name of the bucket on S3 to be used
* TEMPLATE_DIRECTORY_NAME: The base directory for Plato templates on the S3 bucket. The full path to the folder is required if it is not in the base directory. Per our previous example, this
  value would be "plato".
* STORAGE_TYPE: The storage type to be used by Plato. Currently, only "s3" or "disk" are supported.
* POSTGRES_VER: The Postgres version to be used by Plato. 
* Database credentials (USER, PASSWORD, DB)

You should not change the values for the DATA_DIR and TEMPLATE_DIRECTORY variables. All others can be changed and adapted
to fit accordingly to your project's configuration. Also note that a volume for AWS credentials is created, so you have
to indicate where the credentials are in the running environment.

You can now run both docker containers and the Plato API swagger will be available on http://localhost/docs. 
80 is the default port defined on the docker-compose file, but it can be changed for anything else.

### Add Templates to Plato

```json
{
  "title": "student-diploma",
  "schema": {
    "type": "object",
    "required": [
      "recipient_name",
      "certificate_number"
    ],
    "properties": {
      "certificate_number": {
        "type": "string"
      },
      "qr_code": {
        "type": "string"
      },
      "recipient_name": {
        "type": "string"
      }
    }
  },
  "type": "text/html",
  "metadata": {
    "qr_entries": [
      "qr_code"
    ]
  },
  "example_composition": {
    "qr_code": "https://vizidox.com",
    "recipient_name": "Alan Turing",
    "certificate_number": "123ABC"
  },
  "tags": [
    "2022"
  ]
}
```

If you have already added your template files to the Plato storage, per the previous instructions on this guide, and 
you have both the database and the API up and running, then the only thing missing is to create your JSON Schema and 
populate the database with the template data.

To define the JSON Schema and other data, you need to define what fields in the HTML are to be filled in, and specify their
types, if they are required, etc. Check the [JSON Schema specification](https://json-schema.org/specification.html) to learn the expected syntax.
Regarding the rest of the template data:

* Title: The template name/ID 
* Type: The template type. Currently, only "application/html" is accepted.
* Metadata: Fully optional field that can be left empty, but can be used to define QR fields in the HTML. To do so, you need to add a "qr_entries" array
  to the metadata field, containing a list of all template fields that contain an URL to be transformed into QR codes. These fields should
  be in a  [JMESPath](https://jmespath.org/) friendly sequence such as, for example, "course.organization.contact.website_url".
* Example Composition: A JSON containing example values for the fields in the template. Can be used to quickly generate an example file of the template.
* Tags: Any additional details that can be used to identify the template.


To populate the templates on the Plato database, you can follow two different approaches:

> Example query to insert a template on the database

```
INSERT INTO public."template"
(id, "schema", "type", metadata, tags, example_composition)
VALUES('student-diploma', '{"type": "object", "required": ["recipient_name", "certificate_number"], "properties": {"qr_code": {"type": "string"}, "recipient_name": {"type": "string"}, "certificate_number": {"type": "string", "title": "Certificate Number"}}}'::jsonb, 'text/html'::public.template_mime_type, '{"qr_entries": ["qr_code"]}'::jsonb, '{}', '{"qr_code": "https://vizidox.com", "recipient_name": "Alan Turing", "certificate_number": "C5678"}'::jsonb);
```

* Directly insert them in the database via a SQL insert query. The *template* table consists of (similarly to the JSON presented to the right):

    Column              | Type          | Description                              
  --------------------- | ------------- | ----------------------
    id                  | string        | Template ID
    schema              | jsonb         | JSON Schema of the template
    type                | string        | MIME type for template type
    metadata            | jsonb         | JSON dictionary for arbitrary data useful for you 
    tags                | Array[String] | List of tags
    example_composition | jsonb         | JSON dictionary with a compose example for the template
  
  An example insertion query can be found on the right side of this page.

```shell
  docker compose exec -T api poetry run python /app/cli.py <command> <args>
  
  Commands:
    export-template        Export new template to file Args: output: output...
    refresh                
```

* Use the Plato CLI. You have to enter the container with the *run* command, and then execute the *export-template* command, according to instructions to the right.
   You can also run `docker compose exec -T api poetry run python /app/cli.py --help` for information on the available commands.
   The input JSON file that the *export-template* command requires has the JSON structure found on the right side of the page. Note that the title corresponds directly to the
   template ID.

<aside class="warning">
    Whenever changes are done to the Bucket (such as adding a new template or updating existing ones) make sure to refresh the API by following the below instructions. If you only did changes to the templates on the database, however, this does not apply.
</aside>

After inserting the template data in the database, the Plato API needs to be refreshed. To do so, you can either restart the
Plato container manually, or run the *refresh* command via the Plato CLI. At this time, all template files will be downloaded
to Plato's local temporary storage (the aforementioned DATA_DIR), so depending on the number of templates that are configured, 
this might take some time. Every time Plato is restarted, these files are re-downloaded.