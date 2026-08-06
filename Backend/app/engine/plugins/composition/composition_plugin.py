from app.data.champion_traits import has_trait
from app.domain.score import ScoreContribution
from app.engine.plugins.base import (
    RecommendationContext,
    ScoringPlugin,
)


class CompositionPlugin(ScoringPlugin):
    name = "composition"
    weight = 0.20

    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        ally_names = self._get_ally_names(context)

        if not ally_names:
            return self._neutral(
                "Todavía no hay aliados revelados para analizar la composición."
            )

        team_names = ally_names + [champion_name]

        frontline_count = self._count_trait(
            team_names,
            "frontline",
        )
        engage_count = self._count_trait(
            team_names,
            "engage",
        )
        peel_count = self._count_trait(
            team_names,
            "peel",
        )
        magic_count = self._count_trait(
            team_names,
            "magic",
        )
        physical_count = self._count_trait(
            team_names,
            "physical",
        )

        raw_score = 50.0
        reasons: list[str] = []

        ally_frontline = self._count_trait(
            ally_names,
            "frontline",
        )
        ally_engage = self._count_trait(
            ally_names,
            "engage",
        )
        ally_peel = self._count_trait(
            ally_names,
            "peel",
        )
        ally_magic = self._count_trait(
            ally_names,
            "magic",
        )
        ally_physical = self._count_trait(
            ally_names,
            "physical",
        )

        if ally_frontline == 0:
            if has_trait(champion_name, "frontline"):
                raw_score += 14.0
                reasons.append(
                    "Aporta la frontline que falta."
                )
            else:
                raw_score -= 6.0
                reasons.append(
                    "El equipo todavía queda sin frontline clara."
                )

        if ally_engage == 0:
            if has_trait(champion_name, "engage"):
                raw_score += 11.0
                reasons.append(
                    "Añade iniciación al equipo."
                )
            else:
                raw_score -= 4.0

        if ally_peel == 0:
            if has_trait(champion_name, "peel"):
                raw_score += 7.0
                reasons.append(
                    "Añade protección para los carries."
                )

        if ally_physical >= 2 and ally_magic == 0:
            if has_trait(champion_name, "magic"):
                raw_score += 13.0
                reasons.append(
                    "Equilibra una composición cargada de daño físico."
                )
            elif has_trait(champion_name, "physical"):
                raw_score -= 7.0
                reasons.append(
                    "Mantiene al equipo demasiado cargado de daño físico."
                )

        if ally_magic >= 2 and ally_physical == 0:
            if has_trait(champion_name, "physical"):
                raw_score += 13.0
                reasons.append(
                    "Equilibra una composición cargada de daño mágico."
                )
            elif has_trait(champion_name, "magic"):
                raw_score -= 7.0
                reasons.append(
                    "Mantiene al equipo demasiado cargado de daño mágico."
                )

        if frontline_count >= 1:
            raw_score += 2.0

        if engage_count >= 1:
            raw_score += 2.0

        if peel_count >= 1:
            raw_score += 1.0

        if magic_count >= 1 and physical_count >= 1:
            raw_score += 4.0
            reasons.append(
                "La composición conserva daño mixto."
            )

        raw_score = max(
            0.0,
            min(100.0, raw_score),
        )

        if not reasons:
            reasons.append(
                "Ajuste de composición neutral."
            )

        return ScoreContribution(
            engine=self.name,
            score=round(
                raw_score * self.weight,
                2,
            ),
            reason=" ".join(reasons),
        )

    @staticmethod
    def _get_ally_names(
        context: RecommendationContext,
    ) -> list[str]:
        values = context.metadata.get(
            "allyNames",
            [],
        )

        if not isinstance(values, list):
            return []

        return [
            str(value)
            for value in values
            if value
        ]

    @staticmethod
    def _count_trait(
        champions: list[str],
        trait: str,
    ) -> int:
        return sum(
            1
            for champion in champions
            if has_trait(champion, trait)
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
