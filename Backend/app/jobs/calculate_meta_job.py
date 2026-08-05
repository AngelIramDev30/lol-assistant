import argparse
import json

from sqlalchemy import select

from app.database.models.champion_meta import Base
from app.database.session import SessionLocal, engine
from app.models.match import Match
from app.models.match_dataset import MatchDataset
from app.models.participant import Participant
from app.services.meta_calculator_service import (
    MetaCalculatorService,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        choices=["sample_local", "emerald_plus"],
        default="emerald_plus",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    _ = Match
    _ = Participant
    _ = MatchDataset

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as database:
        latest_match = database.scalar(
            select(Match)
            .join(
                MatchDataset,
                MatchDataset.match_db_id == Match.id,
            )
            .where(
                Match.queue == 420,
                MatchDataset.dataset == args.dataset,
            )
            .order_by(Match.game_creation.desc())
            .limit(1)
        )

        if latest_match is None:
            raise RuntimeError(
                f"No hay partidas para {args.dataset}."
            )

        calculator = MetaCalculatorService(database)

        result = calculator.calculate(
            patch=latest_match.patch,
            region=latest_match.region,
            queue=latest_match.queue,
            dataset=args.dataset,
        )

        print(
            json.dumps(
                result.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
