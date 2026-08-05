import os

from app.database.session import SessionLocal
from app.domain.score import ScoreContribution
from app.engine.plugins.base import (
    RecommendationContext,
    ScoringPlugin,
)
from app.repositories.champion_meta_repository import (
    ChampionMetaRepository,
)


class MetaPlugin(ScoringPlugin):
    name = "meta"
    weight = 0.30

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

        region = str(
            context.metadata.get("region")
            or os.getenv("RIOT_REGION", "la1")
        ).lower()

        queue = str(
            context.metadata.get("queue")
            or "420"
        )

        configured_rank = str(
            context.metadata.get("rank")
            or os.getenv(
                "META_DATASET_RANK",
                "sample_local",
            )
        ).lower()

        if not patch or role is None:
            return self._neutral_contribution(
                reason=(
                    "Faltan parche o rol para consultar "
                    "estad?sticas de meta."
                )
            )

        with SessionLocal() as database:
            repository = ChampionMetaRepository(database)

            stats = repository.get_one(
                patch=patch,
                region=region,
                queue=queue,
                role=role,
                rank=configured_rank,
                champion_id=champion_id,
            )

            if (
                stats is None
                and configured_rank != "sample_local"
            ):
                stats = repository.get_one(
                    patch=patch,
                    region=region,
                    queue=queue,
                    role=role,
                    rank="sample_local",
                    champion_id=champion_id,
                )

        if stats is None:
            return self._neutral_contribution(
                reason=(
                    f"Sin datos para {champion_name} "
                    f"en {role}, parche {patch}."
                )
            )

        raw_score = self._calculate_raw_score(
            games=stats.games,
            wins=stats.wins,
            pick_rate=stats.pick_rate,
        )

        weighted_score = raw_score * self.weight

        confidence = min(
            stats.games / 50.0,
            1.0,
        )

        return ScoreContribution(
            engine=self.name,
            score=round(weighted_score, 2),
            reason=(
                f"Meta SQLite: {stats.games} partidas, "
                f"{stats.win_rate:.2f}% WR, "
                f"{stats.pick_rate:.2f}% pick rate. "
                f"Confianza de muestra: "
                f"{confidence * 100:.0f}%."
            ),
        )

    @staticmethod
    def _calculate_raw_score(
        games: int,
        wins: int,
        pick_rate: float,
    ) -> float:
        # Suavizado bayesiano:
        # a?ade 10 partidas virtuales con 50% de win rate.
        adjusted_win_rate = (
            (wins + 5)
            / (games + 10)
            * 100
        )

        win_component = adjusted_win_rate * 0.75

        pick_component = min(
            max(pick_rate, 0.0),
            20.0,
        ) / 20.0 * 20.0

        sample_component = min(
            games / 50.0,
            1.0,
        ) * 5.0

        raw_score = (
            win_component
            + pick_component
            + sample_component
        )

        return max(
            0.0,
            min(100.0, raw_score),
        )

    def _neutral_contribution(
        self,
        reason: str,
    ) -> ScoreContribution:
        neutral_raw_score = 50.0

        return ScoreContribution(
            engine=self.name,
            score=round(
                neutral_raw_score * self.weight,
                2,
            ),
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
