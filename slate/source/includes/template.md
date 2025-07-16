# Template

> The Template Object

```json
{
  "metadata": {
    "qr_entries": [
      "qr_code"
    ]
  },
  "tags": ["2022"],
  "template_id": "student-diploma",
  "template_schema": {
    "properties": {
      "certificate_number": {
        "title": "Certificate Number",
        "type": "string"
      },
      "qr_code": {
        "type": "string"
      },
      "recipient_name": {
        "type": "string"
      }
    },
    "required": [
      "recipient_name",
      "certificate_number"
    ],
    "type": "object"
  },
  "type": "text/html"
}
```

A Template object is none other than an HTML template itself, including the json schema used to fill in the defined
variables in the HTML file.

    Field               | Description                              
    ------------------- | -----------------------------
    template_id         | Unique identifier of the template.
    metadata            | Extra metadata used by the template. For example, can be used to define QR Code fields.
    tags                | Any additional tags that can identify the template.
    template_schema     | The json schema of the template.
    type                | The type of the template (HTML only).
    example_composition | A json containing example values to fill in the template.

## Get All Templates
 
```shell
curl -X GET "http://localhost:8000/templates/" -H  "accept: application/json"
```

```python
templates = plato_client.templates(tags)
```
```python
class TemplateInfo(NamedTuple):
    template_id: str
    template_schema: dict
    type: str
    metadata: dict
    tags: List[str]
```

Retrieves all templates available on the database. Has a single query parameter, "tags", that can be used multiple times
in the same requests. All the tags provided are used to filter for templates that contain at least one of the tags.

### HTTP Request

`GET http://localhost:8000/templates/?tags=abc&tags=xyz`

### Returns

If successful, the HTTP response is a 200 OK, along with all templates.


## Get A Template
 
```shell
curl -X GET "http://localhost:8000/templates/<template_id>" -H  "accept: application/json"
```

Retrieves a specific template and its details. 

### HTTP Request

`GET "http://localhost:8000/templates/<template_id>"`

### Returns

If successful, the HTTP response is a 200 OK, along with the template.

### Errors

     code | Description                              
     ---- | -----------------------------
     404  | Template not found

## Compose File
 
```shell
curl -X POST "http://localhost:8000/template/<template_id>/compose" -H  "accept: <mime_type>" -H "Content-Type: application/json" -d "{\"recipient_name\": \"Alan Turing\"}"
```

```python
file = plato_client.compose(template_id, compose_data, mime_type, page, resize_height, resize_width)
```

Composes a template into a file of a specific type by filling in the placeholders with the intended data. The type of
the file to compose can be defined by the accept header, and is expected to be in MIME format. 
It is currently possible to generate a file of three different types:

* HTML: text/html
* PDF: application/pdf
* PNG: image/png

Other parameters include:

    Parameter   | Type   | Optional | Description                              
    ----------- | ------ | -------- | -----------------------------
    template_id | Path   | No       | ID of the template to compose.
    schema      | Body   | No       | Json containing the data to add to the template, according to template schema.
    accept      | Header | No       | Type of file to create.
    page        | query  | Yes      | Specific page of the template to compose. If none is given, all pages are composed. Defaults to one if an image type is chosen.
    height      | query  | Yes      | Height of the file to compose, if image type is chosen.
    width       | query  | Yes      | Weight of the file to compose, if image type is chosen.  

### HTTP Request

`POST http://localhost:8000/template/<template_id>/compose`

### Returns

If successful, the HTTP response is a 200 OK, along with the file.

### Errors

     code | Description                              
     ---- | -----------------------------
     400  | Invalid compose data for template schema
     404  | Template not found
     406  | Unsupported MIME type for file


## Compose Example
 
```shell
curl -X GET "http://localhost:8000/template/<template_id>/example" -H  "accept: <mime_type>
```

```python
file = plato_client.compose(template_id, compose_data, mime_type, page, resize_height, resize_width)
```

Composes a template into an example file of a specific type. The placeholders are filled in with example data
that is configured directly in the database. The type of the file to compose can be defined by the accept header, 
and is expected to be in MIME format. It is currently possible to generate a file of three different types:

* HTML: text/html
* PDF: application/pdf
* PNG: image/png

Other parameters include:

    Parameter   | Type   | Optional | Description                              
    ----------- | ------ | -------- | -----------------------------
    template_id | Path   | No       | ID of the template to compose.
    accept      | Header | No       | Type of file to create.
    page        | query  | Yes      | Specific page of the template to compose. If none is given, all pages are composed. Defaults to one if an image type is chosen.
    height      | query  | Yes      | Height of the file to compose, if image type is chosen.
    width       | query  | Yes      | Weight of the file to compose, if image type is chosen.  

### HTTP Request

`GET http://localhost:8000/template/<template_id>/example`

### Returns

If successful, the HTTP response is a 200 OK, along with the example file.

### Errors

     code | Description                              
     ---- | -----------------------------
     404  | Template not found
     406  | Unsupported MIME type for file
