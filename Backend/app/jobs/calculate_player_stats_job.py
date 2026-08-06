import json

from sqlalchemy import distinct, select

from app.database.models.champion_meta import Base
from app.database.models.player_champion_stat import (
    PlayerChampionStat,
)
from app.database.session import SessionLocal, engine
from app.models.match import Match
from app.models.participant import Participant
from app.services.league_client import LeagueClient
from app.services.player_stats_calculator_service import (
    PlayerStatsCalculatorService,
)
from app.services.riot_api_service import RiotApiService


LEAGUE_PATH = r"D:\Riot Games\League of Legends"
QUEUE_ID = 420


def main() -> None:
    _ = PlayerChampionStat
    _ = Match
    _ = Participant

    Base.metadata.create_all(bind=engine)

    league_client = LeagueClient()

    if not league_client.find_lockfile(LEAGUE_PATH):
        raise RuntimeError(
            "Abre League Client antes de calcular "
            "tus estadísticas."
        )

    profile = league_client.get_current_summoner()

    game_name = (
        profile.get("gameName")
        or profile.get("displayName")
    )

    tag_line = (
        profile.get("tagLine")
        or profile.get("tagline")
    )

    if not game_name or not tag_line:
        raise RuntimeError(
            "No se pudo obtener tu Riot ID."
        )

    riot_api = RiotApiService()

    account = riot_api.get_account_by_riot_id(
        game_name=str(game_name),
        tag_line=str(tag_line),
    )

    puuid = str(account.get("puuid") or "").strip()

    if not puuid:
        raise RuntimeError(
            "Riot no devolvió tu PUUID oficial."
        )

    results: list[dict] = []
    total_participants = 0
    total_rows = 0

    with SessionLocal() as database:
        patches = list(
            database.scalars(
                select(distinct(Match.patch))
                .join(
                    Participant,
                    Participant.match_db_id == Match.id,
                )
                .where(
                    Participant.puuid == puuid,
                    Match.queue == QUEUE_ID,
                )
                .order_by(Match.patch.desc())
            ).all()
        )

        if not patches:
            raise RuntimeError(
                "No existen partidas personales guardadas."
            )

        calculator = PlayerStatsCalculatorService(
            database
        )

        for patch in patches:
            result = calculator.calculate(
                puuid=puuid,
                patch=str(patch),
                queue=QUEUE_ID,
                profile="current",
            )

            total_participants += (
                result.participants_analyzed
            )
            total_rows += result.rows_written

            results.append(result.to_dict())

    print(
        json.dumps(
            {
                "riotId": f"{game_name}#{tag_line}",
                "patchesProcessed": len(results),
                "participantsAnalyzed": total_participants,
                "rowsWritten": total_rows,
                "patches": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
