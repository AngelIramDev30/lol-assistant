import json

from app.database.models.champion_meta import Base
from app.database.session import SessionLocal, engine
from app.models.ranked_player import RankedPlayer
from app.repositories.ranked_player_repository import (
    RankedPlayerRepository,
)
from app.services.riot_api_service import RiotApiService


TIER = "EMERALD"
DIVISION = "I"
PAGE = 1
PLAYER_LIMIT = 25
QUEUE = "RANKED_SOLO_5x5"


def hide_identifier(value: str) -> str:
    if len(value) <= 12:
        return "***"

    return f"{value[:6]}...{value[-6:]}"


def main() -> None:
    _ = RankedPlayer
    Base.metadata.create_all(bind=engine)

    riot_api = RiotApiService()

    entries = riot_api.get_ranked_entries(
        tier=TIER,
        division=DIVISION,
        page=PAGE,
        queue=QUEUE,
    )

    players_to_store: list[dict] = []
    previews: list[dict] = []
    failures = 0

    for entry in entries[:PLAYER_LIMIT]:
        try:
            puuid = str(
                entry.get("puuid") or ""
            ).strip()

            if not puuid:
                summoner_id = entry.get("summonerId")

                if not summoner_id:
                    failures += 1
                    continue

                summoner = riot_api.get_summoner_by_id(
                    str(summoner_id)
                )

                puuid = str(
                    summoner.get("puuid") or ""
                ).strip()

            if not puuid:
                failures += 1
                continue

            player = {
                "puuid": puuid,
                "region": riot_api.platform_region,
                "queue": QUEUE,
                "tier": str(
                    entry.get("tier") or TIER
                ).upper(),
                "division": str(
                    entry.get("rank") or DIVISION
                ).upper(),
                "league_points": int(
                    entry.get("leaguePoints", 0)
                ),
                "wins": int(entry.get("wins", 0)),
                "losses": int(entry.get("losses", 0)),
                "active": True,
            }

            players_to_store.append(player)

            previews.append(
                {
                    "tier": player["tier"],
                    "division": player["division"],
                    "leaguePoints": player["league_points"],
                    "wins": player["wins"],
                    "losses": player["losses"],
                    "puuidPreview": hide_identifier(puuid),
                }
            )

        except Exception as error:
            failures += 1
            print(
                "[ERROR] "
                f"{type(error).__name__}: {error}"
            )

    with SessionLocal() as database:
        repository = RankedPlayerRepository(database)

        stored = repository.upsert_many(
            players_to_store
        )

    print(
        json.dumps(
            {
                "region": riot_api.platform_region,
                "tier": TIER,
                "division": DIVISION,
                "page": PAGE,
                "entriesReceived": len(entries),
                "playersResolved": len(players_to_store),
                "playersStored": stored,
                "failures": failures,
                "players": previews,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
