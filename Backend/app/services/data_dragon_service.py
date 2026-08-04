from typing import Any

import requests


class DataDragonService:
    VERSIONS_URL = (
        "https://ddragon.leagueoflegends.com/api/versions.json"
    )

    def __init__(self, locale: str = "es_MX") -> None:
        self.locale = locale
        self.version: str | None = None
        self.champions_by_id: dict[int, dict[str, Any]] = {}

    def load_champions(self) -> None:
        version_response = requests.get(
            self.VERSIONS_URL,
            timeout=10,
        )
        version_response.raise_for_status()

        versions = version_response.json()

        if not isinstance(versions, list) or not versions:
            raise RuntimeError(
                "Data Dragon no devolvió versiones válidas."
            )

        self.version = versions[0]

        champions_url = (
            "https://ddragon.leagueoflegends.com/cdn/"
            f"{self.version}/data/{self.locale}/champion.json"
        )

        champions_response = requests.get(
            champions_url,
            timeout=10,
        )
        champions_response.raise_for_status()

        payload = champions_response.json()
        champions = payload.get("data", {})

        self.champions_by_id = {
            int(champion["key"]): {
                "id": champion["id"],
                "name": champion["name"],
                "title": champion["title"],
                "image": champion["image"]["full"],
            }
            for champion in champions.values()
        }

    def ensure_loaded(self) -> None:
        if not self.champions_by_id:
            self.load_champions()

    def get_champion(
        self,
        champion_id: int,
    ) -> dict[str, Any] | None:
        self.ensure_loaded()
        return self.champions_by_id.get(champion_id)

    def get_champion_name(
        self,
        champion_id: int,
    ) -> str | None:
        champion = self.get_champion(champion_id)

        if champion is None:
            return None

        return str(champion["name"])

    def get_version(self) -> str:
        self.ensure_loaded()

        if self.version is None:
            raise RuntimeError(
                "No se pudo determinar la versión."
            )

        return self.version

    def get_all_champions(self) -> list[dict[str, Any]]:
        self.ensure_loaded()

        return [
            {
                "championId": champion_id,
                "championName": champion["name"],
            }
            for champion_id, champion
            in self.champions_by_id.items()
        ]
