import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchases.id", ondelete="SET NULL"),
        nullable=True,
    )
    playbook_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(nullable=True)
    user_agent: Mapped[str | None] = mapped_column(nullable=True)
    platform: Mapped[str | None] = mapped_column(nullable=True)
    downloaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User | None"] = relationship()
    purchase: Mapped["Purchase | None"] = relationship()
    playbook: Mapped["Playbook"] = relationship()


class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "playbook_id", name="uq_reading_progress_user_playbook"),
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
    playbook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    scroll_percent: Mapped[float] = mapped_column(
        default=0.0, server_default=text("0")
    )
    completed: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    downloaded: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    last_chapter: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    last_read_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
    playbook: Mapped["Playbook"] = relationship()


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "playbook_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    playbook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
    playbook: Mapped["Playbook"] = relationship()
