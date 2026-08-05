from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.ranked_player import RankedPlayer


class RankedPlayerRepository:
    def __init__(self, database: Session) -> None:
        self.database = database

    def upsert_many(
        self,
        players: list[dict[str, Any]],
    ) -> int:
        if not players:
            return 0

        now = datetime.now(UTC)

        for player in players:
            statement = sqlite_insert(
                RankedPlayer
            ).values(
                **player,
                updated_at=now,
            )

            statement = statement.on_conflict_do_update(
                index_elements=["puuid"],
                set_={
                    "region": statement.excluded.region,
                    "queue": statement.excluded.queue,
                    "tier": statement.excluded.tier,
                    "division": statement.excluded.division,
                    "league_points": statement.excluded.league_points,
                    "wins": statement.excluded.wins,
                    "losses": statement.excluded.losses,
                    "active": True,
                    "updated_at": statement.excluded.updated_at,
                },
            )

            self.database.execute(statement)

        self.database.commit()
        return len(players)

    def get_active(
        self,
        region: str,
        tier: str | None = None,
        limit: int = 100,
    ) -> list[RankedPlayer]:
        statement = (
            select(RankedPlayer)
            .where(
                RankedPlayer.region == region.lower(),
                RankedPlayer.active.is_(True),
            )
            .order_by(
                RankedPlayer.tier,
                RankedPlayer.division,
                RankedPlayer.league_points.desc(),
            )
            .limit(limit)
        )

        if tier:
            statement = statement.where(
                RankedPlayer.tier == tier.upper()
            )

        return list(
            self.database.scalars(statement).all()
        )

    def mark_scanned(
        self,
        player: RankedPlayer,
    ) -> None:
        player.last_match_scan = datetime.now(UTC)
        self.database.commit()
