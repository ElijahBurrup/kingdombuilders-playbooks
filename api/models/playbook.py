import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, nullable=False)
    color_bg: Mapped[str] = mapped_column(
        default="rgba(123,79,191,0.08)",
        server_default=text("'rgba(123,79,191,0.08)'"),
    )
    color_text: Mapped[str] = mapped_column(
        default="#7B4FBF",
        server_default=text("'#7B4FBF'"),
    )
    display_order: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    playbooks: Mapped[list["Playbook"]] = relationship(back_populates="category")


class Series(Base):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    playbooks: Mapped[list["Playbook"]] = relationship(back_populates="series")


class Playbook(Base):
    __tablename__ = "playbooks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(unique=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    subtitle: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    meta_description: Mapped[str | None] = mapped_column(nullable=True)
    og_title: Mapped[str | None] = mapped_column(nullable=True)
    og_description: Mapped[str | None] = mapped_column(nullable=True)
    landing_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_version: Mapped[int] = mapped_column(
        default=1, server_default=text("1")
    )
    pricing_type: Mapped[str] = mapped_column(
        default="paid", server_default=text("'paid'")
    )
    price_cents: Mapped[int] = mapped_column(
        default=250, server_default=text("250")
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
    )
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("series.id"),
        nullable=True,
    )
    series_order: Mapped[int | None] = mapped_column(nullable=True)
    cover_emoji: Mapped[str | None] = mapped_column(nullable=True)
    cover_gradient_start: Mapped[str] = mapped_column(
        default="#1A0A2E", server_default=text("'#1A0A2E'")
    )
    cover_gradient_end: Mapped[str] = mapped_column(
        default="#2D1B4E", server_default=text("'#2D1B4E'")
    )
    status: Mapped[str] = mapped_column(
        default="draft", server_default=text("'draft'")
    )
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    featured: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    view_count: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    purchase_count: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    category: Mapped["Category"] = relationship(back_populates="playbooks")
    series: Mapped["Series | None"] = relationship(back_populates="playbooks")
    assets: Mapped[list["PlaybookAsset"]] = relationship(
        back_populates="playbook", cascade="all, delete-orphan"
    )


class PlaybookAsset(Base):
    __tablename__ = "playbook_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    playbook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(nullable=False)
    file_url: Mapped[str] = mapped_column(nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    playbook: Mapped["Playbook"] = relationship(back_populates="assets")
