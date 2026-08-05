from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.champion_meta import Base


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    match_db_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    puuid: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    champion_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    kills: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    deaths: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    assists: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    gold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    cs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    win: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "match_db_id",
            "puuid",
            name="uq_participant_match_puuid",
        ),
    )
