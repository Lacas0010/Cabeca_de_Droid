"""Rotas de planejamento diário de farm, materiais de ascensão e notificações."""

import asyncio
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException

from schemas.farming import (
    FarmOrderSendNotificationRequest,
    FarmOrderToggleRequest,
    MaterialsCalculateRequest,
)
from services.farming_service import (
    calculate_ascension_materials,
    generate_daily_farm_order_for_game,
    get_today_farming_plan,
    send_daily_farm_order_notification,
    toggle_farm_order_task,
)
from services.roster_service import get_roster

router = APIRouter(tags=["Farming & Materials"])


@router.post("/api/materials/calculate")
async def calculate_materials(req: MaterialsCalculateRequest):
    """Calcula o total estimado de materiais necessários para elevar um personagem."""
    res = await asyncio.to_thread(
        calculate_ascension_materials, req.game_id, req.current_level, req.target_level, req.char_name
    )
    if not res:
        raise HTTPException(status_code=400, detail="Erro ao realizar o cálculo de ascensão.")
    return res


@router.get("/api/farming/today/{game_id}")
async def get_farming_today(game_id: str, selected_chars: Optional[str] = None, lang: Optional[str] = "pt"):
    """Retorna o calendário de farm do dia atual com base no elenco do jogador."""
    try:
        roster_data = await get_roster(game_id)
        return await asyncio.to_thread(get_today_farming_plan, game_id, roster_data, selected_chars, lang or "pt")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/farm/order-of-day/{game_id}")
async def get_daily_farm_order_endpoint(game_id: str, selected_chars: Optional[str] = None, lang: Optional[str] = "pt"):
    """Retorna a Ordem Diária priorizada de gasto de resina/energia."""
    try:
        roster_data = await get_roster(game_id)
        return await asyncio.to_thread(
            generate_daily_farm_order_for_game, game_id, roster_data, selected_chars, lang or "pt"
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/farm/order-of-day/toggle-step")
async def toggle_farm_order_step(req: FarmOrderToggleRequest):
    """Marca ou desmarca uma tarefa da Ordem Diária no SQLite."""
    try:
        return await asyncio.to_thread(toggle_farm_order_task, req.game_id, req.task_id, req.completed)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/farm/order-of-day/send-notification")
async def send_farm_order_notification(req: FarmOrderSendNotificationRequest):
    """Envia a Ordem Diária de farm para Discord e Telegram."""
    try:
        roster_data = await get_roster(req.game_id)
        return await asyncio.to_thread(send_daily_farm_order_notification, req.game_id, roster_data)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
