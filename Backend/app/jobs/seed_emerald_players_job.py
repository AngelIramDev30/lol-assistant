import json

from app.services.riot_api_service import RiotApiService


TIER = "EMERALD"
DIVISION = "I"
PAGE = 1
PLAYER_LIMIT = 5


def hide_identifier(value: str) -> str:
    if len(value) <= 12:
        return "***"

    return f"{value[:6]}...{value[-6:]}"


def main() -> None:
    riot_api = RiotApiService()

    entries = riot_api.get_ranked_entries(
        tier=TIER,
        division=DIVISION,
        page=PAGE,
        queue="RANKED_SOLO_5x5",
    )

    players: list[dict] = []
    failures = 0

    for entry in entries[:PLAYER_LIMIT]:
        try:
            # League-V4 puede entregar el PUUID directamente.
            puuid = str(entry.get("puuid") or "").strip()

            # Respaldo para respuestas antiguas que todav?a
            # incluyan summonerId.
            if not puuid:
                summoner_id = entry.get("summonerId")

                if not summoner_id:
                    failures += 1
                    print(
                        "[ERROR] La entrada no contiene "
                        "puuid ni summonerId."
                    )
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

            players.append(
                {
                    "tier": entry.get("tier"),
                    "rank": entry.get("rank"),
                    "leaguePoints": int(
                        entry.get("leaguePoints", 0)
                    ),
                    "wins": int(entry.get("wins", 0)),
                    "losses": int(entry.get("losses", 0)),
                    "puuidPreview": hide_identifier(puuid),
                }
            )

        except Exception as error:
            failures += 1
            print(
                "[ERROR] "
                f"{type(error).__name__}: {error}"
            )

    print(
        json.dumps(
            {
                "region": riot_api.platform_region,
                "tier": TIER,
                "division": DIVISION,
                "page": PAGE,
                "entriesReceived": len(entries),
                "playersResolved": len(players),
                "failures": failures,
                "players": players,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
