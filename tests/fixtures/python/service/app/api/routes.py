import pydantic

from app.domain import obligation_link


class ObligationLinkRequest(pydantic.BaseModel):
    obligation_id: str
    regulation_version: str


LINK = obligation_link.ObligationLink
