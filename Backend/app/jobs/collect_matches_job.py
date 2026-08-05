import json

from app.collectors.match_collector import MatchCollector
from app.database.models.champion_meta import Base
from app.database.session import engine
from app.models.match import Match
from app.models.participant import Participant
from app.services.league_client import LeagueClient
from app.services.riot_api_service import RiotApiService


LEAGUE_PATH = r"D:\Riot Games\League of Legends"


def main() -> None:
    _ = Match
    _ = Participant

    Base.metadata.create_all(bind=engine)

    league_client = LeagueClient()

    if not league_client.find_lockfile(LEAGUE_PATH):
        raise RuntimeError(
            "Abre League Client antes de ejecutar el collector."
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
            "El cliente no devolvi? gameName y tagLine. "
            "Revisa GET /league/profile."
        )

    riot_api = RiotApiService()

    account = riot_api.get_account_by_riot_id(
        game_name=str(game_name),
        tag_line=str(tag_line),
    )

    puuid = account.get("puuid")

    if not puuid:
        raise RuntimeError(
            "ACCOUNT-V1 no devolvi? un PUUID v?lido."
        )

    collector = MatchCollector(riot_api)

    result = collector.collect_for_puuid(
        puuid=str(puuid),
        count=5,
        queue=420,
    )

    print(
        json.dumps(
            {
                "riotId": f"{game_name}#{tag_line}",
                "result": result.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
