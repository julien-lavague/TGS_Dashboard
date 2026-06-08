from pydantic import BaseModel


class AlertRow(BaseModel):
    email: str
    name: str
    question: str
    is_active: bool
    day: str | None
    time: str | None


class AlertsResponse(BaseModel):
    rows: list[AlertRow]
