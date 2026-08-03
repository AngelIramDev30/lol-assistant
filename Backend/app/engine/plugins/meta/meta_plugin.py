from app.domain.score import ScoreContribution
from app.engine.plugins.base import RecommendationContext, ScoringPlugin


class MetaPlugin(ScoringPlugin):
    name = "meta"
    weight = 0.30

    TEMPORARY_META_SCORES: dict[str, float] = {
        "Kled": 86.0,
        "Jax": 82.0,
        "Ornn": 80.0,
        "Camille": 84.0,
        "Sett": 78.0,
    }

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        raw_score = self.TEMPORARY_META_SCORES.get(
            champion_name,
            65.0,
        )

        weighted_score = raw_score * self.weight

        return ScoreContribution(
            engine=self.name,
            score=round(weighted_score, 2),
            reason=(
                f"Fuerza temporal de meta: {raw_score:.1f}/100."
            ),
        )
