import time
from dataclasses import dataclass

from app.database.session import SessionLocal
from app.repositories.match_dataset_repository import (
    MatchDatasetRepository,
)
from app.repositories.match_repository import (
    MatchRepository,
)
from app.services.riot_api_service import (
    RiotApiService,
)


@dataclass(frozen=True)
class CollectionResult:
    requested: int
    downloaded: int
    stored: int
    skipped: int
    failed: int
    dataset_attached: int

    def to_dict(self) -> dict[str, int]:
        return {
            "requested": self.requested,
            "downloaded": self.downloaded,
            "stored": self.stored,
            "skipped": self.skipped,
            "failed": self.failed,
            "datasetAttached": self.dataset_attached,
        }


class MatchCollector:
    def __init__(
        self,
        riot_api: RiotApiService,
    ) -> None:
        self.riot_api = riot_api

    def collect_for_puuid(
        self,
        puuid: str,
        start: int = 0,
        count: int = 5,
        queue: int = 420,
        delay_seconds: float = 0.35,
        dataset: str | None = None,
    ) -> CollectionResult:
        match_ids = self.riot_api.get_match_ids(
            puuid=puuid,
            start=start,
            count=count,
            queue=queue,
        )

        downloaded = 0
        stored = 0
        skipped = 0
        failed = 0
        dataset_attached = 0

        with SessionLocal() as database:
            match_repository = MatchRepository(
                database
            )

            dataset_repository = (
                MatchDatasetRepository(database)
            )

            for index, match_id in enumerate(
                match_ids,
                start=1,
            ):
                existing = (
                    match_repository.get_by_match_id(
                        match_id
                    )
                )

                if existing is not None:
                    skipped += 1

                    if dataset:
                        dataset_repository.attach(
                            match_db_id=existing.id,
                            dataset=dataset,
                            commit=True,
                        )
                        dataset_attached += 1

                    print(
                        f"[{index}/{len(match_ids)}] "
                        f"{match_id}: ya existe"
                    )
                    continue

                try:
                    match_data = (
                        self.riot_api.get_match(
                            match_id
                        )
                    )
                    downloaded += 1

                    match = (
                        match_repository.save_match(
                            match_data=match_data,
                            region=(
                                self.riot_api
                                .platform_region
                            ),
                        )
                    )

                    if dataset:
                        dataset_repository.attach(
                            match_db_id=match.id,
                            dataset=dataset,
                            commit=True,
                        )
                        dataset_attached += 1

                    stored += 1

                    print(
                        f"[{index}/{len(match_ids)}] "
                        f"{match_id}: guardada"
                    )

                except Exception as error:
                    database.rollback()
                    failed += 1

                    print(
                        f"[{index}/{len(match_ids)}] "
                        f"{match_id}: ERROR "
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

                time.sleep(delay_seconds)

        return CollectionResult(
            requested=len(match_ids),
            downloaded=downloaded,
            stored=stored,
            skipped=skipped,
            failed=failed,
            dataset_attached=dataset_attached,
        )
