# Template Management

## Create a Template

```shell
curl -X POST "http://localhost:8000/template/create" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "zipfile=<file>>;type=application/zip" -F "template_details=<details>>"
```

```python
template = plato_client.create_template(template, template_details)
```
```python
class TemplateInfo(NamedTuple):
    template_id: str
    template_schema: dict
    type: str
    metadata: dict
    tags: List[str]
```

Create a new template on Plato. Adds the provided HTML and static files to Plato's long term storage, and the details 
are added to the database.

    Parameter        | Type      | Optional | Description                              
    ---------------- | --------- | -------- | -----------------------------
    zipfile          | Form data | No       | Archive containing the template HTML and static files
    template_details | Form data | No       | Details of the template, in json format

The *zipfile* parameter should be a ZIP archive with a structure similar the Plato's permanent storage:

* "templates" folder containing a folder with the name of the template and inside an HTML file. The HTML file should have the name of the template, and no extension. 
  For example, if the user is creating a templated named "example-template", then the html file should be named "example-template".
* "static" folder, containing a folder with the name of the template and inside any static files required by the template. If no files are required, the folder should be empty.

The template_details parameter should be in json format and include all relevant details for the template creation:

    Name                | Description                              
    ------------------- | -------------
    id                  | Template identifier.
    schema              | Template JSON schema.
    type                | Type of the template. Only "text/html" is accepted.
    metadata            | Any additional metadata such as QR Code fields.
    example_composition | A JSON containing an example composition for the template.
    tags                | Extra tags to help identify the template


### HTTP Request

`POST http://localhost:8000/template/create`

### Returns

If successful, the HTTP response is a 201 CREATED, along with the created template.

### Errors

     code | Description                              
     ---- | -----------------------------
     400  | Provided ZIP file does not have the correct structure
     409  | The template already exists
     415  | The provided file is not a ZIP file

## Update a Template

```shell
curl -X PUT "http://localhost:8000/template/<template_id>/update" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "zipfile=<file>>;type=application/zip" -F "template_details=<details>>"
```

```python
template = plato_client.update_template(template_id, file_stream, template_details)
```

```python
class TemplateInfo(NamedTuple):
    template_id: str
    template_schema: dict
    type: str
    metadata: dict
    tags: List[str]
```

Update an existing template on Plato. The template is fully updated, including the HTML file, static content and database entry.

    Parameter        | Type      | Optional | Description                              
    ---------------- | --------- | -------- | -----------------------------
    zipfile          | Form data | No       | Archive containing the template HTML and static files
    template_details | Form data | No       | Details of the template, in json format

The format of the zipfile and the template_details parameters is the same as in the previous endpoint.

### HTTP Request

`PUT http://localhost:8000/template/<template_id>/update`

### Returns

If successful, the HTTP response is a 200 OK, along with the updated template.

### Errors

     code | Description                              
     ---- | -----------------------------
     400  | Provided ZIP file does not have the correct structure
     404  | Template not found
     415  | The provided file is not a ZIP file

## Update Template Details

```shell
curl -X PATCH "http://localhost:8000/template/<template_id>/update_details" -H  "accept: application/json" -H  "Content-Type: application/json" -d <details>
```

```python
template = plato_client.update_template_details(template_id, template_details)
```

```python
class TemplateInfo(NamedTuple):
    template_id: str
    template_schema: dict
    type: str
    metadata: dict
    tags: List[str]
```

Update the database details for an existing template on Plato. No changes are done to the HTML and static content
of the template.

    Parameter        | Type | Optional | Description                              
    ---------------- | ---- | -------- | -----------------------------
    template_details | Body | No       | Details of the template, in json format

The format of the template_details parameter is the same as in the template creation endpoint.

### HTTP Request

`PATCH http://localhost:8000/template/<template_id>/update_details`

### Returns

If successful, the HTTP response is a 200 OK, along with the updated template.

### Errors

     code | Description                              
     ---- | -----------------------------
     400  | Input not in correct form
     404  | Template not found
