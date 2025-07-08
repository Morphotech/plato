# import json
#
# from http import HTTPStatus
# from pathlib import Path
#
# import boto3
# import pytest
# from moto import mock_s3
# from sqlalchemy.orm import Session
#
# from app.db.models.template import Template
#
# from tests.test_s3_application_set_up import BUCKET_NAME
#
# TEMPLATE_ID = "template_test_1"
# CURRENT_TEST_PATH = str(Path(__file__).resolve().parent)
# TEMPLATE_DETAILS_1 = {"title": TEMPLATE_ID,
#                       "schema": {
#                           "type": "object",
#                           "required": [
#                               "cert_name",
#                               "serial_number"
#                           ],
#                           "properties": {
#                               "qr_code": {
#                                   "type": "string"
#                               },
#                               "cert_name": {
#                                   "type": "string"
#                               },
#                               "serial_number": {
#                                   "type": "string"
#                               }
#                           }
#                       },
#                       "type": "text/html",
#                       "metadata": {
#                           "qr_entries": [
#                               "qr_code"
#                           ]
#                       },
#                       "example_composition": {
#                           "qr_code": "https://vizidox.com",
#                           "cert_date": "2020-01-12",
#                           "cert_name": "Alan Turing",
#                           "serial_number": "C18009"
#                       },
#                       "tags": [
#                       ]}
#
# TEMPLATE_DETAILS_1_UPDATE = {
#     "schema": {
#         "type": "object",
#         "required": [
#             "cert_name",
#             "serial_number"
#         ],
#         "properties": {
#             "qr_code": {
#                 "type": "string"
#             },
#             "cert_name": {
#                 "type": "string"
#             },
#             "serial_number": {
#                 "type": "string"
#             }
#         }
#     },
#     "type": "text/html",
#     "metadata": {
#         "qr_entries": [
#             "qr_code"
#         ]
#     },
#     "example_composition": {
#         "qr_code": "https://vizidox.com",
#         "cert_date": "2022-01-12",
#         "cert_name": "Ada Lovelace",
#         "serial_number": "D8999"
#     },
#     "tags": [
#     ]}
#
# TEMPLATE_DETAILS_2 = {"title": "template_test_2",
#                       "schema": {
#                           "type": "object",
#                           "required": [
#                               "cert_name",
#                               "serial_number"
#                           ],
#                           "properties": {
#                               "qr_code": {
#                                   "type": "string"
#                               },
#                               "cert_name": {
#                                   "type": "string"
#                               },
#                               "serial_number": {
#                                   "type": "string"
#                               }
#                           }
#                       },
#                       "type": "text/html",
#                       "metadata": {
#                           "qr_entries": [
#                               "qr_code"
#                           ]
#                       },
#                       "example_composition": {
#                           "qr_code": "https://vizidox.com",
#                           "cert_date": "2020-01-12",
#                           "cert_name": "Alan Turing",
#                           "serial_number": "C18009"
#                       },
#                       "tags": [
#                       ]}
#
# TEMPLATE_DETAILS_2_UPDATE = {
#     "schema": {
#         "type": "object",
#         "required": [
#             "cert_name",
#             "serial_number"
#         ],
#         "properties": {
#             "qr_code": {
#                 "type": "string"
#             },
#             "cert_name": {
#                 "type": "string"
#             },
#             "serial_number": {
#                 "type": "string"
#             }
#         }
#     },
#     "type": "text/html",
#     "metadata": {
#         "qr_entries": [
#             "qr_code"
#         ]
#     },
#     "example_composition": {
#         "qr_code": "https://vizidox.com",
#         "cert_date": "2020-01-12",
#         "cert_name": "Alan Turing",
#         "serial_number": "C18009"
#     },
#     "tags": [
#     ]}
#

# @pytest.fixture(scope="function")
# def populate_db_s3(client_s3_storage, db: Session):
#     yield from _fleeting_database(client_s3_storage, db)
#
#
# @pytest.fixture(scope="function")
# def populate_db(client_local_storage, db: Session):
#     yield from _fleeting_database(client_local_storage, db)
#
#
# def _fleeting_database(client, db: Session):
#     with client.application.test_request_context():
#         t = Template(id_=TEMPLATE_ID,
#                      schema={
#                          "type": "object",
#                          "required": [
#                              "cert_name",
#                              "serial_number"
#                          ],
#                          "properties": {
#                              "qr_code": {
#                                  "type": "string"
#                              },
#                              "cert_name": {
#                                  "type": "string"
#                              },
#                              "serial_number": {
#                                  "type": "string"
#                              }
#                          }
#                      },
#                      type_="text/html", metadata={}, example_composition={}, tags=[])
#         db.add(t)
#         db.commit()
#     yield
#     with client.application.test_request_context():
#         db.delete(Template)
#         db.commit()
#
#
# @pytest.fixture(scope="class")
# @mock_s3
# def setup_s3():
#     conn = boto3.resource('s3', region_name='eu-central-1')
#     conn.create_bucket(Bucket=BUCKET_NAME)
#
#
# @pytest.mark.usefixtures("populate_db")
# class TestManageTemplates:
#     CREATE_TEMPLATE_ENDPOINT = '/template/create'
#     UPDATE_TEMPLATE = '/template/{0}/update'
#     UPDATE_TEMPLATE_DETAILS = '/template/{0}/update_details'
#
#     def test_create_new_template_invalid_zip_file(self, client_local_storage):
#         with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
#             template_details_str = json.dumps(TEMPLATE_DETAILS_2)
#             data: dict = {'template_details': template_details_str}
#             if file is not None:
#                 filename = 'invalid_file.zip'
#                 file_payload = (file, filename) if filename is not None else file
#                 data["zipfile"] = file_payload
#             result = client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
#             assert result.status_code == HTTPStatus.BAD_REQUEST
#
#     def test_create_new_template_already_exists(self, client_local_storage):
#         with open(f'{CURRENT_TEST_PATH}/resources/{TEMPLATE_ID}.zip', 'rb') as file:
#             template_details_str = json.dumps(TEMPLATE_DETAILS_1)
#             data: dict = {'template_details': template_details_str}
#             filename = f'{TEMPLATE_ID}.zip'
#             if file is not None:
#                 file_payload = (file, filename) if filename is not None else file
#                 data["zipfile"] = file_payload
#             result = client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
#             assert result.status_code == HTTPStatus.CONFLICT
#
#     def test_create_new_template_invalid_file_type(self, client_local_storage):
#         filename = 'example.pdf'
#         file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
#         template_details_str = json.dumps(TEMPLATE_DETAILS_2)
#         data: dict = {'template_details': template_details_str}
#         if file is not None:
#             file_payload = (file, filename) if filename is not None else file
#             data["zipfile"] = file_payload
#         result = client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
#         assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
#
#     def test_create_new_template_ok(self, client_local_storage):
#         with open(f'{CURRENT_TEST_PATH}/resources/template_test_2.zip', 'rb') as file:
#             template_id = "template_test_2"
#             template_details_str = json.dumps(TEMPLATE_DETAILS_2)
#             data: dict = {'template_details': template_details_str}
#             filename = f'{template_id}.zip'
#             if file is not None:
#                 file_payload = (file, filename) if filename is not None else file
#                 data["zipfile"] = file_payload
#
#             result = client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
#             assert result.status_code == HTTPStatus.CREATED
#             template_model: Template = Template.query.filter_by(id=template_id).one()
#             assert template_model is not None
#
#             expected_template = Template.from_json_dict(TEMPLATE_DETAILS_2)
#             assert template_model.schema == expected_template.schema
#
#     def test_update_template_invalid_zip_file(self, client_local_storage):
#         with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
#             template_details_str = json.dumps(TEMPLATE_DETAILS_2_UPDATE)
#             data: dict = {'template_details': template_details_str}
#
#             if file is not None:
#                 filename = 'invalid_file.zip'
#                 file_payload = (file, filename) if filename is not None else file
#                 data["zipfile"] = file_payload
#             result = client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data)
#             assert result.status_code == HTTPStatus.BAD_REQUEST
#
#     def test_update_template_invalid_details(self, client_local_storage):
#         with open(f'{CURRENT_TEST_PATH}/resources/{TEMPLATE_ID}.zip', 'rb') as file:
#             template_details_str = json.dumps({"user": "Carlos Coda"})
#             data: dict = {'template_details': template_details_str}
#
#             if file is not None:
#                 filename = 'template_test_1.zip'
#                 file_payload = (file, filename) if filename is not None else file
#                 data["zipfile"] = file_payload
#             result = client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data)
#             assert result.status_code == HTTPStatus.BAD_REQUEST
#
#     def test_update_template_invalid_file_type(self, client_local_storage):
#         filename = 'example.pdf'
#         file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
#         template_details_str = json.dumps(TEMPLATE_DETAILS_2)
#         data: dict = {'template_details': template_details_str}
#
#         if file is not None:
#             file_payload = (file, filename) if filename is not None else file
#             data["zipfile"] = file_payload
#
#         result = client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data)
#         assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
#
#     def test_update_template_not_found(self, client_local_storage):
#         template_id = "template_test_2"
#         filename = 'template_test_2.zip'
#         file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
#         template_details_str = json.dumps(TEMPLATE_DETAILS_2)
#         data: dict = {'template_details': template_details_str}
#
#         if file is not None:
#             file_payload = (file, filename) if filename is not None else file
#             data["zipfile"] = file_payload
#
#         result = client_local_storage.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
#         assert result.status_code == HTTPStatus.NOT_FOUND
#
#     def test_update_template_ok(self, client_local_storage):
#         filename = 'template_test_1.zip'
#         file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
#         template_details_str = json.dumps(TEMPLATE_DETAILS_1_UPDATE)
#         data: dict = {'template_details': template_details_str}
#         if file is not None:
#             file_payload = (file, filename) if filename is not None else file
#             data["zipfile"] = file_payload
#         result = client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data)
#         assert result.status_code == HTTPStatus.OK
#         template_model: Template = Template.query.filter_by(id=TEMPLATE_ID).one()
#         assert template_model.example_composition is not None
#         expected_example_composition = {
#             "qr_code": "https://vizidox.com",
#             "cert_date": "2022-01-12",
#             "cert_name": "Ada Lovelace",
#             "serial_number": "D8999"
#         }
#         assert template_model.example_composition == expected_example_composition
#         expected_template = Template.from_json_dict(TEMPLATE_DETAILS_1)
#         assert template_model.schema == expected_template.schema
#
#     def test_update_template_details_not_found(self, client_local_storage):
#         template_id = "template_test_3"
#         data: dict = {'template_details': {"tags": ["test"]}}
#
#         result = client_local_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(template_id), json=data)
#         assert result.status_code == HTTPStatus.NOT_FOUND
#
#     def test_update_template_details_invalid(self, client_local_storage):
#         data: dict = {"user": "invalid"}
#
#         result = client_local_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(TEMPLATE_ID), json=data)
#         assert result.status_code == HTTPStatus.BAD_REQUEST
#
#     def test_update_template_details_ok(self, client_local_storage):
#         example_composition_data = {"qr_code": "https://google.com",
#                                     "cert_date": "2021-01-12",
#                                     "cert_name": "Albert Einstein",
#                                     "serial_number": "C9999"}
#
#         data: dict = {"example_composition": example_composition_data}
#
#         result = client_local_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(TEMPLATE_ID), json=data)
#         assert result.status_code == HTTPStatus.OK
#         template_model: Template = Template.query.filter_by(id=TEMPLATE_ID).one()
#         assert template_model.example_composition is not None
#         assert template_model.example_composition == example_composition_data
#
#
# @pytest.mark.usefixtures("populate_db_s3")
# @pytest.mark.usefixtures("setup_s3")
# @mock_s3
# class TestManageTemplatesS3FileStorage:
#     CREATE_TEMPLATE_ENDPOINT = '/template/create'
#     UPDATE_TEMPLATE = '/template/{0}/update'
#     UPDATE_TEMPLATE_DETAILS = '/template/{0}/update_details'
#
#     def test_create_new_template_ok(self, client_s3_storage):
#         with open(f'{CURRENT_TEST_PATH}/resources/template_test_2.zip', 'rb') as file:
#             template_id = "template_test_2"
#             template_details_str = json.dumps(TEMPLATE_DETAILS_2)
#             data: dict = {'template_details': template_details_str}
#             filename = f'{template_id}.zip'
#             if file is not None:
#                 file_payload = (file, filename) if filename is not None else file
#                 data["zipfile"] = file_payload
#
#             result = client_s3_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
#             assert result.status_code == HTTPStatus.CREATED
#             template_model: Template = Template.query.filter_by(id=template_id).one()
#             assert template_model is not None
#
#             expected_template = Template.from_json_dict(TEMPLATE_DETAILS_2)
#             assert template_model.schema == expected_template.schema
#
#     def test_update_template_ok(self, client_s3_storage):
#         filename = 'template_test_1.zip'
#         file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
#         template_details_str = json.dumps(TEMPLATE_DETAILS_1_UPDATE)
#         data: dict = {'template_details': template_details_str}
#         if file is not None:
#             file_payload = (file, filename) if filename is not None else file
#             data["zipfile"] = file_payload
#         result = client_s3_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data)
#         assert result.status_code == HTTPStatus.OK
#         template_model: Template = Template.query.filter_by(id=TEMPLATE_ID).one()
#         assert template_model.example_composition is not None
#         expected_example_composition = {
#             "qr_code": "https://vizidox.com",
#             "cert_date": "2022-01-12",
#             "cert_name": "Ada Lovelace",
#             "serial_number": "D8999"
#         }
#         assert template_model.example_composition == expected_example_composition
#         expected_template = Template.from_json_dict(TEMPLATE_DETAILS_1)
#         assert template_model.schema == expected_template.schema
#
#     def test_update_template_details_ok(self, client_s3_storage):
#         example_composition_data = {"qr_code": "https://google.com",
#                                     "cert_date": "2021-01-12",
#                                     "cert_name": "Albert Einstein",
#                                     "serial_number": "C9999"}
#
#         data: dict = {"example_composition": example_composition_data}
#
#         result = client_s3_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(TEMPLATE_ID), json=data)
#         assert result.status_code == HTTPStatus.OK
#         template_model: Template = Template.query.filter_by(id=TEMPLATE_ID).one()
#         assert template_model.example_composition is not None
#         assert template_model.example_composition == example_composition_data
