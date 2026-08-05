import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env", override=True)


class RiotApiService:
    def __init__(self) -> None:
        self.api_key = os.getenv("RIOT_API_KEY")
        self.platform_region = os.getenv(
            "RIOT_REGION",
            "la1",
        ).lower()

        self.routing_region = os.getenv(
            "RIOT_ROUTING_REGION",
            "americas",
        ).lower()

        if not self.api_key:
            raise RuntimeError(
                "RIOT_API_KEY no est? configurada en Backend/.env."
            )

    def _request(
        self,
        host: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:

        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        response = requests.get(
            url=f"https://{host}.api.riotgames.com{endpoint}",
            headers={
                "X-Riot-Token": self.api_key,
            },
            params=params,
            timeout=15,
        )

        if response.status_code == 401:
            raise RuntimeError(
                "La Riot API Key es inv?lida."
            )

        if response.status_code == 403:
            raise RuntimeError(
                "La Riot API Key expir?."
            )

        if response.status_code == 429:
            raise RuntimeError(
                "Rate limit de Riot alcanzado."
            )

        response.raise_for_status()

        if not response.content:
            return None

        return response.json()

    def get_account_by_riot_id(
        self,
        game_name: str,
        tag_line: str,
    ) -> dict[str, Any]:

        data = self._request(
            host=self.routing_region,
            endpoint=(
                "/riot/account/v1/accounts/by-riot-id/"
                f"{game_name}/{tag_line}"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Respuesta inv?lida."
            )

        return data

    def get_ranked_entries(
        self,
        tier: str = "EMERALD",
        division: str = "I",
        page: int = 1,
        queue: str = "RANKED_SOLO_5x5",
    ) -> list[dict[str, Any]]:
        data = self._request(
            host=self.platform_region,
            endpoint=(
                f"/lol/league/v4/entries/{queue}/"
                f"{tier.upper()}/{division.upper()}"
            ),
            params={"page": page},
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "Riot devolvi? entradas clasificatorias inv?lidas."
            )

        return [
            entry
            for entry in data
            if isinstance(entry, dict)
        ]

    def get_summoner_by_id(
        self,
        summoner_id: str,
    ) -> dict[str, Any]:
        data = self._request(
            host=self.platform_region,
            endpoint=(
                "/lol/summoner/v4/summoners/"
                f"{summoner_id}"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Riot devolvi? un invocador inv?lido."
            )

        return data
    def get_match_ids(
        self,
        puuid: str,
        start: int = 0,
        count: int = 10,
        queue: int | None = 420,
    ) -> list[str]:

        params: dict[str, Any] = {
            "start": start,
            "count": count,
        }

        if queue is not None:
            params["queue"] = queue

        data = self._request(
            host=self.routing_region,
            endpoint=f"/lol/match/v5/matches/by-puuid/{puuid}/ids",
            params=params,
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "Respuesta inv?lida."
            )

        return [str(match) for match in data]

    def get_match(
        self,
        match_id: str,
    ) -> dict[str, Any]:

        data = self._request(
            host=self.routing_region,
            endpoint=f"/lol/match/v5/matches/{match_id}",
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Respuesta inv?lida."
            )

        return data

