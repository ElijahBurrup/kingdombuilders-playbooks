import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class PlaybookTag(Base):
    __tablename__ = "playbook_tags"
    __table_args__ = (
        UniqueConstraint("playbook_id", "tag", name="uq_playbook_tag"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    playbook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(nullable=False, index=True)
    weight: Mapped[float] = mapped_column(
        Float, default=1.0, server_default=text("1.0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    playbook: Mapped["Playbook"] = relationship(  # noqa: F821
        back_populates="tags",
    )


class PlaybookConnection(Base):
    __tablename__ = "playbook_connections"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "target_id", "connection_type",
            name="uq_playbook_connection",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_type: Mapped[str] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    teaser: Mapped[str] = mapped_column(nullable=False)
    strength: Mapped[float] = mapped_column(
        Float, default=0.8, server_default=text("0.8")
    )
    display_order: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    source: Mapped["Playbook"] = relationship(  # noqa: F821
        foreign_keys=[source_id],
        back_populates="outgoing_connections",
    )
    target: Mapped["Playbook"] = relationship(  # noqa: F821
        foreign_keys=[target_id],
        back_populates="incoming_connections",
    )


class JourneyStamp(Base):
    __tablename__ = "journey_stamps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stamp_type: Mapped[str] = mapped_column(nullable=False)
    stamp_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    earned_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()  # noqa: F821


class ReadingPath(Base):
    __tablename__ = "reading_paths"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(unique=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    theme_tag: Mapped[str] = mapped_column(nullable=False)
    emoji: Mapped[str | None] = mapped_column(nullable=True)
    color: Mapped[str] = mapped_column(
        default="#D4A843", server_default=text("'#D4A843'")
    )
    display_order: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    steps: Mapped[list["ReadingPathStep"]] = relationship(
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="ReadingPathStep.step_order",
    )


class ReadingPathStep(Base):
    __tablename__ = "reading_path_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reading_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    playbook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    transition_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    path: Mapped["ReadingPath"] = relationship(back_populates="steps")
    playbook: Mapped["Playbook"] = relationship()  # noqa: F821
