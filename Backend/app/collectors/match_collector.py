import time
from dataclasses import dataclass

from app.database.session import SessionLocal
from app.repositories.match_repository import MatchRepository
from app.services.riot_api_service import RiotApiService


@dataclass(frozen=True)
class CollectionResult:
    requested: int
    downloaded: int
    stored: int
    skipped: int
    failed: int

    def to_dict(self) -> dict[str, int]:
        return {
            "requested": self.requested,
            "downloaded": self.downloaded,
            "stored": self.stored,
            "skipped": self.skipped,
            "failed": self.failed,
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
        delay_seconds: float = 0.30,
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

        with SessionLocal() as database:
            repository = MatchRepository(database)

            for index, match_id in enumerate(match_ids, start=1):
                if repository.exists(match_id):
                    skipped += 1
                    print(
                        f"[{index}/{len(match_ids)}] "
                        f"{match_id}: ya existe"
                    )
                    continue

                try:
                    match_data = self.riot_api.get_match(match_id)
                    downloaded += 1

                    repository.save_match(
                        match_data=match_data,
                        region=self.riot_api.platform_region,
                    )

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
                        f"{type(error).__name__}: {error}"
                    )

                time.sleep(delay_seconds)

        return CollectionResult(
            requested=len(match_ids),
            downloaded=downloaded,
            stored=stored,
            skipped=skipped,
            failed=failed,
        )
