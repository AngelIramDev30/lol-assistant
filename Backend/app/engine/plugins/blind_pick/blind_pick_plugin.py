from app.domain.score import ScoreContribution
from app.engine.plugins.base import RecommendationContext, ScoringPlugin


class BlindPickPlugin(ScoringPlugin):
    name = "blind_pick"
    weight = 0.20

    TEMPORARY_BLIND_SCORES: dict[str, float] = {
        "Kled": 82.0,
        "Jax": 72.0,
        "Ornn": 91.0,
        "Camille": 76.0,
        "Sett": 80.0,
    }

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        raw_score = self.TEMPORARY_BLIND_SCORES.get(
            champion_name,
            60.0,
        )

        is_early_pick = (
            context.pick_order is not None
            and context.pick_order <= 2
        )

        if not is_early_pick:
            raw_score = min(raw_score + 5.0, 100.0)

        weighted_score = raw_score * self.weight

        reason = (
            "Selección temprana: se prioriza seguridad."
            if is_early_pick
            else "Selección tardía: menor riesgo de counter."
        )

        return ScoreContribution(
            engine=self.name,
            score=round(weighted_score, 2),
            reason=f"{reason} Blind score: {raw_score:.1f}/100.",
        )
