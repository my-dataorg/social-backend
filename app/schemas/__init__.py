from typing import Any

from datetime import datetime

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    venueId: str | None = None


class PostOut(BaseModel):
    id: str
    venueId: str | None = None
    authorId: str
    body: str
    type: str = "text"
    metadata: dict[str, Any] | None = None
    createdAt: datetime


class PostPage(BaseModel):
    items: list[PostOut]
    nextCursor: str | None = None
    totalApprox: int
