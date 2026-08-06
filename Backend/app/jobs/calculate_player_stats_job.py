import json

from sqlalchemy import select

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


def main() -> None:
    _ = PlayerChampionStat
    _ = Match
    _ = Participant

    Base.metadata.create_all(bind=engine)

    league_client = LeagueClient()

    if not league_client.find_lockfile(LEAGUE_PATH):
        raise RuntimeError(
            "Abre League Client antes de calcular tus estadísticas."
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

    puuid = str(account.get("puuid") or "")

    if not puuid:
        raise RuntimeError(
            "Riot no devolvió tu PUUID."
        )

    with SessionLocal() as database:
        latest_patch = database.scalar(
            select(Match.patch)
            .join(
                Participant,
                Participant.match_db_id == Match.id,
            )
            .where(
                Participant.puuid == puuid,
                Match.queue == 420,
            )
            .order_by(Match.game_creation.desc())
            .limit(1)
        )

        if not latest_patch:
            raise RuntimeError(
                "No existen partidas personales guardadas."
            )

        calculator = PlayerStatsCalculatorService(
            database
        )

        result = calculator.calculate(
            puuid=puuid,
            patch=str(latest_patch),
            queue=420,
            profile="current",
        )

    print(
        json.dumps(
            {
                "riotId": f"{game_name}#{tag_line}",
                **result.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
