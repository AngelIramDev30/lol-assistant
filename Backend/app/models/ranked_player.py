from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.champion_meta import Base


class RankedPlayer(Base):
    __tablename__ = "ranked_players"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    puuid: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    queue: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="RANKED_SOLO_5x5",
        index=True,
    )

    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    division: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    league_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    wins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    losses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    last_match_scan: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
