from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    color_bg: str
    color_text: str
    display_order: int
    playbook_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SeriesResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class PlaybookSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    subtitle: str | None
    description: str
    pricing_type: str
    price_cents: int
    category: CategoryResponse | None
    series_name: str | None = None
    series_order: int | None = None
    cover_emoji: str | None
    status: str
    published_at: datetime | None
    featured: bool
    view_count: int
    purchase_count: int

    model_config = ConfigDict(from_attributes=True)


class PlaybookDetail(PlaybookSummary):
    landing_html: str
    has_access: bool = False


class PlaybookContent(BaseModel):
    content_html: str
    content_version: int


class PlaybookListResponse(BaseModel):
    items: list[PlaybookSummary]
    total: int
    page: int
    per_page: int
    pages: int
