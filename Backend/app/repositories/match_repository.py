from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.participant import Participant


class MatchRepository:
    def __init__(self, database: Session) -> None:
        self.database = database

    def get_by_match_id(
        self,
        match_id: str,
    ) -> Match | None:
        return self.database.scalar(
            select(Match).where(
                Match.match_id == match_id
            )
        )

    def exists(self, match_id: str) -> bool:
        return self.get_by_match_id(match_id) is not None

    def save_match(
        self,
        match_data: dict[str, Any],
        region: str,
    ) -> Match:
        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})

        match_id = str(metadata.get("matchId", ""))

        if not match_id:
            raise ValueError(
                "La partida no contiene matchId."
            )

        existing = self.get_by_match_id(match_id)

        if existing is not None:
            return existing

        game_version = str(
            info.get("gameVersion", "unknown")
        )

        patch = self._normalize_patch(game_version)
        game_creation_ms = int(
            info.get("gameCreation", 0)
        )

        match = Match(
            match_id=match_id,
            patch=patch,
            queue=int(info.get("queueId", 0)),
            region=region.lower(),
            duration=int(
                info.get("gameDuration", 0)
            ),
            game_creation=datetime.fromtimestamp(
                game_creation_ms / 1000,
                tz=UTC,
            ),
            processed=False,
        )

        self.database.add(match)
        self.database.flush()

        participants = info.get(
            "participants",
            [],
        )

        if not isinstance(participants, list):
            raise ValueError(
                "La partida no contiene participantes válidos."
            )

        for participant_data in participants:
            if not isinstance(
                participant_data,
                dict,
            ):
                continue

            puuid = str(
                participant_data.get("puuid", "")
            )

            champion_id = int(
                participant_data.get(
                    "championId",
                    0,
                )
            )

            if not puuid or champion_id <= 0:
                continue

            participant = Participant(
                match_db_id=match.id,
                puuid=puuid,
                champion_id=champion_id,
                team_id=int(
                    participant_data.get(
                        "teamId",
                        0,
                    )
                ),
                role=self._normalize_role(
                    participant_data
                ),
                kills=int(
                    participant_data.get(
                        "kills",
                        0,
                    )
                ),
                deaths=int(
                    participant_data.get(
                        "deaths",
                        0,
                    )
                ),
                assists=int(
                    participant_data.get(
                        "assists",
                        0,
                    )
                ),
                gold=int(
                    participant_data.get(
                        "goldEarned",
                        0,
                    )
                ),
                cs=(
                    int(
                        participant_data.get(
                            "totalMinionsKilled",
                            0,
                        )
                    )
                    + int(
                        participant_data.get(
                            "neutralMinionsKilled",
                            0,
                        )
                    )
                ),
                win=bool(
                    participant_data.get(
                        "win",
                        False,
                    )
                ),
            )

            self.database.add(participant)

        self.database.commit()
        self.database.refresh(match)

        return match

    @staticmethod
    def _normalize_patch(
        game_version: str,
    ) -> str:
        parts = game_version.split(".")

        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"

        return game_version

    @staticmethod
    def _normalize_role(
        participant: dict[str, Any],
    ) -> str:
        role = str(
            participant.get("teamPosition")
            or participant.get(
                "individualPosition"
            )
            or "UNKNOWN"
        ).strip().lower()

        aliases = {
            "top": "top",
            "jungle": "jungle",
            "middle": "middle",
            "mid": "middle",
            "bottom": "bottom",
            "bot": "bottom",
            "utility": "utility",
            "support": "utility",
        }

        return aliases.get(role, "unknown")
