from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.champion_meta import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    match_id: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        unique=True,
        index=True,
    )

    patch: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    queue: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    game_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
