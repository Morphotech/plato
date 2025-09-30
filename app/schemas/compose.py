from typing import Annotated

from fastapi import Query, Header
from pydantic import BaseModel


class ComposeBaseSchema(BaseModel):
    page: int | None
    width: int | None
    height: int | None


class ComposeSchema(ComposeBaseSchema):
    page: Annotated[int, Query(...)] | None = None
    width: Annotated[int, Query(...)] | None = None
    height: Annotated[int, Query(...)] | None = None