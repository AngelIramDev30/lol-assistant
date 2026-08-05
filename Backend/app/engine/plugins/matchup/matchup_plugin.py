import os

from app.database.session import SessionLocal
from app.domain.score import ScoreContribution
from app.engine.plugins.base import (
    RecommendationContext,
    ScoringPlugin,
)
from app.repositories.champion_matchup_repository import (
    ChampionMatchupRepository,
)


class MatchupPlugin(ScoringPlugin):
    name = "matchup"
    weight = 0.25

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        if not context.enemy_champion_ids:
            return self._neutral(
                "No hay campeones enemigos revelados."
            )

        patch = self._normalize_patch(
            str(context.metadata.get("patch") or "")
        )
        role = self._normalize_role(context.role)

        region = str(
            context.metadata.get("region")
            or os.getenv("RIOT_REGION", "la1")
        ).lower()

        queue = str(
            context.metadata.get("queue") or "420"
        )

        rank = str(
            context.metadata.get("rank")
            or "sample_local"
        ).lower()

        enemy_names = context.metadata.get(
            "enemyNamesById",
            {},
        )

        if not patch or role is None:
            return self._neutral(
                "Faltan parche o rol para consultar matchups."
            )

        contributions: list[float] = []
        explanations: list[str] = []

        with SessionLocal() as database:
            repository = ChampionMatchupRepository(database)

            for enemy_id in context.enemy_champion_ids:
                stats = repository.get_one(
                    patch=patch,
                    region=region,
                    queue=queue,
                    role=role,
                    rank=rank,
                    champion_id=champion_id,
                    enemy_champion_id=enemy_id,
                )

                enemy_name = str(
                    enemy_names.get(
                        str(enemy_id),
                        enemy_names.get(
                            enemy_id,
                            f"ID {enemy_id}",
                        ),
                    )
                )

                if stats is None:
                    continue

                raw_score = self._calculate_raw_score(
                    games=stats.games,
                    wins=stats.wins,
                    gold_diff=stats.gold_diff,
                    cs_diff=stats.cs_diff,
                    kill_diff=stats.kill_diff,
                )

                contributions.append(raw_score)

                confidence = min(
                    stats.games / 30.0,
                    1.0,
                )

                explanations.append(
                    f"{champion_name} vs {enemy_name}: "
                    f"{stats.games} partidas, "
                    f"{stats.win_rate:.2f}% WR, "
                    f"oro {stats.gold_diff:+.0f}, "
                    f"CS {stats.cs_diff:+.1f}, "
                    f"kills {stats.kill_diff:+.1f}. "
                    f"Confianza {confidence * 100:.0f}%."
                )

        if not contributions:
            return self._neutral(
                "No existen datos guardados para los "
                "matchups enemigos actuales."
            )

        combined_raw_score = sum(contributions) / len(
            contributions
        )

        return ScoreContribution(
            engine=self.name,
            score=round(
                combined_raw_score * self.weight,
                2,
            ),
            reason=" | ".join(explanations),
        )

    @staticmethod
    def _calculate_raw_score(
        games: int,
        wins: int,
        gold_diff: float,
        cs_diff: float,
        kill_diff: float,
    ) -> float:
        # Suavizado: agrega 10 partidas virtuales al 50%.
        adjusted_win_rate = (
            (wins + 5)
            / (games + 10)
            * 100
        )

        win_component = adjusted_win_rate * 0.70

        gold_component = max(
            -10.0,
            min(10.0, gold_diff / 500.0),
        )

        cs_component = max(
            -5.0,
            min(5.0, cs_diff / 10.0),
        )

        kill_component = max(
            -5.0,
            min(5.0, kill_diff * 1.5),
        )

        sample_component = min(
            games / 30.0,
            1.0,
        ) * 5.0

        raw_score = (
            win_component
            + 25.0
            + gold_component
            + cs_component
            + kill_component
            + sample_component
        )

        return max(
            0.0,
            min(100.0, raw_score),
        )

    def _neutral(
        self,
        reason: str,
    ) -> ScoreContribution:
        return ScoreContribution(
            engine=self.name,
            score=round(50.0 * self.weight, 2),
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
        if role is None:
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
