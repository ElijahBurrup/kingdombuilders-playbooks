import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
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
