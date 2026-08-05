import json

from sqlalchemy import select

from app.database.models.champion_meta import Base
from app.database.session import SessionLocal, engine
from app.models.match import Match
from app.models.participant import Participant
from app.services.meta_calculator_service import (
    MetaCalculatorService,
)


def main() -> None:
    _ = Match
    _ = Participant

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as database:
        latest_match = database.scalar(
            select(Match)
            .where(Match.queue == 420)
            .order_by(Match.game_creation.desc())
            .limit(1)
        )

        if latest_match is None:
            raise RuntimeError(
                "No hay partidas guardadas. "
                "Ejecuta primero collect_matches_job."
            )

        calculator = MetaCalculatorService(database)

        result = calculator.calculate(
            patch=latest_match.patch,
            region=latest_match.region,
            queue=latest_match.queue,
            rank="sample_local",
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
