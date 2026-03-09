from pydantic import BaseModel


class ChainCard(BaseModel):
    connection_type: str
    slug: str
    title: str
    cover_emoji: str | None
    category_name: str
    category_color: str
    teaser: str
    is_free: bool


class ChainResponse(BaseModel):
    current_slug: str
    recommendations: list[ChainCard]


class ChainClickRequest(BaseModel):
    slug: str
    target_slug: str
    connection_type: str
