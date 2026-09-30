import os
import sys
import datetime
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException

import database
import build_calculator
from core.config import get_config
from notifications import notifier
from services.roster_service import get_roster
from schemas.farming import (
    FarmOrderToggleRequest,
    FarmOrderSendNotificationRequest,
    MaterialsCalculateRequest,
)

router = APIRouter(tags=["Farming & Materials"])

@router.post("/api/materials/calculate")
async def calculate_materials(req: MaterialsCalculateRequest):
    """Calcula o total estimado de materiais necessários para elevar um personagem."""
    res = build_calculator.calculate_ascension(req.game_id, req.current_level, req.target_level, req.char_name)
    if not res:
        raise HTTPException(status_code=400, detail="Erro ao realizar o cálculo de ascensão.")
    return res

@router.get("/api/farming/today/{game_id}")
async def get_farming_today(game_id: str, selected_chars: Optional[str] = None):
    """Retorna o calendário de farm do dia atual + sugestões com base nos seus personagens."""
    try:
        roster_data = await get_roster(game_id)
        selected_list = [s.strip() for s in selected_chars.split(",") if s.strip()] if selected_chars else None
        res = build_calculator.get_daily_farm_recommendations(game_id=game_id, roster=roster_data, selected_chars=selected_list)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/farm/order-of-day/{game_id}")
async def get_daily_farm_order_endpoint(game_id: str, selected_chars: Optional[str] = None):
    """Retorna a Ordem de Serviço Diária com alocação inteligente de resina/energia."""
    try:
        roster_data = await get_roster(game_id)
        meta_data = build_calculator.get_meta_data(game_id)
        selected_list = [s.strip() for s in selected_chars.split(",") if s.strip()] if selected_chars else None
        order = build_calculator.generate_daily_farm_order(
            game_id=game_id,
            roster=roster_data,
            meta_data=meta_data,
            selected_chars=selected_list
        )
        return order
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/farm/order-of-day/toggle-step")
async def toggle_farm_order_step(req: FarmOrderToggleRequest):
    """Marca ou desmarca uma tarefa da Ordem de Serviço como concluída no banco de dados SQLite."""
    try:
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        new_state = database.set_farm_task_completed(
            date_str=today_str,
            game_id=req.game_id,
            task_id=req.task_id,
            completed=req.completed
        )
        return {"status": "success", "game_id": req.game_id, "task_id": req.task_id, "completed": new_state}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/farm/order-of-day/send-notification")
async def send_farm_order_notification(req: FarmOrderSendNotificationRequest):
    """Envia a Ordem de Serviço Diária diretamente para os canais Discord e Telegram configurados."""
    try:
        roster_data = await get_roster(req.game_id)
        meta_data = build_calculator.get_meta_data(req.game_id)
        order = build_calculator.generate_daily_farm_order(
            game_id=req.game_id,
            roster=roster_data,
            meta_data=meta_data
        )
        server_mod = sys.modules.get("server")
        cfg = server_mod.get_config() if (server_mod and hasattr(server_mod, "get_config")) else get_config()
        notif = server_mod.notifier if (server_mod and hasattr(server_mod, "notifier")) else notifier
        
        fields = []
        for t in order.get("tasks", []):
            check_icon = "✅" if t.get("completed") else "⏳"
            status_label = "Disponível Agora" if t.get("available_now") else t.get("time_estimate")
            fields.append({
                "name": f"{check_icon} Passo {t.get('step')}: {t.get('type_label')} ({t.get('target_character')})",
                "value": f"**Material:** {t.get('material_name')}\n**Local:** {t.get('location')}\n**Custo:** {t.get('cost_energy')} {t.get('energy_name')} ({status_label})",
                "inline": False
            })

        energy_info = order.get("energy", {})
        header_desc = (
            f"⚡ **Energia Atual:** {energy_info.get('current')}/{energy_info.get('max')} {energy_info.get('name')}\n"
            f"📅 **Dia:** {order.get('weekday_name')} ({order.get('date')})\n"
            f"🎯 **Progresso:** {order.get('completed_count')}/{order.get('total_tasks')} tarefas concluídas ({order.get('completion_percentage')}%)"
        )

        res = notif.send_notification(
            title=f"📋 Ordem de Serviço de Farm Diário • {order.get('game_name')}",
            message=header_desc,
            config=cfg,
            color=0x10b981,
            fields=fields
        )
        return {"status": "success", "results": res, "quick_summary_text": order.get("quick_summary_text")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
