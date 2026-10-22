import traceback
from fastapi import APIRouter, HTTPException

import database
from build_calculator import (
    recommend_relic_crafting,
    find_trash_relics,
    calculate_stat_breakpoints,
    optimize_character_relics,
    get_meta_data,
)
from services.roster_service import get_roster
from services.simulation_service import simulate_relic_swap
from schemas.stats import BreakpointRequest, BreakpointResponse
from schemas.relics import TrashRelicsResponse
from schemas.simulation import SimulateSwapRequest, SimulateSwapResponse

router = APIRouter(tags=["Relics & Optimization"])


@router.get("/api/relics/craft-recommendations/{game_id}")
async def get_relic_craft_recommendations(game_id: str):
    """
    Retorna recomendações inteligentes para uso de Resina Automodeladora (HSR),
    Elixir Santificador (Genshin) e Sintetizador de Discos (ZZZ).
    """
    game_id = game_id.lower().strip()
    if game_id not in ["genshin", "hsr", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")

    try:
        roster_data = database.get_roster_data(game_id)
        result = recommend_relic_crafting(game_id, roster_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/relics/trash/{game_id}", response_model=TrashRelicsResponse)
async def get_trash_relics(game_id: str):
    """Analisa o inventário de relíquias salvas contra o metagame, identifica peças lixo e protege peças coringa."""
    try:
        roster = database.get_roster_data(game_id=game_id)
        all_relics = []
        for char in roster:
            for r in char.get("relics", []):
                all_relics.append(
                    {
                        "name": r.get("name", ""),
                        "slot": r.get("slot", ""),
                        "main_stat": r.get("main", r.get("main_stat", "")),
                        "substats": [{"name": s.strip()} for s in str(r.get("sub", "")).split(",") if s.strip()],
                        "character_name": char.get("name", ""),
                        "icon": r.get("icon", ""),
                    }
                )
        meta = get_meta_data(game_id)
        res = find_trash_relics(game_id=game_id, relics=all_relics, meta_data=meta)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/relics/optimize/{game_id}/{char_name}")
async def optimize_relics_for_character(game_id: str, char_name: str):
    """Encontra a melhor combinação possível de relíquias no inventário do usuário para um personagem."""
    try:
        roster = database.get_roster_data(game_id=game_id)
        all_relics = []
        for char in roster:
            for r in char.get("relics", []):
                r_copy = dict(r)
                r_copy["character_name"] = char.get("name", "")
                all_relics.append(r_copy)

        res = optimize_character_relics(game_id=game_id, char_id=char_name, relics_list=all_relics)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/stats/breakpoints", response_model=BreakpointResponse)
async def check_breakpoints(req: BreakpointRequest):
    """Verifica limiares de velocidade, EHR, Recarga e Crítico do personagem."""
    try:
        res = calculate_stat_breakpoints(game_id=req.game_id, char_name=req.char_name, stats=req.stats)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/relics/simulate-swap", response_model=SimulateSwapResponse)
async def simulate_relic_swap_endpoint(req: SimulateSwapRequest):
    """
    Simula a substituição de uma relíquia equipada por outra peça (do inventário ou teórica),
    avaliando as variações de score da build, Roll Value, deltas de atributos e novos breakpoints.
    """
    try:
        return simulate_relic_swap(req)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
