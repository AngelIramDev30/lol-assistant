import json

from sqlalchemy import distinct, select

from app.database.models.champion_meta import Base
from app.database.session import SessionLocal, engine
from app.models.match import Match
from app.models.match_dataset import MatchDataset
from app.models.participant import Participant
from app.models.ranked_player import RankedPlayer
from app.repositories.match_dataset_repository import (
    MatchDatasetRepository,
)


def main() -> None:
    _ = Match
    _ = Participant
    _ = RankedPlayer
    _ = MatchDataset

    Base.metadata.create_all(bind=engine)

    emerald_count = 0
    local_count = 0

    with SessionLocal() as database:
        dataset_repository = MatchDatasetRepository(
            database
        )

        ranked_puuids = set(
            database.scalars(
                select(RankedPlayer.puuid)
            ).all()
        )

        matches = list(
            database.scalars(
                select(Match).order_by(Match.id)
            ).all()
        )

        for match in matches:
            participant_puuids = set(
                database.scalars(
                    select(distinct(Participant.puuid))
                    .where(
                        Participant.match_db_id == match.id
                    )
                ).all()
            )

            if participant_puuids & ranked_puuids:
                dataset = "emerald_plus"
                emerald_count += 1
            else:
                dataset = "sample_local"
                local_count += 1

            dataset_repository.attach(
                match_db_id=match.id,
                dataset=dataset,
                commit=False,
            )

        database.commit()

    print(
        json.dumps(
            {
                "totalMatches": emerald_count + local_count,
                "emeraldPlus": emerald_count,
                "sampleLocal": local_count,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
