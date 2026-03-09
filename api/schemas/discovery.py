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


# --- Phase 3: Journey Dashboard ---

class JourneyPlaybook(BaseModel):
    slug: str
    title: str
    cover_emoji: str | None = None
    category_name: str = ""
    completed_at: str = ""
    scroll_percent: float = 0.0


class JourneyStampResponse(BaseModel):
    stamp_type: str
    display_name: str
    emoji: str
    description: str
    earned_at: str = ""


class JourneyResponse(BaseModel):
    completed: list[JourneyPlaybook]
    in_progress: list[JourneyPlaybook]
    stamps: list[JourneyStampResponse]
    total_completed: int
    total_published: int
    categories_explored: int
    category_breakdown: dict[str, int]


class CompleteRequest(BaseModel):
    slug: str
    scroll_percent: float = 100.0


class CompleteResponse(BaseModel):
    completed: bool
    new_stamps: list[str]


# --- Phase 4: Constellation + Reading Paths ---

class ConstellationNode(BaseModel):
    slug: str
    title: str
    cover_emoji: str | None = None
    category_name: str = ""
    category_color: str = "#7B4FBF"
    category_slug: str = ""
    is_free: bool = False


class ConstellationEdge(BaseModel):
    source: str  # slug
    target: str  # slug
    connection_type: str
    strength: float = 0.8


class ConstellationResponse(BaseModel):
    nodes: list[ConstellationNode]
    edges: list[ConstellationEdge]


class PathStepResponse(BaseModel):
    slug: str
    title: str
    cover_emoji: str | None = None
    category_name: str = ""
    category_color: str = "#7B4FBF"
    is_free: bool = False
    transition_text: str | None = None


class ReadingPathSummary(BaseModel):
    slug: str
    title: str
    description: str
    theme_tag: str
    emoji: str | None = None
    color: str = "#D4A843"
    step_count: int = 0
    category_names: list[str] = []


class ReadingPathDetail(BaseModel):
    slug: str
    title: str
    description: str
    theme_tag: str
    emoji: str | None = None
    color: str = "#D4A843"
    steps: list[PathStepResponse]


class PathsResponse(BaseModel):
    paths: list[ReadingPathSummary]
