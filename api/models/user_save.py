import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class UserSave(Base):
    """A user's explicit bookmark of an interactive widget's state.

    Distinct from WidgetResponse (which stores live, auto-persisted widget
    state). UserSave is a snapshot the reader chose to keep, with enough
    denormalized metadata (titles, preview text) to render the My Saves
    list page without hitting every playbook asset.

    Re-saving the same widget upserts: one row per (user, slug, widget_key)
    holds the latest snapshot and bumps saved_at. Unsave deletes the row.
    """

    __tablename__ = "user_saves"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "playbook_slug",
            "widget_key",
            name="uq_user_saves_user_slug_widget",
        ),
        Index(
            "ix_user_saves_user_saved_at",
            "user_id",
            "saved_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    playbook_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    widget_key: Mapped[str] = mapped_column(String(80), nullable=False)
    widget_title: Mapped[str] = mapped_column(String(160), nullable=False)
    playbook_title: Mapped[str] = mapped_column(String(200), nullable=False)
    preview_text: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
