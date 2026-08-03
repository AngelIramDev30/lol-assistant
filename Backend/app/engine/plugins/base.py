from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.domain.score import ScoreContribution


@dataclass
class RecommendationContext:
    role: str | None
    pick_order: int | None
    ally_champion_ids: list[int] = field(default_factory=list)
    enemy_champion_ids: list[int] = field(default_factory=list)
    banned_champion_ids: list[int] = field(default_factory=list)
    owned_champion_ids: set[int] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


class ScoringPlugin(ABC):
    name: str
    weight: float

    @abstractmethod
    def evaluate(
        self,
        champion_id: int,
        champion_name: str,
        context: RecommendationContext,
    ) -> ScoreContribution:
        raise NotImplementedError
