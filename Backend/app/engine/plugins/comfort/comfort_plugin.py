from app.database.session import SessionLocal
from app.domain.score import ScoreContribution
from app.engine.plugins.base import (
    RecommendationContext,
    ScoringPlugin,
)
from app.repositories.player_champion_stat_repository import (
    PlayerChampionStatRepository,
)


class ComfortPlugin(ScoringPlugin):
    name = "comfort"
    weight = 0.20

    PATCH_WEIGHTS = [
        1.00,
        0.80,
        0.65,
        0.50,
        0.40,
    ]

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        current_patch = self._normalize_patch(
            str(context.metadata.get("patch") or "")
        )

        role = self._normalize_role(context.role)

        if not current_patch or role is None:
            return self._neutral(
                "Faltan parche o rol para medir comodidad."
            )

        with SessionLocal() as database:
            repository = PlayerChampionStatRepository(
                database
            )

            stats_rows = repository.get_recent(
                profile="current",
                queue="420",
                role=role,
                champion_id=champion_id,
                limit=len(self.PATCH_WEIGHTS),
            )

        if not stats_rows:
            return ScoreContribution(
                engine=self.name,
                score=round(42.5 * self.weight, 2),
                reason=(
                    f"No hay historial personal con "
                    f"{champion_name} en {role}."
                ),
            )

        aggregate = self._aggregate(stats_rows)

        raw_score = self._calculate_score(
            games=aggregate["effective_games"],
            wins=aggregate["effective_wins"],
            average_kills=aggregate["average_kills"],
            average_deaths=aggregate["average_deaths"],
            average_assists=aggregate["average_assists"],
        )

        confidence = min(
            aggregate["effective_games"] / 20.0,
            1.0,
        )

        patches = ", ".join(
            str(row.patch)
            for row in stats_rows
        )

        return ScoreContribution(
            engine=self.name,
            score=round(raw_score * self.weight, 2),
            reason=(
                f"Historial personal ponderado: "
                f"{aggregate['real_games']} partidas reales, "
                f"{aggregate['win_rate']:.2f}% WR, "
                f"KDA promedio "
                f"{aggregate['average_kills']:.1f}/"
                f"{aggregate['average_deaths']:.1f}/"
                f"{aggregate['average_assists']:.1f}. "
                f"Parches usados: {patches}. "
                f"Confianza {confidence * 100:.0f}%."
            ),
        )

    def _aggregate(
        self,
        rows: list,
    ) -> dict[str, float | int]:
        effective_games = 0.0
        effective_wins = 0.0

        weighted_kills = 0.0
        weighted_deaths = 0.0
        weighted_assists = 0.0

        real_games = 0
        real_wins = 0

        for index, row in enumerate(rows):
            weight = self.PATCH_WEIGHTS[
                min(index, len(self.PATCH_WEIGHTS) - 1)
            ]

            weighted_games = row.games * weight

            effective_games += weighted_games
            effective_wins += row.wins * weight

            weighted_kills += (
                row.average_kills * weighted_games
            )
            weighted_deaths += (
                row.average_deaths * weighted_games
            )
            weighted_assists += (
                row.average_assists * weighted_games
            )

            real_games += row.games
            real_wins += row.wins

        denominator = max(effective_games, 1.0)

        return {
            "effective_games": effective_games,
            "effective_wins": effective_wins,
            "real_games": real_games,
            "real_wins": real_wins,
            "win_rate": (
                real_wins / max(real_games, 1) * 100
            ),
            "average_kills": (
                weighted_kills / denominator
            ),
            "average_deaths": (
                weighted_deaths / denominator
            ),
            "average_assists": (
                weighted_assists / denominator
            ),
        }

    @staticmethod
    def _calculate_score(
        games: float,
        wins: float,
        average_kills: float,
        average_deaths: float,
        average_assists: float,
    ) -> float:
        adjusted_win_rate = (
            (wins + 5.0)
            / (games + 10.0)
            * 100
        )

        kda = (
            average_kills + average_assists
        ) / max(average_deaths, 1.0)

        kda_bonus = min(
            max((kda - 2.0) * 5.0, -8.0),
            12.0,
        )

        experience_bonus = min(
            games / 20.0,
            1.0,
        ) * 12.0

        score = (
            adjusted_win_rate
            + kda_bonus
            + experience_bonus
        )

        return max(0.0, min(100.0, score))

    def _neutral(
        self,
        reason: str,
    ) -> ScoreContribution:
        return ScoreContribution(
            engine=self.name,
            score=round(47.5 * self.weight, 2),
            reason=reason,
        )

    @staticmethod
    def _normalize_patch(
        patch: str,
    ) -> str:
        parts = patch.split(".")

        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"

        return patch

    @staticmethod
    def _normalize_role(
        role: str | None,
    ) -> str | None:
        if not role:
            return None

        aliases = {
            "top": "top",
            "jungle": "jungle",
            "middle": "middle",
            "mid": "middle",
            "bottom": "bottom",
            "bot": "bottom",
            "adc": "bottom",
            "utility": "utility",
            "support": "utility",
        }

        return aliases.get(role.strip().lower())
