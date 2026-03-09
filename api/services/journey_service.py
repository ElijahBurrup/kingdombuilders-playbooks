"""
Journey Service — checks and awards achievement stamps after playbook completion.

Called from the /api/v1/discovery/journey/complete endpoint when a user
finishes reading a playbook (scroll >= 90%).
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.activity import ReadingProgress
from api.models.discovery import JourneyStamp
from api.models.playbook import Playbook, Series


# Achievement definitions: type -> (display_name, emoji, description)
ACHIEVEMENTS = {
    "first_steps": ("First Steps", "\U0001f9ed", "Complete your first playbook"),
    "series_scholar": ("Series Scholar", "\U0001f393", "Complete every playbook in a series"),
    "category_explorer": ("Category Explorer", "\U0001f30d", "Read playbooks from 3 or more categories"),
    "cross_pollinator": ("Cross Pollinator", "\U0001f331", "Read playbooks from 5 or more categories"),
    "deep_diver": ("Deep Diver", "\U0001f30a", "Read 5 or more playbooks in one category"),
    "all_free": ("Open Doors", "\U0001f513", "Read all 5 free playbooks"),
    "ten_complete": ("Double Digits", "\U0001f3af", "Complete 10 playbooks"),
    "twenty_five": ("All In", "\U0001f451", "Complete 25 playbooks"),
}


async def check_and_award_stamps(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> list[str]:
    """Check all achievement conditions and award any newly earned stamps.

    Returns list of newly awarded stamp types (empty if none).
    """
    # Get existing stamps to avoid duplicates
    existing_result = await db.execute(
        select(JourneyStamp.stamp_type)
        .where(JourneyStamp.user_id == user_id)
    )
    existing = {row.stamp_type for row in existing_result}

    # Get completed playbooks with their category info
    progress_result = await db.execute(
        select(ReadingProgress, Playbook)
        .join(Playbook, ReadingProgress.playbook_id == Playbook.id)
        .where(ReadingProgress.user_id == user_id)
        .where(ReadingProgress.completed == True)  # noqa: E712
    )
    completed = [(rp, pb) for rp, pb in progress_result]
    completed_count = len(completed)
    completed_ids = {pb.id for _, pb in completed}
    completed_categories = {pb.category_id for _, pb in completed}

    newly_awarded: list[str] = []

    def award(stamp_type: str, data: dict | None = None):
        if stamp_type not in existing:
            db.add(JourneyStamp(
                user_id=user_id,
                stamp_type=stamp_type,
                stamp_data=data,
            ))
            existing.add(stamp_type)
            newly_awarded.append(stamp_type)

    # --- First Steps ---
    if completed_count >= 1:
        award("first_steps")

    # --- Category Explorer (3+) ---
    if len(completed_categories) >= 3:
        award("category_explorer", {"categories": len(completed_categories)})

    # --- Cross Pollinator (5+) ---
    if len(completed_categories) >= 5:
        award("cross_pollinator", {"categories": len(completed_categories)})

    # --- Deep Diver (5+ in one category) ---
    if "deep_diver" not in existing:
        cat_counts: dict[uuid.UUID, int] = {}
        for _, pb in completed:
            cat_counts[pb.category_id] = cat_counts.get(pb.category_id, 0) + 1
        for cat_id, count in cat_counts.items():
            if count >= 5:
                award("deep_diver", {"category_id": str(cat_id), "count": count})
                break

    # --- Series Scholar (complete all in a series) ---
    if "series_scholar" not in existing:
        # Get all series with their playbook counts
        series_result = await db.execute(
            select(
                Series.id,
                Series.name,
                func.count(Playbook.id).label("total"),
            )
            .join(Playbook, Playbook.series_id == Series.id)
            .where(Playbook.status == "published")
            .group_by(Series.id, Series.name)
        )
        for row in series_result:
            # Count how many in this series the user completed
            series_pb_result = await db.execute(
                select(Playbook.id)
                .where(Playbook.series_id == row.id)
                .where(Playbook.status == "published")
            )
            series_pb_ids = {r.id for r in series_pb_result}
            if series_pb_ids and series_pb_ids.issubset(completed_ids):
                award("series_scholar", {"series": row.name})
                break

    # --- Open Doors (all free playbooks) ---
    if "all_free" not in existing:
        free_result = await db.execute(
            select(Playbook.id)
            .where(Playbook.pricing_type == "free")
            .where(Playbook.status == "published")
        )
        free_ids = {r.id for r in free_result}
        if free_ids and free_ids.issubset(completed_ids):
            award("all_free")

    # --- Double Digits (10) ---
    if completed_count >= 10:
        award("ten_complete", {"count": completed_count})

    # --- All In (25) ---
    if completed_count >= 25:
        award("twenty_five", {"count": completed_count})

    if newly_awarded:
        await db.flush()

    return newly_awarded
