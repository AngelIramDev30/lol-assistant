from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import urllib3


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


@dataclass
class LockfileData:
    process: str
    pid: int
    port: int
    password: str
    protocol: str


class LeagueClient:
    def __init__(self) -> None:
        self.lockfile: LockfileData | None = None

    def find_lockfile(self, league_path: str) -> bool:
        lockfile_path = Path(league_path) / "lockfile"

        if not lockfile_path.is_file():
            self.lockfile = None
            return False

        try:
            content = lockfile_path.read_text(
                encoding="utf-8"
            ).strip()

            process, pid, port, password, protocol = (
                content.split(":", maxsplit=4)
            )

            self.lockfile = LockfileData(
                process=process,
                pid=int(pid),
                port=int(port),
                password=password,
                protocol=protocol.lower(),
            )

            return True

        except (OSError, ValueError):
            self.lockfile = None
            return False

    def info(self) -> dict[str, str | int] | None:
        if self.lockfile is None:
            return None

        return {
            "process": self.lockfile.process,
            "pid": self.lockfile.pid,
            "port": self.lockfile.port,
            "protocol": self.lockfile.protocol,
        }

    def request(
        self,
        method: str,
        endpoint: str,
        timeout: float = 5.0,
    ) -> Any:
        if self.lockfile is None:
            raise RuntimeError(
                "League Client no está conectado. "
                "Ejecuta find_lockfile primero."
            )

        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        url = (
            f"{self.lockfile.protocol}://127.0.0.1:"
            f"{self.lockfile.port}{endpoint}"
        )

        response = requests.request(
            method=method,
            url=url,
            auth=("riot", self.lockfile.password),
            verify=False,
            timeout=timeout,
        )

        response.raise_for_status()

        if not response.content:
            return None

        content_type = response.headers.get(
            "content-type",
            "",
        ).lower()

        if "application/json" in content_type:
            return response.json()

        return response.text

    def get_current_summoner(self) -> dict[str, Any]:
        data = self.request(
            method="GET",
            endpoint="/lol-summoner/v1/current-summoner",
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "El cliente devolvió un perfil inválido."
            )

        return data

    def get_gameflow_phase(self) -> str:
        data = self.request(
            method="GET",
            endpoint="/lol-gameflow/v1/gameflow-phase",
        )

        if not isinstance(data, str):
            raise RuntimeError(
                "El cliente devolvió una fase inválida."
            )

        return data

    def get_champion_select_session(
        self,
    ) -> dict[str, Any] | None:
        try:
            data = self.request(
                method="GET",
                endpoint="/lol-champ-select/v1/session",
            )

        except requests.HTTPError as error:
            if (
                error.response is not None
                and error.response.status_code == 404
            ):
                return None

            raise

        if not isinstance(data, dict):
            return None

        return data

    def get_owned_champions(
        self,
    ) -> list[dict[str, Any]]:
        try:
            data = self.request(
                method="GET",
                endpoint=(
                    "/lol-champions/v1/"
                    "owned-champions-minimal"
                ),
            )

        except requests.HTTPError as error:
            response = error.response

            if (
                response is None
                or response.status_code != 404
            ):
                raise

            profile = self.get_current_summoner()
            summoner_id = profile.get("summonerId")

            if summoner_id is None:
                raise RuntimeError(
                    "No se pudo obtener el summonerId."
                ) from error

            data = self.request(
                method="GET",
                endpoint=(
                    "/lol-champions/v1/inventories/"
                    f"{summoner_id}/champions-minimal"
                ),
            )

        if not isinstance(data, list):
            raise RuntimeError(
                "El cliente devolvió una lista "
                "de campeones inválida."
            )

        owned: list[dict[str, Any]] = []

        for champion in data:
            if not isinstance(champion, dict):
                continue

            ownership = champion.get("ownership", {})

            if not isinstance(ownership, dict):
                continue

            if ownership.get("owned", False):
                owned.append(champion)

        return owned

    def get_owned_champion_ids(self) -> set[int]:
        champions = self.get_owned_champions()
        champion_ids: set[int] = set()

        for champion in champions:
            champion_id = champion.get("id")

            if champion_id is None:
                continue

            try:
                champion_ids.add(int(champion_id))
            except (TypeError, ValueError):
                continue

        return champion_ids
