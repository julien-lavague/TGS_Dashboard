from pydantic import BaseModel


class UsersListResponse(BaseModel):
    segments: dict[str, list[str]]
