from typing import NamedTuple, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models.template import Template


class TemplateDetailView(NamedTuple):
    """
    Template Detail
    ---
    properties:
        template_id:
            type: string
            description: template id
        template_schema:
            type: object
            description: jsonschema for template
        type:
            type: string
            description: template MIME type
        metadata:
            type: object
            description: a collection on property values defined by the resource owner at the template conception
        tags:
            type: array
            items:
                type: string
        example_composition:
            type: object
            description: a dictionary containing example compose data for the template
    """
    template_id: str
    template_schema: dict
    type: str
    metadata: dict
    tags: Sequence[str]
    example_composition: dict

    @classmethod
    def view_from_template(cls, template: 'Template') -> 'TemplateDetailView':
        """
        Takes a template model and creates a TemplateDetailView.

        Args:
            template: the target template

        Returns:
            TemplateDetailView: A view for the template
        """
        return TemplateDetailView(template_id=template.id,
                                  template_schema=template.schema,
                                  type=template.type,
                                  metadata=template.metadata_,
                                  tags=template.tags,
                                  example_composition=template.example_composition)


TEMPLATE_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "schema": {
            "type": "object"
        },
        "type": {
            "type": "string"
        },
        "metadata": {
            "type": "object"
        },
        "example_composition": {
            "type": "object"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "schema",
        "type",
        "metadata",
        "example_composition",
        "tags"
    ]
}
