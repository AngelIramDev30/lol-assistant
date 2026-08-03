from typing import Any

from app.services.data_dragon_service import DataDragonService


class ChampionSelectEngine:
    def __init__(self, data_dragon: DataDragonService) -> None:
        self.data_dragon = data_dragon

    def analyze(self, session: dict[str, Any]) -> dict[str, Any]:
        local_player_cell_id = session.get("localPlayerCellId")

        my_team = session.get("myTeam", [])
        their_team = session.get("theirTeam", [])
        actions = session.get("actions", [])

        local_player = self._find_player(
            players=my_team,
            cell_id=local_player_cell_id,
        )

        pick_order = self._calculate_pick_order(
            actions=actions,
            local_player_cell_id=local_player_cell_id,
        )

        return {
            "active": True,
            "patch": self.data_dragon.get_version(),
            "localPlayerCellId": local_player_cell_id,
            "assignedPosition": (
                local_player.get("assignedPosition")
                if local_player
                else None
            ),
            "pickOrder": pick_order,
            "selectedChampion": self._champion_from_player(local_player),
            "allies": [
                self._normalize_player(player)
                for player in my_team
            ],
            "enemies": [
                self._normalize_player(player)
                for player in their_team
            ],
            "bans": self._extract_bans(actions),
        }

    @staticmethod
    def _find_player(
        players: list[dict[str, Any]],
        cell_id: int | None,
    ) -> dict[str, Any] | None:
        for player in players:
            if player.get("cellId") == cell_id:
                return player

        return None

    def _champion_from_player(
        self,
        player: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if player is None:
            return None

        champion_id = player.get("championId", 0)

        if not champion_id:
            return None

        champion = self.data_dragon.get_champion(champion_id)

        return {
            "championId": champion_id,
            "name": champion["name"] if champion else None,
        }

    def _normalize_player(
        self,
        player: dict[str, Any],
    ) -> dict[str, Any]:
        champion_id = player.get("championId", 0)
        champion = (
            self.data_dragon.get_champion(champion_id)
            if champion_id
            else None
        )

        return {
            "cellId": player.get("cellId"),
            "assignedPosition": player.get("assignedPosition"),
            "championId": champion_id or None,
            "championName": (
                champion["name"]
                if champion
                else None
            ),
        }

    @staticmethod
    def _calculate_pick_order(
        actions: list[list[dict[str, Any]]],
        local_player_cell_id: int | None,
    ) -> int | None:
        pick_number = 0

        for action_group in actions:
            for action in action_group:
                if action.get("type") != "pick":
                    continue

                if not action.get("isAllyAction", False):
                    continue

                pick_number += 1

                if action.get("actorCellId") == local_player_cell_id:
                    return pick_number

        return None

    def _extract_bans(
        self,
        actions: list[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        bans: list[dict[str, Any]] = []

        for action_group in actions:
            for action in action_group:
                if action.get("type") != "ban":
                    continue

                champion_id = action.get("championId", 0)

                if not champion_id:
                    continue

                champion = self.data_dragon.get_champion(champion_id)

                bans.append(
                    {
                        "championId": champion_id,
                        "championName": (
                            champion["name"]
                            if champion
                            else None
                        ),
                        "allyBan": action.get("isAllyAction", False),
                        "completed": action.get("completed", False),
                    }
                )

        return bans