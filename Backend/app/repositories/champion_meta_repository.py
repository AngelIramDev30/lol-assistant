from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.database.models.champion_meta import ChampionMeta


class ChampionMetaRepository:
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
            values = {
                **row,
                "updated_at": now,
            }

            statement = sqlite_insert(
                ChampionMeta
            ).values(**values)

            statement = statement.on_conflict_do_update(
                index_elements=[
                    "patch",
                    "region",
                    "queue",
                    "role",
                    "rank",
                    "champion_id",
                ],
                set_={
                    "games": statement.excluded.games,
                    "wins": statement.excluded.wins,
                    "win_rate": statement.excluded.win_rate,
                    "pick_rate": statement.excluded.pick_rate,
                    "updated_at": statement.excluded.updated_at,
                },
            )

            self.database.execute(statement)

        self.database.commit()
        return len(rows)

    def get_for_context(
        self,
        patch: str,
        region: str,
        queue: str,
        role: str,
        rank: str,
    ) -> list[ChampionMeta]:
        statement = (
            select(ChampionMeta)
            .where(
                ChampionMeta.patch == patch,
                ChampionMeta.region == region,
                ChampionMeta.queue == queue,
                ChampionMeta.role == role,
                ChampionMeta.rank == rank,
            )
            .order_by(
                ChampionMeta.win_rate.desc(),
                ChampionMeta.games.desc(),
            )
        )

        return list(
            self.database.scalars(statement).all()
        )
