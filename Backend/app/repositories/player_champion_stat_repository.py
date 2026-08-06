from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.database.models.player_champion_stat import (
    PlayerChampionStat,
)


class PlayerChampionStatRepository:
    def __init__(self, database: Session) -> None:
        self.database = database

    def upsert_many(
        self,
        rows: list[dict[str, Any]],
    ) -> int:
        if not rows:
            return 0

        now = datetime.now(UTC)

        for row in rows:
            statement = sqlite_insert(
                PlayerChampionStat
            ).values(
                **row,
                updated_at=now,
            )

            statement = statement.on_conflict_do_update(
                index_elements=[
                    "profile",
                    "patch",
                    "queue",
                    "role",
                    "champion_id",
                ],
                set_={
                    "games": statement.excluded.games,
                    "wins": statement.excluded.wins,
                    "win_rate": statement.excluded.win_rate,
                    "average_kills": statement.excluded.average_kills,
                    "average_deaths": statement.excluded.average_deaths,
                    "average_assists": statement.excluded.average_assists,
                    "average_cs": statement.excluded.average_cs,
                    "updated_at": statement.excluded.updated_at,
                },
            )

            self.database.execute(statement)

        self.database.commit()
        return len(rows)

    def get_one(
        self,
        profile: str,
        patch: str,
        queue: str,
        role: str,
        champion_id: int,
    ) -> PlayerChampionStat | None:
        statement = select(PlayerChampionStat).where(
            PlayerChampionStat.profile == profile,
            PlayerChampionStat.patch == patch,
            PlayerChampionStat.queue == queue,
            PlayerChampionStat.role == role,
            PlayerChampionStat.champion_id == champion_id,
        )

        return self.database.scalar(statement)

    def get_recent(
        self,
        profile: str,
        queue: str,
        role: str,
        champion_id: int,
        limit: int = 5,
    ) -> list[PlayerChampionStat]:
        statement = (
            select(PlayerChampionStat)
            .where(
                PlayerChampionStat.profile == profile,
                PlayerChampionStat.queue == queue,
                PlayerChampionStat.role == role,
                PlayerChampionStat.champion_id == champion_id,
            )
            .order_by(
                PlayerChampionStat.updated_at.desc(),
                PlayerChampionStat.patch.desc(),
            )
            .limit(limit)
        )

        return list(
            self.database.scalars(statement).all()
        )
