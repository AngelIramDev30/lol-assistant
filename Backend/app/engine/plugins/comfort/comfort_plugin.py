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

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        patch = self._normalize_patch(
            str(context.metadata.get("patch") or "")
        )

        role = self._normalize_role(context.role)

        if not patch or role is None:
            return self._neutral(
                "Faltan parche o rol para medir comodidad."
            )

        with SessionLocal() as database:
            repository = PlayerChampionStatRepository(
                database
            )

            stats = repository.get_one(
                profile="current",
                patch=patch,
                queue="420",
                role=role,
                champion_id=champion_id,
            )

        if stats is None:
            return ScoreContribution(
                engine=self.name,
                score=round(42.5 * self.weight, 2),
                reason=(
                    f"No hay historial personal suficiente "
                    f"con {champion_name} en {role}."
                ),
            )

        raw_score = self._calculate_score(
            games=stats.games,
            wins=stats.wins,
            average_kills=stats.average_kills,
            average_deaths=stats.average_deaths,
            average_assists=stats.average_assists,
        )

        confidence = min(
            stats.games / 20.0,
            1.0,
        )

        return ScoreContribution(
            engine=self.name,
            score=round(raw_score * self.weight, 2),
            reason=(
                f"Historial personal: {stats.games} partidas, "
                f"{stats.win_rate:.2f}% WR, "
                f"KDA promedio "
                f"{stats.average_kills:.1f}/"
                f"{stats.average_deaths:.1f}/"
                f"{stats.average_assists:.1f}. "
                f"Confianza {confidence * 100:.0f}%."
            ),
        )

    @staticmethod
    def _calculate_score(
        games: int,
        wins: int,
        average_kills: float,
        average_deaths: float,
        average_assists: float,
    ) -> float:
        adjusted_win_rate = (
            (wins + 5)
            / (games + 10)
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
    def _normalize_patch(patch: str) -> str:
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
