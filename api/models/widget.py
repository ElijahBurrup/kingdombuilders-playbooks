import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class WidgetResponse(Base):
    """Per-user state for an interactive widget inside a playbook.

    Each widget on each playbook is identified by (playbook_slug, widget_key).
    For "latest" widgets (diagnostics, calculators) we upsert by
    (user_id, playbook_slug, widget_key) and keep only one row.
    For "diary" widgets we allow many rows per user/widget via the
    history flag, queried in created_at order.
    """

    __tablename__ = "widget_responses"
    __table_args__ = (
        Index(
            "ix_widget_responses_user_playbook_widget",
            "user_id",
            "playbook_slug",
            "widget_key",
        ),
        Index(
            "ix_widget_responses_user_history",
            "user_id",
            "widget_key",
            "created_at",
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
    is_history: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
