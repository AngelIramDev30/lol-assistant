import json
from dataclasses import asdict, dataclass

from app.collectors.match_collector import MatchCollector
from app.database.models.champion_meta import Base
from app.database.session import SessionLocal, engine
from app.models.match import Match
from app.models.participant import Participant
from app.models.ranked_player import RankedPlayer
from app.repositories.ranked_player_repository import (
    RankedPlayerRepository,
)
from app.services.riot_api_service import RiotApiService


REGION = "la1"
TIER = "EMERALD"
PLAYER_LIMIT = 5
MATCHES_PER_PLAYER = 3
QUEUE_ID = 420


@dataclass
class RankedCollectionSummary:
    players_requested: int = 0
    players_scanned: int = 0
    players_failed: int = 0
    matches_requested: int = 0
    matches_downloaded: int = 0
    matches_stored: int = 0
    matches_skipped: int = 0
    matches_failed: int = 0


def main() -> None:
    _ = Match
    _ = Participant
    _ = RankedPlayer

    Base.metadata.create_all(bind=engine)

    riot_api = RiotApiService()
    collector = MatchCollector(riot_api)

    summary = RankedCollectionSummary()

    with SessionLocal() as database:
        player_repository = RankedPlayerRepository(
            database
        )

        players = player_repository.get_next_to_scan(
            region=REGION,
            tier=TIER,
            limit=PLAYER_LIMIT,
        )

        summary.players_requested = len(players)

        for index, player in enumerate(players, start=1):
            preview = (
                f"{player.puuid[:6]}..."
                f"{player.puuid[-6:]}"
            )

            print(
                f"\nJugador {index}/{len(players)} "
                f"{player.tier} {player.division} "
                f"{player.league_points} LP "
                f"({preview})"
            )

            try:
                result = collector.collect_for_puuid(
                    puuid=player.puuid,
                    start=0,
                    count=MATCHES_PER_PLAYER,
                    queue=QUEUE_ID,
                    delay_seconds=0.35,
                )

                summary.matches_requested += (
                    result.requested
                )
                summary.matches_downloaded += (
                    result.downloaded
                )
                summary.matches_stored += result.stored
                summary.matches_skipped += result.skipped
                summary.matches_failed += result.failed

                player_repository.mark_scanned(player)
                summary.players_scanned += 1

            except Exception as error:
                database.rollback()
                summary.players_failed += 1

                print(
                    "[ERROR JUGADOR] "
                    f"{type(error).__name__}: {error}"
                )

    print()
    print(
        json.dumps(
            {
                "dataset": "emerald_collection_test",
                "region": REGION,
                "tier": TIER,
                "queue": QUEUE_ID,
                "matchesPerPlayer": MATCHES_PER_PLAYER,
                "summary": asdict(summary),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
