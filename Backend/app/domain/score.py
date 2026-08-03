from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoreContribution:
    engine: str
    score: float
    reason: str


@dataclass
class ChampionScore:
    champion_id: int
    champion_name: str
    contributions: list[ScoreContribution] = field(default_factory=list)

    @property
    def total(self) -> float:
        if not self.contributions:
            return 0.0

        return round(
            sum(item.score for item in self.contributions),
            2,
        )

    def add(
        self,
        engine: str,
        score: float,
        reason: str,
    ) -> None:
        self.contributions.append(
            ScoreContribution(
                engine=engine,
                score=score,
                reason=reason,
            )
        )

    def to_dict(self) -> dict:
        return {
            "championId": self.champion_id,
            "championName": self.champion_name,
            "score": self.total,
            "breakdown": [
                {
                    "engine": item.engine,
                    "score": item.score,
                    "reason": item.reason,
                }
                for item in self.contributions
            ],
        }
