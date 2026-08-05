from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.participant import Participant
from app.repositories.champion_meta_repository import (
    ChampionMetaRepository,
)


@dataclass(frozen=True)
class MetaCalculationResult:
    patch: str
    region: str
    queue: int
    rank: str
    rows_written: int
    participants_analyzed: int

    def to_dict(self) -> dict:
        return {
            "patch": self.patch,
            "region": self.region,
            "queue": self.queue,
            "rank": self.rank,
            "rowsWritten": self.rows_written,
            "participantsAnalyzed": self.participants_analyzed,
        }


class MetaCalculatorService:
    VALID_ROLES = {
        "top",
        "jungle",
        "middle",
        "bottom",
        "utility",
    }

    def __init__(self, database: Session) -> None:
        self.database = database
        self.repository = ChampionMetaRepository(database)

    def calculate(
        self,
        patch: str,
        region: str,
        queue: int = 420,
        rank: str = "sample_local",
    ) -> MetaCalculationResult:
        participants_analyzed = self._count_participants(
            patch=patch,
            region=region,
            queue=queue,
        )

        rows: list[dict] = []

        for role in sorted(self.VALID_ROLES):
            rows.extend(
                self._calculate_role(
                    patch=patch,
                    region=region,
                    queue=queue,
                    role=role,
                    rank=rank,
                )
            )

        rows_written = self.repository.upsert_many(rows)

        return MetaCalculationResult(
            patch=patch,
            region=region,
            queue=queue,
            rank=rank,
            rows_written=rows_written,
            participants_analyzed=participants_analyzed,
        )

    def _calculate_role(
        self,
        patch: str,
        region: str,
        queue: int,
        role: str,
        rank: str,
    ) -> list[dict]:
        total_role_slots = self.database.scalar(
            select(func.count(Participant.id))
            .join(
                Match,
                Match.id == Participant.match_db_id,
            )
            .where(
                Match.patch == patch,
                Match.region == region,
                Match.queue == queue,
                Participant.role == role,
            )
        ) or 0

        if total_role_slots == 0:
            return []

        statement = (
            select(
                Participant.champion_id,
                func.count(Participant.id).label("games"),
                func.sum(
                    func.cast(Participant.win, Integer)
                ).label("wins"),
            )
            .join(
                Match,
                Match.id == Participant.match_db_id,
            )
            .where(
                Match.patch == patch,
                Match.region == region,
                Match.queue == queue,
                Participant.role == role,
                Participant.champion_id > 0,
            )
            .group_by(Participant.champion_id)
        )

        rows: list[dict] = []

        for champion_id, games, wins in self.database.execute(
            statement
        ):
            games_value = int(games or 0)
            wins_value = int(wins or 0)

            if games_value <= 0:
                continue

            win_rate = round(
                wins_value / games_value * 100,
                2,
            )

            pick_rate = round(
                games_value / total_role_slots * 100,
                2,
            )

            rows.append(
                {
                    "patch": patch,
                    "region": region,
                    "queue": str(queue),
                    "role": role,
                    "rank": rank,
                    "champion_id": int(champion_id),
                    "games": games_value,
                    "wins": wins_value,
                    "win_rate": win_rate,
                    "pick_rate": pick_rate,
                }
            )

        return rows

    def _count_participants(
        self,
        patch: str,
        region: str,
        queue: int,
    ) -> int:
        value = self.database.scalar(
            select(func.count(Participant.id))
            .join(
                Match,
                Match.id == Participant.match_db_id,
            )
            .where(
                Match.patch == patch,
                Match.region == region,
                Match.queue == queue,
            )
        )

        return int(value or 0)


# Import aqu? para mantener visible el tipo usado por SQLAlchemy.
from sqlalchemy import Integer
