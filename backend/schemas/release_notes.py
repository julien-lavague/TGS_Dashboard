from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["major", "minor", "fix"]
Audience = Literal["all", "free", "premium"]


class ReleaseNoteItem(BaseModel):
    category: Category
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    # Public URL of the illustration attached to this line, if any
    image_url: str | None = None


class ReleaseNote(BaseModel):
    id: str
    version: str
    published_at: datetime
    is_important: bool
    audience: Audience
    items: list[ReleaseNoteItem]


class ReleaseNoteCreate(BaseModel):
    version: str = Field(min_length=1, max_length=50)
    published_at: datetime | None = None
    is_important: bool = False
    audience: Audience = "all"
    items: list[ReleaseNoteItem] = []


class ReleaseNoteUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=50)
    published_at: datetime | None = None
    is_important: bool | None = None
    audience: Audience | None = None
    items: list[ReleaseNoteItem] | None = None


class ReleaseNotesResponse(BaseModel):
    rows: list[ReleaseNote]


class ImageUploadResponse(BaseModel):
    image_url: str
