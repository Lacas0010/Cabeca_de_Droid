from fastapi import APIRouter, HTTPException
from typing import Optional

import database
from build_calculator import simulate_gacha_probabilities, calculate_gacha_forecast
from schemas.gacha import GachaRequest, GachaForecastRequest, GachaGoalSaveRequest
from services.gacha_service import get_gacha_characters

router = APIRouter(tags=["Gacha & Banners"])

@router.post("/api/gacha/calculate")
async def calculate_gacha_sim(req: GachaRequest):
    """Executa simulação Monte Carlo para probabilidade de obtenção em banners gacha."""
    try:
        res = simulate_gacha_probabilities(
            game_id=req.game_id,
            current_pity=req.current_pity,
            is_guaranteed=req.is_guaranteed,
            pulls_available=req.pulls_available,
            target_copies=req.target_copies or 1,
            current_copies=req.current_copies or 0,
            current_rank=req.current_rank,
            target_rank=req.target_rank
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/gacha/forecast/calculate")
async def calculate_gacha_forecast_endpoint(req: GachaForecastRequest):
    """
    Calcula o acúmulo futuro de tiros/gemas (diárias, passe, eventos, resets de loja/endgame)
    e roda o Monte Carlo para prever a probabilidade de bater a meta de banner.
    """
    try:
        res = calculate_gacha_forecast(
            game_id=req.game_id,
            character_name=req.character_name or "",
            current_pulls=req.current_pulls or 0,
            current_pity=req.current_pity or 0,
            is_guaranteed=bool(req.is_guaranteed),
            target_rank=req.target_rank if req.target_rank is not None else 0,
            current_rank=req.current_rank if req.current_rank is not None else -1,
            target_days=req.target_days or 21,
            has_daily_pass=bool(req.has_daily_pass),
            has_battle_pass=bool(req.has_battle_pass),
            include_shop_resets=bool(req.include_shop_resets),
            include_events_estimate=bool(req.include_events_estimate),
            include_endgame_resets=bool(req.include_endgame_resets)
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/gacha/goals")
@router.get("/api/gacha/goals/{game_id}")
async def list_gacha_goals(game_id: Optional[str] = "all"):
    """Retorna a lista de metas de banners salvas no banco de dados SQLite."""
    try:
        goals = database.get_gacha_goals(game_id)
        return {"game_id": game_id or "all", "goals": goals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/gacha/goals")
async def save_gacha_goal_endpoint(req: GachaGoalSaveRequest):
    """Salva uma nova meta de gacha forecast no SQLite."""
    try:
        goal_id = database.save_gacha_goal(
            game_id=req.game_id,
            character_name=req.character_name,
            target_rank_str=req.target_rank_str,
            current_pulls=req.current_pulls,
            current_pity=req.current_pity,
            is_guaranteed=req.is_guaranteed,
            target_days=req.target_days,
            has_daily_pass=req.has_daily_pass,
            success_rate=req.success_rate,
            projected_pulls=req.projected_pulls,
            notes=req.notes or ""
        )
        return {"status": "saved", "goal_id": goal_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/gacha/goals/{goal_id}")
async def delete_gacha_goal_endpoint(goal_id: int):
    """Exclui uma meta de gacha forecast pelo ID."""
    try:
        success = database.delete_gacha_goal(goal_id)
        if not success:
            raise HTTPException(status_code=404, detail="Meta não encontrada.")
        return {"status": "deleted", "goal_id": goal_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/gacha/characters/{game_id}")
async def get_gacha_characters_endpoint(game_id: str):
    """Retorna a lista de personagens 5★ (Lendários / Rank S) para o simulador de gacha."""
    try:
        return await get_gacha_characters(game_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
