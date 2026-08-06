from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.participant import Participant
from app.repositories.player_champion_stat_repository import (
    PlayerChampionStatRepository,
)


@dataclass(frozen=True)
class PlayerStatsResult:
    patch: str
    queue: int
    participants_analyzed: int
    rows_written: int

    def to_dict(self) -> dict:
        return {
            "patch": self.patch,
            "queue": self.queue,
            "participantsAnalyzed": self.participants_analyzed,
            "rowsWritten": self.rows_written,
        }


class PlayerStatsCalculatorService:
    VALID_ROLES = {
        "top",
        "jungle",
        "middle",
        "bottom",
        "utility",
    }

    def __init__(self, database: Session) -> None:
        self.database = database
        self.repository = PlayerChampionStatRepository(
            database
        )

    def calculate(
        self,
        puuid: str,
        patch: str,
        queue: int = 420,
        profile: str = "current",
    ) -> PlayerStatsResult:
        statement = (
            select(
                Participant.role,
                Participant.champion_id,
                func.count(Participant.id).label("games"),
                func.sum(
                    func.cast(Participant.win, Integer)
                ).label("wins"),
                func.avg(Participant.kills).label("average_kills"),
                func.avg(Participant.deaths).label("average_deaths"),
                func.avg(Participant.assists).label("average_assists"),
                func.avg(Participant.cs).label("average_cs"),
            )
            .join(
                Match,
                Match.id == Participant.match_db_id,
            )
            .where(
                Participant.puuid == puuid,
                Participant.role.in_(self.VALID_ROLES),
                Participant.champion_id > 0,
                Match.patch == patch,
                Match.queue == queue,
            )
            .group_by(
                Participant.role,
                Participant.champion_id,
            )
        )

        rows: list[dict] = []
        total_participants = 0

        for result in self.database.execute(statement):
            games = int(result.games or 0)
            wins = int(result.wins or 0)

            if games <= 0:
                continue

            total_participants += games

            rows.append(
                {
                    "profile": profile,
                    "patch": patch,
                    "queue": str(queue),
                    "role": str(result.role),
                    "champion_id": int(result.champion_id),
                    "games": games,
                    "wins": wins,
                    "win_rate": round(
                        wins / games * 100,
                        2,
                    ),
                    "average_kills": round(
                        float(result.average_kills or 0),
                        2,
                    ),
                    "average_deaths": round(
                        float(result.average_deaths or 0),
                        2,
                    ),
                    "average_assists": round(
                        float(result.average_assists or 0),
                        2,
                    ),
                    "average_cs": round(
                        float(result.average_cs or 0),
                        2,
                    ),
                }
            )

        written = self.repository.upsert_many(rows)

        return PlayerStatsResult(
            patch=patch,
            queue=queue,
            participants_analyzed=total_participants,
            rows_written=written,
        )


from sqlalchemy import Integer
