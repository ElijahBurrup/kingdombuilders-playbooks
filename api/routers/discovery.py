"""
Discovery API — powers the Thread System.

Endpoints:
  GET  /api/v1/discovery/chain/{slug}  — 3 recommendations (deeper, bridge, surprise)
  POST /api/v1/discovery/chain-click   — track which recommendation was clicked
  GET  /api/v1/discovery/tags          — top tags for catalog filter UI
  GET  /api/v1/discovery/surprise      — random playbook from an unexplored category
  GET  /api/v1/discovery/journey       — reading passport (requires auth)
  POST /api/v1/discovery/journey/complete — mark playbook complete + check achievements
  GET  /api/v1/discovery/constellation — all nodes + edges for the graph view
  GET  /api/v1/discovery/paths         — list all reading paths
  GET  /api/v1/discovery/paths/{slug}  — single reading path with steps
"""

import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.database import get_db
from api.dependencies import get_current_user, get_current_user_from_session
from api.models.activity import ReadingProgress
from api.models.playbook import Playbook, Category
from api.models.discovery import PlaybookConnection, PlaybookTag, JourneyStamp, ReadingPath, ReadingPathStep
from api.models.user import User
from api.schemas.discovery import (
    ChainCard, ChainResponse, ChainClickRequest,
    TagInfo, TagsResponse, SurpriseResponse,
    JourneyResponse, JourneyPlaybook, JourneyStampResponse,
    CompleteRequest, CompleteResponse,
    ConstellationNode, ConstellationEdge, ConstellationResponse,
    PathStepResponse, ReadingPathSummary, ReadingPathDetail, PathsResponse,
)
from api.services.journey_service import ACHIEVEMENTS, check_and_award_stamps

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/chain/{slug}", response_model=ChainResponse)
async def get_chain(slug: str, db: AsyncSession = Depends(get_db)):
    """Return up to 3 recommendations for the given playbook slug."""

    # Get the source playbook
    result = await db.execute(
        select(Playbook).where(Playbook.slug == slug)
    )
    source = result.scalar_one_or_none()
    if not source:
        return ChainResponse(current_slug=slug, recommendations=[])

    # Get curated connections with target playbook + category eager-loaded
    conn_result = await db.execute(
        select(PlaybookConnection)
        .where(PlaybookConnection.source_id == source.id)
        .options(
            selectinload(PlaybookConnection.target)
            .selectinload(Playbook.category)
        )
        .order_by(PlaybookConnection.display_order)
    )
    connections = conn_result.scalars().all()

    # Build response — one card per connection type
    seen_types: set[str] = set()
    cards: list[ChainCard] = []

    for conn in connections:
        if conn.connection_type in seen_types:
            continue
        seen_types.add(conn.connection_type)

        target = conn.target
        cat = target.category

        cards.append(ChainCard(
            connection_type=conn.connection_type,
            slug=target.slug,
            title=target.title,
            cover_emoji=target.cover_emoji,
            category_name=cat.name if cat else "",
            category_color=cat.color_text if cat else "#7B4FBF",
            teaser=conn.teaser,
            is_free=target.pricing_type == "free",
        ))

    # If we're missing any connection type, try to fill with tag-based fallback
    for ctype in ("deeper", "bridge", "surprise"):
        if ctype not in seen_types and source:
            fallback = await _tag_based_fallback(
                db, source, ctype,
                exclude_slugs={slug} | {c.slug for c in cards},
            )
            if fallback:
                cards.append(fallback)

    return ChainResponse(current_slug=slug, recommendations=cards)


async def _tag_based_fallback(
    db: AsyncSession,
    source: Playbook,
    connection_type: str,
    exclude_slugs: set[str],
) -> ChainCard | None:
    """Compute a fallback recommendation based on shared tags."""

    # Get source tags
    tag_result = await db.execute(
        select(PlaybookTag.tag, PlaybookTag.weight)
        .where(PlaybookTag.playbook_id == source.id)
    )
    source_tags = {row.tag: row.weight for row in tag_result}

    if not source_tags:
        return None

    # Get all other playbooks with their tags and categories
    pb_result = await db.execute(
        select(Playbook)
        .where(Playbook.slug.notin_(exclude_slugs))
        .where(Playbook.status == "published")
        .options(
            selectinload(Playbook.tags),
            selectinload(Playbook.category),
        )
    )
    candidates = pb_result.scalars().all()

    best: Playbook | None = None
    best_score = -1.0

    for candidate in candidates:
        candidate_tags = {t.tag: t.weight for t in candidate.tags}
        overlap = sum(
            source_tags[t] * candidate_tags[t]
            for t in source_tags
            if t in candidate_tags
        )

        if connection_type == "deeper":
            # Prefer same category, high overlap
            if candidate.category_id == source.category_id and overlap > best_score:
                best = candidate
                best_score = overlap
        elif connection_type == "bridge":
            # Prefer different category, some overlap
            if candidate.category_id != source.category_id and overlap > best_score:
                best = candidate
                best_score = overlap
        elif connection_type == "surprise":
            # Prefer different category, low but nonzero overlap
            if candidate.category_id != source.category_id and 0 < overlap < 2.0:
                score = 1.0 / (1.0 + overlap)  # inverse: less overlap = higher score
                if score > best_score:
                    best = candidate
                    best_score = score

    if not best:
        return None

    cat = best.category
    shared = set(source_tags) & {t.tag for t in best.tags}
    thread = next(iter(shared)) if shared else "a shared thread"
    teasers = {
        "deeper": f"Go further into {cat.name.lower() if cat else 'this topic'}",
        "bridge": f"Connected through {thread}",
        "surprise": f"An unexpected connection through {thread}",
    }

    return ChainCard(
        connection_type=connection_type,
        slug=best.slug,
        title=best.title,
        cover_emoji=best.cover_emoji,
        category_name=cat.name if cat else "",
        category_color=cat.color_text if cat else "#7B4FBF",
        teaser=teasers.get(connection_type, ""),
        is_free=best.pricing_type == "free",
    )


@router.post("/chain-click")
async def track_chain_click(body: ChainClickRequest):
    """Track when a user clicks a chain recommendation (for analytics)."""
    # For now, just acknowledge. Future: store in user_reading_sessions.
    return {"status": "ok"}


@router.get("/tags", response_model=TagsResponse)
async def get_tags(db: AsyncSession = Depends(get_db)):
    """Return top tags used across playbooks, with counts and connected slugs."""

    # Get all tags with their playbook slugs
    result = await db.execute(
        select(
            PlaybookTag.tag,
            func.count(PlaybookTag.id).label("count"),
        )
        .group_by(PlaybookTag.tag)
        .order_by(func.count(PlaybookTag.id).desc())
    )
    tag_counts = [(row.tag, row.count) for row in result]

    # Get slugs per tag for the top tags
    tags: list[TagInfo] = []
    for tag_name, count in tag_counts:
        slug_result = await db.execute(
            select(Playbook.slug)
            .join(PlaybookTag, PlaybookTag.playbook_id == Playbook.id)
            .where(PlaybookTag.tag == tag_name)
            .where(Playbook.status == "published")
        )
        slugs = [row.slug for row in slug_result]
        tags.append(TagInfo(tag=tag_name, count=count, slugs=slugs))

    return TagsResponse(tags=tags)


@router.get("/surprise", response_model=SurpriseResponse)
async def get_surprise(
    exclude: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Return a random playbook, preferring unexplored categories.

    Query param `exclude` is a comma-separated list of slugs the user has already read.
    """
    exclude_slugs = {s.strip() for s in exclude.split(",") if s.strip()}

    # Get all published playbooks with categories
    result = await db.execute(
        select(Playbook)
        .where(Playbook.status == "published")
        .options(selectinload(Playbook.category))
    )
    all_playbooks = result.scalars().all()

    if not all_playbooks:
        return SurpriseResponse(slug="", title="", cover_emoji=None, category_name="", reason="No playbooks available")

    # Separate into read vs unread
    unread = [pb for pb in all_playbooks if pb.slug not in exclude_slugs]
    if not unread:
        unread = all_playbooks  # fallback: all read, pick any

    # Find categories the user has read
    read_categories = {
        pb.category_id for pb in all_playbooks if pb.slug in exclude_slugs
    }

    # Prefer playbooks from unexplored categories
    unexplored = [pb for pb in unread if pb.category_id not in read_categories]

    if unexplored:
        pick = random.choice(unexplored)
        cat = pick.category
        reason = f"You have not explored any {cat.name} playbooks yet" if cat else "Something new for you"
    else:
        pick = random.choice(unread)
        cat = pick.category
        reason = f"A fresh pick from {cat.name}" if cat else "Something different"

    return SurpriseResponse(
        slug=pick.slug,
        title=pick.title,
        cover_emoji=pick.cover_emoji,
        category_name=cat.name if cat else "",
        category_color=cat.color_text if cat else "#7B4FBF",
        is_free=pick.pricing_type == "free",
        reason=reason,
    )


# ============================================================================
# Journey Dashboard
# ============================================================================

@router.get("/journey", response_model=JourneyResponse)
async def get_journey(
    user: User = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's reading passport: completed playbooks, stats, stamps."""

    # Completed playbooks
    progress_result = await db.execute(
        select(ReadingProgress, Playbook)
        .join(Playbook, ReadingProgress.playbook_id == Playbook.id)
        .where(ReadingProgress.user_id == user.id)
        .where(ReadingProgress.completed == True)  # noqa: E712
        .options(selectinload(Playbook.category))
        .order_by(ReadingProgress.last_read_at.desc())
    )
    completed_rows = [(rp, pb) for rp, pb in progress_result]

    completed: list[JourneyPlaybook] = []
    category_counts: dict[str, int] = {}
    for rp, pb in completed_rows:
        cat_name = pb.category.name if pb.category else "Unknown"
        completed.append(JourneyPlaybook(
            slug=pb.slug,
            title=pb.title,
            cover_emoji=pb.cover_emoji,
            category_name=cat_name,
            completed_at=rp.last_read_at.isoformat() if rp.last_read_at else "",
        ))
        category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

    # In-progress playbooks (started but not completed)
    in_progress_result = await db.execute(
        select(ReadingProgress, Playbook)
        .join(Playbook, ReadingProgress.playbook_id == Playbook.id)
        .where(ReadingProgress.user_id == user.id)
        .where(ReadingProgress.completed == False)  # noqa: E712
        .where(ReadingProgress.scroll_percent > 0)
        .options(selectinload(Playbook.category))
        .order_by(ReadingProgress.last_read_at.desc())
    )
    in_progress: list[JourneyPlaybook] = []
    for rp, pb in in_progress_result:
        in_progress.append(JourneyPlaybook(
            slug=pb.slug,
            title=pb.title,
            cover_emoji=pb.cover_emoji,
            category_name=pb.category.name if pb.category else "Unknown",
            scroll_percent=rp.scroll_percent,
        ))

    # Stamps
    stamp_result = await db.execute(
        select(JourneyStamp)
        .where(JourneyStamp.user_id == user.id)
        .order_by(JourneyStamp.earned_at)
    )
    stamps: list[JourneyStampResponse] = []
    for s in stamp_result.scalars():
        info = ACHIEVEMENTS.get(s.stamp_type, (s.stamp_type, "", ""))
        stamps.append(JourneyStampResponse(
            stamp_type=s.stamp_type,
            display_name=info[0],
            emoji=info[1],
            description=info[2],
            earned_at=s.earned_at.isoformat() if s.earned_at else "",
        ))

    # Total published for percentage
    total_result = await db.execute(
        select(func.count(Playbook.id))
        .where(Playbook.status == "published")
    )
    total_published = total_result.scalar() or 0

    return JourneyResponse(
        completed=completed,
        in_progress=in_progress,
        stamps=stamps,
        total_completed=len(completed),
        total_published=total_published,
        categories_explored=len(category_counts),
        category_breakdown=category_counts,
    )


@router.post("/journey/complete", response_model=CompleteResponse)
async def mark_complete(
    body: CompleteRequest,
    user: User = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Mark a playbook as completed and check for new achievement stamps."""

    # Find the playbook
    pb_result = await db.execute(
        select(Playbook).where(Playbook.slug == body.slug)
    )
    playbook = pb_result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Upsert reading progress
    rp_result = await db.execute(
        select(ReadingProgress)
        .where(ReadingProgress.user_id == user.id)
        .where(ReadingProgress.playbook_id == playbook.id)
    )
    rp = rp_result.scalar_one_or_none()

    if rp:
        rp.scroll_percent = max(rp.scroll_percent, body.scroll_percent)
        if body.scroll_percent >= 90:
            rp.completed = True
    else:
        rp = ReadingProgress(
            user_id=user.id,
            playbook_id=playbook.id,
            scroll_percent=body.scroll_percent,
            completed=body.scroll_percent >= 90,
        )
        db.add(rp)

    await db.flush()

    # Check and award stamps
    new_stamps: list[str] = []
    if rp.completed:
        new_stamps = await check_and_award_stamps(user.id, db)

    await db.commit()

    return CompleteResponse(
        completed=rp.completed,
        new_stamps=new_stamps,
    )


# ============================================================================
# Constellation (Graph View)
# ============================================================================

@router.get("/constellation", response_model=ConstellationResponse)
async def get_constellation(db: AsyncSession = Depends(get_db)):
    """Return all published playbooks as nodes and all connections as edges."""

    # Nodes: all published playbooks with categories
    pb_result = await db.execute(
        select(Playbook)
        .where(Playbook.status == "published")
        .options(selectinload(Playbook.category))
    )
    playbooks = pb_result.scalars().all()

    nodes = []
    slug_set: set[str] = set()
    for pb in playbooks:
        cat = pb.category
        nodes.append(ConstellationNode(
            slug=pb.slug,
            title=pb.title,
            cover_emoji=pb.cover_emoji,
            category_name=cat.name if cat else "",
            category_color=cat.color_text if cat else "#7B4FBF",
            category_slug=cat.slug if cat else "",
            is_free=pb.pricing_type == "free",
        ))
        slug_set.add(pb.slug)

    # Edges: all connections between published playbooks
    conn_result = await db.execute(
        select(PlaybookConnection)
        .options(
            selectinload(PlaybookConnection.source),
            selectinload(PlaybookConnection.target),
        )
    )
    connections = conn_result.scalars().all()

    edges = []
    for conn in connections:
        if conn.source.slug in slug_set and conn.target.slug in slug_set:
            edges.append(ConstellationEdge(
                source=conn.source.slug,
                target=conn.target.slug,
                connection_type=conn.connection_type,
                strength=conn.strength,
            ))

    return ConstellationResponse(nodes=nodes, edges=edges)


# ============================================================================
# Reading Paths
# ============================================================================

@router.get("/paths", response_model=PathsResponse)
async def get_paths(db: AsyncSession = Depends(get_db)):
    """Return all reading paths with summary info."""

    result = await db.execute(
        select(ReadingPath)
        .options(
            selectinload(ReadingPath.steps)
            .selectinload(ReadingPathStep.playbook)
            .selectinload(Playbook.category)
        )
        .order_by(ReadingPath.display_order)
    )
    paths = result.scalars().all()

    summaries = []
    for path in paths:
        cat_names = []
        seen_cats: set[str] = set()
        for step in path.steps:
            cat = step.playbook.category
            if cat and cat.name not in seen_cats:
                cat_names.append(cat.name)
                seen_cats.add(cat.name)

        summaries.append(ReadingPathSummary(
            slug=path.slug,
            title=path.title,
            description=path.description,
            theme_tag=path.theme_tag,
            emoji=path.emoji,
            color=path.color,
            step_count=len(path.steps),
            category_names=cat_names,
        ))

    return PathsResponse(paths=summaries)


@router.get("/paths/{slug}", response_model=ReadingPathDetail)
async def get_path(slug: str, db: AsyncSession = Depends(get_db)):
    """Return a single reading path with all steps."""

    result = await db.execute(
        select(ReadingPath)
        .where(ReadingPath.slug == slug)
        .options(
            selectinload(ReadingPath.steps)
            .selectinload(ReadingPathStep.playbook)
            .selectinload(Playbook.category)
        )
    )
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="Reading path not found")

    steps = []
    for step in path.steps:
        pb = step.playbook
        cat = pb.category
        steps.append(PathStepResponse(
            slug=pb.slug,
            title=pb.title,
            cover_emoji=pb.cover_emoji,
            category_name=cat.name if cat else "",
            category_color=cat.color_text if cat else "#7B4FBF",
            is_free=pb.pricing_type == "free",
            transition_text=step.transition_text,
        ))

    return ReadingPathDetail(
        slug=path.slug,
        title=path.title,
        description=path.description,
        theme_tag=path.theme_tag,
        emoji=path.emoji,
        color=path.color,
        steps=steps,
    )
