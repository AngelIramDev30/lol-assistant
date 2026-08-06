import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env", override=True)


class RiotApiService:
    def __init__(self) -> None:
        self.api_key = (
            os.getenv("RIOT_API_KEY") or ""
        ).strip()

        self.platform_region = os.getenv(
            "RIOT_REGION",
            "la1",
        ).strip().lower()

        self.routing_region = os.getenv(
            "RIOT_ROUTING_REGION",
            "americas",
        ).strip().lower()

        if not self.api_key:
            raise RuntimeError(
                "RIOT_API_KEY no está configurada "
                "en Backend/.env."
            )

    def _request(
        self,
        host: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        max_attempts: int = 4,
    ) -> Any:
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        url = (
            f"https://{host}.api.riotgames.com"
            f"{endpoint}"
        )

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(
                    url=url,
                    headers={
                        "X-Riot-Token": self.api_key,
                    },
                    params=params,
                    timeout=20,
                )

            except requests.RequestException as error:
                last_error = error

                if attempt >= max_attempts:
                    raise RuntimeError(
                        "No se pudo conectar con Riot API "
                        f"después de {max_attempts} intentos."
                    ) from error

                wait_seconds = min(
                    2 ** (attempt - 1),
                    8,
                )

                print(
                    "[RIOT API] Error de red. "
                    f"Reintento en {wait_seconds}s..."
                )

                time.sleep(wait_seconds)
                continue

            if response.status_code == 200:
                if not response.content:
                    return None

                return response.json()

            if response.status_code == 401:
                raise RuntimeError(
                    "Riot no recibió credenciales válidas. "
                    "Revisa RIOT_API_KEY."
                )

            if response.status_code == 403:
                raise RuntimeError(
                    "La Riot API Key expiró, fue revocada "
                    "o no tiene acceso a este endpoint."
                )

            if response.status_code == 404:
                raise RuntimeError(
                    "Riot no encontró el recurso solicitado."
                )

            if response.status_code == 429:
                retry_after_header = response.headers.get(
                    "Retry-After",
                    "2",
                )

                try:
                    retry_after = max(
                        float(retry_after_header),
                        1.0,
                    )
                except ValueError:
                    retry_after = 2.0

                rate_limit_type = response.headers.get(
                    "X-Rate-Limit-Type",
                    "unknown",
                )

                if attempt >= max_attempts:
                    raise RuntimeError(
                        "Se alcanzó el rate limit de Riot "
                        f"({rate_limit_type}) y se agotaron "
                        "los reintentos."
                    )

                print(
                    "[RIOT API] Rate limit "
                    f"({rate_limit_type}). "
                    f"Esperando {retry_after:.1f}s..."
                )

                time.sleep(retry_after)
                continue

            if 500 <= response.status_code < 600:
                if attempt >= max_attempts:
                    response.raise_for_status()

                wait_seconds = min(
                    2 ** (attempt - 1),
                    8,
                )

                print(
                    "[RIOT API] Error temporal "
                    f"{response.status_code}. "
                    f"Reintento en {wait_seconds}s..."
                )

                time.sleep(wait_seconds)
                continue

            try:
                error_body = response.json()
            except ValueError:
                error_body = response.text

            raise RuntimeError(
                "Riot API devolvió "
                f"HTTP {response.status_code}: "
                f"{error_body}"
            )

        if last_error is not None:
            raise RuntimeError(
                "Riot API no respondió correctamente."
            ) from last_error

        raise RuntimeError(
            "Riot API no respondió correctamente."
        )

    def get_account_by_riot_id(
        self,
        game_name: str,
        tag_line: str,
    ) -> dict[str, Any]:
        encoded_game_name = quote(
            game_name,
            safe="",
        )
        encoded_tag_line = quote(
            tag_line,
            safe="",
        )

        data = self._request(
            host=self.routing_region,
            endpoint=(
                "/riot/account/v1/accounts/by-riot-id/"
                f"{encoded_game_name}/{encoded_tag_line}"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Riot devolvió una cuenta inválida."
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
            params={
                "page": page,
            },
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "Riot devolvió entradas "
                "clasificatorias inválidas."
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
                f"{quote(summoner_id, safe='')}"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Riot devolvió un invocador inválido."
            )

        return data

    def get_match_ids(
        self,
        puuid: str,
        start: int = 0,
        count: int = 10,
        queue: int | None = 420,
    ) -> list[str]:
        if count < 1 or count > 100:
            raise ValueError(
                "count debe estar entre 1 y 100."
            )

        params: dict[str, Any] = {
            "start": max(start, 0),
            "count": count,
        }

        if queue is not None:
            params["queue"] = queue

        data = self._request(
            host=self.routing_region,
            endpoint=(
                "/lol/match/v5/matches/by-puuid/"
                f"{quote(puuid, safe='')}/ids"
            ),
            params=params,
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "Riot devolvió una lista "
                "de partidas inválida."
            )

        return [
            str(match_id)
            for match_id in data
        ]

    def get_match(
        self,
        match_id: str,
    ) -> dict[str, Any]:
        data = self._request(
            host=self.routing_region,
            endpoint=(
                "/lol/match/v5/matches/"
                f"{quote(match_id, safe='')}"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Riot devolvió una partida inválida."
            )

        return data
