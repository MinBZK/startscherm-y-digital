from pydantic import BaseModel, Field


class LinkResponse(BaseModel):
    url: str
