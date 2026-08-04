from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChampionMeta(Base):
    __tablename__ = "champion_meta"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    patch: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    queue: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    rank: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    champion_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    games: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    wins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    win_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    pick_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "patch",
            "region",
            "queue",
            "role",
            "rank",
            "champion_id",
            name="uq_champion_meta_context",
        ),
    )
