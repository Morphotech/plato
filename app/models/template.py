from typing import List, Sequence
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB, ARRAY

from app.db.base_class import Base


class Template(Base):
    """
    Database model for a Template
    The unique identifier for the table is `id`.
    The metadata has some optional but relevant entries:
        qr_entries
            This is an array of JMESPath friendly sequences to represent where in the schema
            are the urls to be transformed into QR codes.
            Examples
                "course.organization.contact.website_url"
    Attributes:
        id (str): The id for the template
        schema (dict): JSON dictionary with jsonschema used for validation in said template
        type (str): MIME type for template type, currently restricted to 'text/html'
        metadata_ (dict): JSON dictionary for arbitrary data useful for owner
        example_composition (dict): A dictionary containing example compose data for the template
        tags (list): A list of identifying tags for the template
    """
    __tablename__ = "template"
    id = Column(String, primary_key=True)
    schema = Column(JSONB, nullable=False)
    type = Column(ENUM("text/html", name="template_mime_type"), nullable=False)
    metadata_ = Column(JSONB, name="metadata", nullable=True)
    example_composition = Column(JSONB, nullable=False)
    tags = Column(ARRAY(String), name="tags", nullable=False, server_default="{}")

    def __init__(self, id_: str, schema: dict, type_: str,
                 metadata: dict,
                 example_composition: dict,
                 tags: Sequence[str]):
        self.id = id_
        self.schema = schema
        self.type = type_
        self.metadata_ = metadata
        self.example_composition = example_composition
        self.tags = tags

    @classmethod
    def from_json_dict(cls, json_: dict) -> 'Template':
        """
        Builds a model from a dictionary that follows the export standard.

        Args:
            json_: dict with template details.

        Returns:
            Template
        """

        return Template(id_=json_["title"],
                        schema=json_["schema"],
                        type_=json_["type"],
                        metadata=json_["metadata"],
                        example_composition=json_["example_composition"],
                        tags=json_["tags"])

    def update_fields(self, json_: dict):
        """
        Updates some fields of a template object from a dictionary. It does not update the template id.

        Args:
            json_: dict with template details.

        Raises a KeyError exception if key does not exist
        """
        for key, value in json_.items():
            if hasattr(self, key) and key not in self.id:
                setattr(self, key, value)
            else:
                raise KeyError(key)

    def json_dict(self) -> dict:
        """
        Exports template data as dict.

        Returns:
            dict
        """
        json_ = dict()
        json_["title"] = self.id
        json_["schema"] = self.schema
        json_["type"] = self.type
        json_["metadata"] = self.metadata_
        json_["example_composition"] = self.example_composition
        json_["tags"] = self.tags
        return json_

    def get_qr_entries(self) -> List[str]:
        """
        Fetches all the qr_entries for the template as a list comprised of JMESPath friendly strings
        Returns:
            List[str]
        """
        return self.metadata_.get("qr_entries", [])

    def __repr__(self):
        return '<Template %r>' % self.id
