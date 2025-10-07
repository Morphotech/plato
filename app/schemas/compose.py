from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, model_validator, NonNegativeInt

from app.exceptions import AspectRatioCompromisedException, NegativePageNumberException


class ComposeBaseSchema(BaseModel):
    page: int | None
    width: int | None
    height: int | None


class ComposeSchema(ComposeBaseSchema):
    page: Annotated[NonNegativeInt, Query(...)] | None = None
    width: Annotated[NonNegativeInt, Query(...)] | None = None
    height: Annotated[NonNegativeInt, Query(...)] | None = None


    @model_validator(mode="after")
    def validate_aspect_ratio(self) -> 'ComposeSchema':
        """
        Validates if the aspect ratio is valid

        :raises AspectRatioCompromisedException if both width and height are specified
        """
        if self.width is not None and self.height is not None:
            raise AspectRatioCompromisedException()
        return self

    @model_validator(mode="after")
    def validate_negative_page_number(self) -> 'ComposeSchema': # is this needed now that we have NonNegativeInt?
        """
        Validates if the page number is not negative

        :raises NegativePageNumberException if the page number is negative
        """
        if self.page is not None and self.page < 0:
            raise NegativePageNumberException(self.page)
        return self
