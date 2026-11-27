"""Rotas de manifestos estáticos, cronogramas de domínios e avaliação de atributos."""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException

import database
from core.config import validate_game_id
from schemas.static_data import EvaluateStatsRequest
from schemas.sync import StaticDataSyncRequest
from services.roster_service import invalidate_roster_cache
from services.static_data_service import (
    evaluate_stats_against_meta,
    get_static_data_status_summary,
    sync_static_data_and_banners,
)
from static_data_manager import static_data_manager

router = APIRouter(tags=["Static Data & Datamines"])


@router.get("/api/static-data/status")
async def get_static_data_status():
    """Retorna o status geral de sincronização dos manifestos de dados estáticos."""
    return await asyncio.to_thread(get_static_data_status_summary, database, static_data_manager)


@router.post("/api/static-data/sync")
async def trigger_static_data_sync(req: Optional[StaticDataSyncRequest] = None):
    """Dispara a sincronização de dados estáticos de um jogo específico ou de todos."""
    target_game = req.game_id if req else None
    results = await asyncio.to_thread(
        sync_static_data_and_banners,
        target_game,
        static_data_manager,
        database,
        invalidate_roster_cache,
    )
    return {"status": "success", "results": results}


@router.get("/api/static-data/schedule/{game_id}")
async def get_static_data_schedule(game_id: str, weekday: Optional[int] = None):
    """Retorna o calendário de materiais/domínios abertos hoje ou em dia específico."""
    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(static_data_manager.get_daily_farm_schedule, clean_game, weekday)


@router.get("/api/static-data/character/{game_id}/{char_name}")
async def get_static_data_character(game_id: str, char_name: str):
    """Retorna o perfil detalhado de materiais, chefes e calendário de um personagem."""
    clean_game = validate_game_id(game_id)
    profile = await asyncio.to_thread(static_data_manager.get_character_profile, clean_game, char_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Personagem não encontrado no manifesto de dados.")
    return profile


@router.get("/api/static-data/all-characters/{game_id}")
async def get_all_static_data_characters(game_id: str):
    """Retorna o catálogo completo de personagens com materiais mapeados para o jogo."""
    clean_game = validate_game_id(game_id)
    characters = await asyncio.to_thread(static_data_manager.get_all_characters, clean_game)
    return {"game_id": clean_game, "total": len(characters), "characters": characters}


@router.post("/api/evaluate-stats/{game_id}/{char_id}")
async def evaluate_character_stats(game_id: str, char_id: str, final_stats: EvaluateStatsRequest):
    """Compara os status consolidados reais do personagem contra os benchmarks do metagame."""
    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(evaluate_stats_against_meta, clean_game, str(char_id), final_stats.root)
