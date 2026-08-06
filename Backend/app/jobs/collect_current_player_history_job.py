import json

from app.collectors.match_collector import MatchCollector
from app.database.models.champion_meta import Base
from app.database.session import engine
from app.models.match import Match
from app.models.match_dataset import MatchDataset
from app.models.participant import Participant
from app.services.league_client import LeagueClient
from app.services.riot_api_service import RiotApiService


LEAGUE_PATH = r"D:\Riot Games\League of Legends"

MATCH_COUNT = 20
QUEUE_ID = 420
DATASET = "sample_local"


def hide_identifier(value: str) -> str:
    if len(value) <= 16:
        return "***"

    return f"{value[:8]}...{value[-8:]}"


def main() -> None:
    _ = Match
    _ = Participant
    _ = MatchDataset

    Base.metadata.create_all(bind=engine)

    league_client = LeagueClient()

    if not league_client.find_lockfile(LEAGUE_PATH):
        raise RuntimeError(
            "Abre League Client antes de recolectar tu historial."
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
            "League Client no devolvió tu Riot ID."
        )

    riot_api = RiotApiService()

    account = riot_api.get_account_by_riot_id(
        game_name=str(game_name),
        tag_line=str(tag_line),
    )

    puuid = str(account.get("puuid") or "").strip()

    if not puuid:
        raise RuntimeError(
            "ACCOUNT-V1 no devolvió tu PUUID oficial."
        )

    collector = MatchCollector(riot_api)

    result = collector.collect_for_puuid(
        puuid=puuid,
        start=0,
        count=MATCH_COUNT,
        queue=QUEUE_ID,
        delay_seconds=0.35,
        dataset=DATASET,
    )

    print(
        json.dumps(
            {
                "riotId": f"{game_name}#{tag_line}",
                "puuidPreview": hide_identifier(puuid),
                "dataset": DATASET,
                "queue": QUEUE_ID,
                "result": result.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
