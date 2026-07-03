from pydantic import BaseModel


class UsersListResponse(BaseModel):
    segments: dict[str, list[str]]


class AnonymousStatsResponse(BaseModel):
    session_count: int
    page_view_count: int
    last_seen: str | None
