from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.match_dataset import MatchDataset


class MatchDatasetRepository:
    def __init__(self, database: Session) -> None:
        self.database = database

    def attach(
        self,
        match_db_id: int,
        dataset: str,
        commit: bool = True,
    ) -> None:
        statement = sqlite_insert(
            MatchDataset
        ).values(
            match_db_id=match_db_id,
            dataset=dataset,
        )

        statement = statement.on_conflict_do_nothing(
            index_elements=[
                "match_db_id",
                "dataset",
            ]
        )

        self.database.execute(statement)

        if commit:
            self.database.commit()
        else:
            self.database.flush()

    def exists(
        self,
        match_db_id: int,
        dataset: str,
    ) -> bool:
        statement = select(MatchDataset.id).where(
            MatchDataset.match_db_id == match_db_id,
            MatchDataset.dataset == dataset,
        )

        return self.database.scalar(statement) is not None
