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


class TagInfo(BaseModel):
    tag: str
    count: int
    slugs: list[str]


class TagsResponse(BaseModel):
    tags: list[TagInfo]


class SurpriseResponse(BaseModel):
    slug: str
    title: str
    cover_emoji: str | None = None
    category_name: str = ""
    category_color: str = "#7B4FBF"
    is_free: bool = False
    reason: str = ""
