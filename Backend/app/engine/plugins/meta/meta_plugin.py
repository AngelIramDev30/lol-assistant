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

    PRIMARY_DATASET = "emerald_plus"
    FALLBACK_DATASET = "sample_local"

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
            context.metadata.get("queue") or "420"
        )

        preferred_dataset = str(
            context.metadata.get("rank")
            or self.PRIMARY_DATASET
        ).lower()

        if not patch or role is None:
            return self._unknown_contribution(
                "Faltan parche o rol para consultar el meta."
            )

        with SessionLocal() as database:
            repository = ChampionMetaRepository(database)

            stats = repository.get_one(
                patch=patch,
                region=region,
                queue=queue,
                role=role,
                rank=preferred_dataset,
                champion_id=champion_id,
            )

            dataset_used = preferred_dataset

            if stats is None:
                stats = repository.get_one(
                    patch=patch,
                    region=region,
                    queue=queue,
                    role=role,
                    rank=self.FALLBACK_DATASET,
                    champion_id=champion_id,
                )
                dataset_used = self.FALLBACK_DATASET

        if stats is None:
            return self._unknown_contribution(
                f"Sin datos para {champion_name} en "
                f"{role}, parche {patch}."
            )

        raw_score = self._calculate_raw_score(
            games=stats.games,
            wins=stats.wins,
            pick_rate=stats.pick_rate,
        )

        confidence = min(
            stats.games / 50.0,
            1.0,
        )

        dataset_text = (
            "Emerald+"
            if dataset_used == self.PRIMARY_DATASET
            else "muestra local de respaldo"
        )

        return ScoreContribution(
            engine=self.name,
            score=round(raw_score * self.weight, 2),
            reason=(
                f"Meta SQLite ({dataset_text}): "
                f"{stats.games} partidas, "
                f"{stats.win_rate:.2f}% WR, "
                f"{stats.pick_rate:.2f}% pick rate. "
                f"Confianza {confidence * 100:.0f}%."
            ),
        )

    @staticmethod
    def _calculate_raw_score(
        games: int,
        wins: int,
        pick_rate: float,
    ) -> float:
        # Prior conservador:
        # 20 partidas virtuales con 50% de win rate.
        adjusted_win_rate = (
            (wins + 10)
            / (games + 20)
            * 100
        )

        # La popularidad suma, pero no domina el resultado.
        pick_bonus = min(
            max(pick_rate, 0.0),
            20.0,
        ) / 20.0 * 10.0

        # La confianza aumenta lentamente con la muestra.
        sample_bonus = min(
            games / 50.0,
            1.0,
        ) * 5.0

        raw_score = (
            adjusted_win_rate
            + pick_bonus
            + sample_bonus
        )

        return max(
            0.0,
            min(100.0, raw_score),
        )

    def _unknown_contribution(
        self,
        reason: str,
    ) -> ScoreContribution:
        # Desconocido no significa malo, pero recibe una
        # pequeña penalización frente a datos reales.
        unknown_raw_score = 47.5

        return ScoreContribution(
            engine=self.name,
            score=round(
                unknown_raw_score * self.weight,
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
