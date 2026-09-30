from typing import Optional, Dict
from fastapi import APIRouter, HTTPException

import database
from static_data_manager import static_data_manager
from schemas.sync import StaticDataSyncRequest
from build_calculator import evaluate_general_stats

router = APIRouter(tags=["Static Data & Datamines"])

@router.get("/api/static-data/status")
async def get_static_data_status():
    """Retorna o status geral de sincronização dos manifestos de dados estáticos."""
    manifests = database.get_static_data_manifests()
    summary = static_data_manager.get_sync_status()
    return {
        "status": "success",
        "manifests": manifests,
        "summary": summary
    }

@router.post("/api/static-data/sync")
async def trigger_static_data_sync(req: Optional[StaticDataSyncRequest] = None):
    """Dispara a sincronização de dados estáticos de um jogo específico ou de todos."""
    target_game = req.game_id if req else None
    results = static_data_manager.sync_upstream_data(target_game)
    for gid, info in results.items():
        database.save_static_data_manifest(
            game_id=gid,
            version="1.0",
            item_count=info.get("character_count", 0),
            status=info.get("status", "success"),
            source=info.get("source", "seed")
        )
    return {
        "status": "success",
        "results": results
    }

@router.get("/api/static-data/schedule/{game_id}")
async def get_static_data_schedule(game_id: str, weekday: Optional[int] = None):
    """Retorna o calendário de materiais/domínios abertos hoje ou em dia específico."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    schedule = static_data_manager.get_daily_farm_schedule(game_id, weekday)
    return schedule

@router.get("/api/static-data/character/{game_id}/{char_name}")
async def get_static_data_character(game_id: str, char_name: str):
    """Retorna o perfil detalhado de materiais, chefes e calendário de um personagem."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    profile = static_data_manager.get_character_profile(game_id, char_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Personagem não encontrado no manifesto de dados.")
    return profile

@router.get("/api/static-data/all-characters/{game_id}")
async def get_all_static_data_characters(game_id: str):
    """Retorna o catálogo completo de personagens com materiais mapeados para o jogo."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    characters = static_data_manager.get_all_characters(game_id)
    return {
        "game_id": game_id,
        "total": len(characters),
        "characters": characters
    }

@router.post("/api/evaluate-stats/{game_id}/{char_id}")
async def evaluate_character_stats(game_id: str, char_id: str, final_stats: Dict[str, str]):
    """Compara os status consolidados reais do personagem contra os benchmarks do metagame."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    results = evaluate_general_stats(game_id, str(char_id), final_stats)
    return results
