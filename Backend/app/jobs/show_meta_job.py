import argparse

from sqlalchemy import select

from app.database.models.champion_meta import ChampionMeta
from app.database.session import SessionLocal
from app.services.data_dragon_service import DataDragonService


VALID_ROLES = {
    "top",
    "jungle",
    "middle",
    "bottom",
    "utility",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--role",
        choices=sorted(VALID_ROLES),
        default="top",
    )

    parser.add_argument(
        "--patch",
        default="16.15",
    )

    parser.add_argument(
        "--dataset",
        choices=["emerald_plus", "sample_local"],
        default="emerald_plus",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data_dragon = DataDragonService(locale="es_MX")
    data_dragon.ensure_loaded()

    with SessionLocal() as database:
        statement = (
            select(ChampionMeta)
            .where(
                ChampionMeta.patch == args.patch,
                ChampionMeta.region == "la1",
                ChampionMeta.queue == "420",
                ChampionMeta.role == args.role,
                ChampionMeta.rank == args.dataset,
            )
            .order_by(
                ChampionMeta.games.desc(),
                ChampionMeta.win_rate.desc(),
            )
            .limit(args.limit)
        )

        rows = list(
            database.scalars(statement).all()
        )

    if not rows:
        print(
            "No hay estadísticas para ese contexto."
        )
        return

    print()
    print(
        f"Meta {args.dataset} | "
        f"Patch {args.patch} | "
        f"Role {args.role}"
    )
    print("-" * 78)

    for position, row in enumerate(rows, start=1):
        champion_name = (
            data_dragon.get_champion_name(
                row.champion_id
            )
            or f"ID {row.champion_id}"
        )

        print(
            f"{position:>2}. "
            f"{champion_name:<20} "
            f"Games: {row.games:<4} "
            f"Wins: {row.wins:<4} "
            f"WR: {row.win_rate:>6.2f}% "
            f"Pick: {row.pick_rate:>6.2f}%"
        )


if __name__ == "__main__":
    main()
