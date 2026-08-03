from app.domain.score import ScoreContribution
from app.engine.plugins.base import RecommendationContext, ScoringPlugin


class MatchupPlugin(ScoringPlugin):
    name = "matchup"
    weight = 0.25

    TEMPORARY_MATCHUPS: dict[tuple[str, str], float] = {
        ("Kled", "Renekton"): 7.0,
        ("Kled", "Fiora"): -9.0,
        ("Jax", "Camille"): 5.0,
        ("Ornn", "Renekton"): 3.0,
        ("Sett", "Renekton"): 2.0,
    }

    TEMPORARY_NAMES_BY_ID: dict[int, str] = {
        58: "Renekton",
        114: "Fiora",
        164: "Camille",
    }

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        if not context.enemy_champion_ids:
            return ScoreContribution(
                engine=self.name,
                score=12.5,
                reason=(
                    "Todavía no se conoce el rival de línea; "
                    "se aplica puntuación neutral."
                ),
            )

        matchup_adjustment = 0.0
        explanations: list[str] = []

        for enemy_id in context.enemy_champion_ids:
            enemy_name = self.TEMPORARY_NAMES_BY_ID.get(enemy_id)

            if enemy_name is None:
                continue

            adjustment = self.TEMPORARY_MATCHUPS.get(
                (champion_name, enemy_name),
                0.0,
            )

            matchup_adjustment += adjustment

            if adjustment != 0:
                sign = "+" if adjustment > 0 else ""
                explanations.append(
                    f"{champion_name} vs {enemy_name}: "
                    f"{sign}{adjustment:.0f}"
                )

        base_score = 50.0
        raw_score = max(
            0.0,
            min(100.0, base_score + matchup_adjustment),
        )

        weighted_score = raw_score * self.weight

        reason = (
            "; ".join(explanations)
            if explanations
            else "No hay datos temporales para este matchup."
        )

        return ScoreContribution(
            engine=self.name,
            score=round(weighted_score, 2),
            reason=reason,
        )
