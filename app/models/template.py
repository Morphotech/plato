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


    def get_qr_entries(self) -> List[str]:
        """
        Fetches all the qr_entries for the template as a list comprised of JMESPath friendly strings
        Returns:
            List[str]
        """
        return self.metadata_.get("qr_entries", [])

    def __repr__(self):
        return '<Template %r>' % self.id
