from fastapi import FastAPI, HTTPException
from requests import RequestException
from app.engine.draft_engine import DraftEngine
from app.engine.plugins.blind_pick.blind_pick_plugin import BlindPickPlugin
from app.engine.plugins.matchup.matchup_plugin import MatchupPlugin
from app.engine.plugins.meta.meta_plugin import MetaPlugin
from app.engine.scoring_engine import ScoringEngine
from app.engine.champion_select_engine import ChampionSelectEngine
from app.services.data_dragon_service import DataDragonService

from app.services.league_client import LeagueClient


app = FastAPI(
    title="LoL Assistant",
    version="0.3.0",
    description="League of Legends AI Assistant",
)

league_client = LeagueClient()

data_dragon = DataDragonService(locale="es_MX")
champion_select_engine = ChampionSelectEngine(data_dragon)
scoring_engine = ScoringEngine(
    plugins=[
        MetaPlugin(),
        MatchupPlugin(),
        BlindPickPlugin(),
    ]
)

draft_engine = DraftEngine(scoring_engine)
LEAGUE_PATH = r"D:\Riot Games\League of Legends"


def connect_league_client() -> None:
    found = league_client.find_lockfile(LEAGUE_PATH)

    if not found:
        raise HTTPException(
            status_code=503,
            detail="League Client no está abierto.",
        )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "running",
        "message": "LoL Assistant API",
    }


@app.get("/health")
def health() -> dict[str, bool]:
    return {
        "healthy": True,
    }


@app.get("/league/status")
def league_status() -> dict:
    found = league_client.find_lockfile(LEAGUE_PATH)

    if not found:
        return {
            "running": False,
            "message": "No se encontró el lockfile.",
        }

    return {
        "running": True,
        "lockfile": league_client.info(),
    }


@app.get("/league/profile")
def league_profile() -> dict:
    connect_league_client()

    try:
        profile = league_client.get_current_summoner()

        return {
            "connected": True,
            "profile": profile,
        }

    except RequestException as error:
        raise HTTPException(
            status_code=502,
            detail="No se pudo leer el perfil del cliente.",
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.get("/league/phase")
def league_phase() -> dict:
    connect_league_client()

    try:
        phase = league_client.get_gameflow_phase()

        return {
            "phase": phase,
        }

    except RequestException as error:
        raise HTTPException(
            status_code=502,
            detail="No se pudo leer el estado del cliente.",
        ) from error


@app.get("/league/champion-select")
def champion_select() -> dict:
    connect_league_client()

    try:
        session = league_client.get_champion_select_session()

        if session is None:
            return {
                "active": False,
                "message": "No estás en selección de campeón.",
            }

        return champion_select_engine.analyze(session)

    except RequestException as error:
        raise HTTPException(
            status_code=502,
            detail="No se pudo leer Champion Select.",
        ) from error

@app.get("/league/draft-recommendations")
def draft_recommendations() -> dict:
    connect_league_client()

    try:
        session = league_client.get_champion_select_session()

        if session is None:
            return {
                "active": False,
                "message": "No estás en selección de campeón.",
            }

        champion_select_data = champion_select_engine.analyze(session)

        all_champions = data_dragon.get_all_champions()

        draft_result = draft_engine.recommend(
            champion_select=champion_select_data,
            candidates=all_champions,
            limit=5,
        )

        return {
            "active": True,
            "patch": champion_select_data.get("patch"),
            "draft": draft_result,
        }

    except RequestException as error:
        raise HTTPException(
            status_code=502,
            detail="No se pudo leer la selección de campeón.",
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error
    
    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    