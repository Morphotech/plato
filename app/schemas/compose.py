from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, model_validator, NonNegativeInt

from app.exceptions import AspectRatioCompromisedException


class ComposeBaseSchema(BaseModel):
    page: NonNegativeInt | None = None
    width: NonNegativeInt | None = None
    height: NonNegativeInt | None = None


class ComposeSchema(ComposeBaseSchema):
    page: Annotated[NonNegativeInt, Query(...)] | None = None
    width: Annotated[NonNegativeInt, Query(...)] | None = None
    height: Annotated[NonNegativeInt, Query(...)] | None = None


    @model_validator(mode="after")
    def validate_aspect_ratio(self) -> 'ComposeSchema':
        """
        Validates if the aspect ratio is valid

        :raises ValueError if both width and height are specified
        """
        if self.width is not None and self.height is not None:
            raise ValueError(AspectRatioCompromisedException().detail)
        return self

