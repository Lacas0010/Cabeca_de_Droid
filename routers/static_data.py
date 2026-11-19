import asyncio
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException

import database
from core.config import validate_game_id
from services.roster_service import invalidate_roster_cache
from static_data_manager import static_data_manager
from schemas.sync import StaticDataSyncRequest
from build_calculator import evaluate_general_stats

router = APIRouter(tags=["Static Data & Datamines"])


@router.get("/api/static-data/status")
async def get_static_data_status():
    """Retorna o status geral de sincronização dos manifestos de dados estáticos."""
    manifests = await asyncio.to_thread(database.get_static_data_manifests)
    summary = await asyncio.to_thread(static_data_manager.get_sync_status)
    return {"status": "success", "manifests": manifests, "summary": summary}


def _sync_static_data_and_banners_sync(target_game: Optional[str]):
    results = static_data_manager.sync_upstream_data(target_game)
    database.save_static_data_manifests(results)
    invalidate_roster_cache(target_game)
    try:
        from scrapers.scraper_prydwen import PrydwenScraper

        PrydwenScraper().get_current_banners(target_game)
    except Exception as e:
        print(f"[WARN] Erro ao sincronizar banners em trigger_static_data_sync: {e}")
    return results


@router.post("/api/static-data/sync")
async def trigger_static_data_sync(req: Optional[StaticDataSyncRequest] = None):
    """Dispara a sincronização de dados estáticos de um jogo específico ou de todos."""
    target_game = req.game_id if req else None
    results = await asyncio.to_thread(_sync_static_data_and_banners_sync, target_game)
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
async def evaluate_character_stats(game_id: str, char_id: str, final_stats: Dict[str, str]):
    """Compara os status consolidados reais do personagem contra os benchmarks do metagame."""
    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(evaluate_general_stats, clean_game, str(char_id), final_stats)
