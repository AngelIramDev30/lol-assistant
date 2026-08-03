from app.domain.score import ChampionScore
from app.engine.plugins.base import RecommendationContext, ScoringPlugin


class ScoringEngine:
    def __init__(
        self,
        plugins: list[ScoringPlugin],
    ) -> None:
        self.plugins = plugins

    def score_champion(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ChampionScore:
        result = ChampionScore(
            champion_id=champion_id,
            champion_name=champion_name,
        )

        for plugin in self.plugins:
            contribution = plugin.evaluate(
                champion_id=champion_id,
                champion_name=champion_name,
                context=context,
            )

            result.contributions.append(contribution)

        return result

    def rank_champions(
        self,
        champions: list[dict],
        context: RecommendationContext,
        limit: int = 5,
    ) -> list[dict]:
        scores: list[ChampionScore] = []

        for champion in champions:
            champion_id = int(champion["championId"])
            champion_name = str(champion["championName"])

            if (
                context.owned_champion_ids
                and champion_id not in context.owned_champion_ids
            ):
                continue

            if champion_id in context.banned_champion_ids:
                continue

            scores.append(
                self.score_champion(
                    champion_id=champion_id,
                    champion_name=champion_name,
                    context=context,
                )
            )

        scores.sort(
            key=lambda item: item.total,
            reverse=True,
        )

        return [
            score.to_dict()
            for score in scores[:limit]
        ]
