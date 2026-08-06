import json
import subprocess
import sys
from dataclasses import dataclass, asdict

from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.match import Match
from app.models.match_dataset import MatchDataset
from app.models.participant import Participant


DATASET = "emerald_plus"


@dataclass
class UpdateSummary:
    collection_ok: bool = False
    meta_ok: bool = False
    matchups_ok: bool = False
    latest_patch: str | None = None
    matches_current_patch: int = 0
    participants_current_patch: int = 0


def run_module(*arguments: str) -> bool:
    command = [
        sys.executable,
        "-m",
        *arguments,
    ]

    print()
    print("$", " ".join(command))
    print("-" * 72)

    result = subprocess.run(
        command,
        check=False,
    )

    return result.returncode == 0


def get_dataset_stats() -> tuple[str | None, int, int]:
    with SessionLocal() as database:
        latest_patch = database.scalar(
            select(Match.patch)
            .join(
                MatchDataset,
                MatchDataset.match_db_id == Match.id,
            )
            .where(
                MatchDataset.dataset == DATASET,
                Match.queue == 420,
            )
            .order_by(Match.game_creation.desc())
            .limit(1)
        )

        if not latest_patch:
            return None, 0, 0

        matches = database.scalar(
            select(func.count(Match.id))
            .join(
                MatchDataset,
                MatchDataset.match_db_id == Match.id,
            )
            .where(
                MatchDataset.dataset == DATASET,
                Match.patch == latest_patch,
                Match.queue == 420,
            )
        ) or 0

        participants = database.scalar(
            select(func.count(Participant.id))
            .join(
                Match,
                Match.id == Participant.match_db_id,
            )
            .join(
                MatchDataset,
                MatchDataset.match_db_id == Match.id,
            )
            .where(
                MatchDataset.dataset == DATASET,
                Match.patch == latest_patch,
                Match.queue == 420,
            )
        ) or 0

        return (
            str(latest_patch),
            int(matches),
            int(participants),
        )


def main() -> None:
    summary = UpdateSummary()

    print("Actualizando dataset Emerald+...")

    summary.collection_ok = run_module(
        "app.jobs.collect_ranked_players_matches_job"
    )

    if not summary.collection_ok:
        print()
        print(
            "La recolección falló. "
            "No se recalcularán estadísticas."
        )
        print(json.dumps(asdict(summary), indent=2))
        raise SystemExit(1)

    summary.meta_ok = run_module(
        "app.jobs.calculate_meta_job",
        "--dataset",
        DATASET,
    )

    summary.matchups_ok = run_module(
        "app.jobs.calculate_matchups_job",
        "--dataset",
        DATASET,
    )

    (
        summary.latest_patch,
        summary.matches_current_patch,
        summary.participants_current_patch,
    ) = get_dataset_stats()

    print()
    print("=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(
        json.dumps(
            asdict(summary),
            indent=2,
            ensure_ascii=False,
        )
    )

    if not summary.meta_ok or not summary.matchups_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
