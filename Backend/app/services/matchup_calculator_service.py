from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.participant import Participant
from app.repositories.champion_matchup_repository import (
    ChampionMatchupRepository,
)


@dataclass(frozen=True)
class MatchupCalculationResult:
    patch: str
    region: str
    queue: int
    rank: str
    matchups_written: int
    lane_pairs_analyzed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch": self.patch,
            "region": self.region,
            "queue": self.queue,
            "rank": self.rank,
            "matchupsWritten": self.matchups_written,
            "lanePairsAnalyzed": self.lane_pairs_analyzed,
        }


class MatchupCalculatorService:
    VALID_ROLES = {
        "top",
        "jungle",
        "middle",
        "bottom",
        "utility",
    }

    def __init__(self, database: Session) -> None:
        self.database = database
        self.repository = ChampionMatchupRepository(database)

    def calculate(
        self,
        patch: str,
        region: str,
        queue: int = 420,
        rank: str = "sample_local",
    ) -> MatchupCalculationResult:
        statement = (
            select(Match, Participant)
            .join(
                Participant,
                Participant.match_db_id == Match.id,
            )
            .where(
                Match.patch == patch,
                Match.region == region,
                Match.queue == queue,
                Participant.role.in_(self.VALID_ROLES),
                Participant.champion_id > 0,
            )
            .order_by(Match.id)
        )

        matches: dict[int, dict[str, list[Participant]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for match, participant in self.database.execute(statement):
            matches[match.id][participant.role].append(participant)

        aggregates: dict[
            tuple[str, int, int],
            dict[str, float],
        ] = defaultdict(
            lambda: {
                "games": 0,
                "wins": 0,
                "gold_diff_total": 0.0,
                "cs_diff_total": 0.0,
                "kill_diff_total": 0.0,
            }
        )

        lane_pairs = 0

        for roles in matches.values():
            for role, participants in roles.items():
                if len(participants) != 2:
                    continue

                first, second = participants

                if first.team_id == second.team_id:
                    continue

                lane_pairs += 1

                self._add_pair(
                    aggregates=aggregates,
                    role=role,
                    player=first,
                    enemy=second,
                )

                self._add_pair(
                    aggregates=aggregates,
                    role=role,
                    player=second,
                    enemy=first,
                )

        rows: list[dict[str, Any]] = []

        for (
            role,
            champion_id,
            enemy_champion_id,
        ), values in aggregates.items():
            games = int(values["games"])
            wins = int(values["wins"])

            if games <= 0:
                continue

            rows.append(
                {
                    "patch": patch,
                    "region": region,
                    "queue": str(queue),
                    "role": role,
                    "rank": rank,
                    "champion_id": champion_id,
                    "enemy_champion_id": enemy_champion_id,
                    "games": games,
                    "wins": wins,
                    "win_rate": round(
                        wins / games * 100,
                        2,
                    ),
                    "gold_diff": round(
                        values["gold_diff_total"] / games,
                        2,
                    ),
                    "cs_diff": round(
                        values["cs_diff_total"] / games,
                        2,
                    ),
                    "kill_diff": round(
                        values["kill_diff_total"] / games,
                        2,
                    ),
                }
            )

        written = self.repository.upsert_many(rows)

        return MatchupCalculationResult(
            patch=patch,
            region=region,
            queue=queue,
            rank=rank,
            matchups_written=written,
            lane_pairs_analyzed=lane_pairs,
        )

    @staticmethod
    def _add_pair(
        aggregates: dict,
        role: str,
        player: Participant,
        enemy: Participant,
    ) -> None:
        key = (
            role,
            player.champion_id,
            enemy.champion_id,
        )

        values = aggregates[key]

        values["games"] += 1
        values["wins"] += int(player.win)
        values["gold_diff_total"] += player.gold - enemy.gold
        values["cs_diff_total"] += player.cs - enemy.cs
        values["kill_diff_total"] += player.kills - enemy.kills
