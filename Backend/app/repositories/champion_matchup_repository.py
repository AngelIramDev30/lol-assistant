from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.database.models.champion_matchup import ChampionMatchup


class ChampionMatchupRepository:
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
                ChampionMatchup
            ).values(
                **row,
                updated_at=now,
            )

            statement = statement.on_conflict_do_update(
                index_elements=[
                    "patch",
                    "region",
                    "queue",
                    "role",
                    "rank",
                    "champion_id",
                    "enemy_champion_id",
                ],
                set_={
                    "games": statement.excluded.games,
                    "wins": statement.excluded.wins,
                    "win_rate": statement.excluded.win_rate,
                    "gold_diff": statement.excluded.gold_diff,
                    "cs_diff": statement.excluded.cs_diff,
                    "kill_diff": statement.excluded.kill_diff,
                    "updated_at": statement.excluded.updated_at,
                },
            )

            self.database.execute(statement)

        self.database.commit()
        return len(rows)

    def get_one(
        self,
        patch: str,
        region: str,
        queue: str,
        role: str,
        rank: str,
        champion_id: int,
        enemy_champion_id: int,
    ) -> ChampionMatchup | None:
        statement = select(ChampionMatchup).where(
            ChampionMatchup.patch == patch,
            ChampionMatchup.region == region,
            ChampionMatchup.queue == queue,
            ChampionMatchup.role == role,
            ChampionMatchup.rank == rank,
            ChampionMatchup.champion_id == champion_id,
            ChampionMatchup.enemy_champion_id == enemy_champion_id,
        )

        return self.database.scalar(statement)
