import json

from sqlalchemy import select

from app.database.models.champion_matchup import ChampionMatchup
from app.database.models.champion_meta import Base
from app.database.session import SessionLocal, engine
from app.models.match import Match
from app.models.participant import Participant
from app.services.matchup_calculator_service import (
    MatchupCalculatorService,
)


def main() -> None:
    _ = ChampionMatchup
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
                "No hay partidas guardadas."
            )

        calculator = MatchupCalculatorService(database)

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
