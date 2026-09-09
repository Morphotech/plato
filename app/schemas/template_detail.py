from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TemplateDetailSchema(BaseModel):
    template_id: str = Field(..., alias="id", serialization_alias="template_id")
    template_schema: dict = Field(
        ..., alias="schema", serialization_alias="template_schema"
    )
    type: str
    metadata: dict = Field(..., alias="metadata_", serialization_alias="metadata")
    tags: set[str]
    example_composition: dict

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class MIMETypeEnum(str, Enum):
    PDF_MIME = "application/pdf"
    HTML_MIME = "text/html"
    OCTET_STREAM = "application/octet-stream"
