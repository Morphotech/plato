from typing import TYPE_CHECKING, Set

from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    pass


class TemplateDetailSchema(BaseModel):
    template_id: str = Field(..., alias='id', serialization_alias='template_id')
    template_schema: dict = Field(..., alias='schema', serialization_alias='template_schema')
    type: str
    metadata: dict = Field(..., alias='metadata_', serialization_alias='metadata')
    tags: Set[str]
    example_composition: dict

    model_config = ConfigDict(from_attributes=True, extra='forbid')

