"""Serviço de planejamento diário de farm, materiais de ascensão e despacho de notificações."""

import datetime
import sys
from typing import Any, Dict, List, Optional

import build_calculator
import database
from core.config import get_config
from notifications import notifier


def calculate_ascension_materials(
    game_id: str, current_level: int, target_level: int, char_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    return build_calculator.calculate_ascension(game_id, current_level, target_level, char_name)


def get_today_farming_plan(
    game_id: str, roster: List[Dict[str, Any]], selected_chars: Optional[str] = None, lang: str = "pt"
) -> Dict[str, Any]:
    selected_list = [s.strip() for s in selected_chars.split(",") if s.strip()] if selected_chars else None
    return build_calculator.get_daily_farm_recommendations(
        game_id=game_id,
        roster=roster,
        selected_chars=selected_list,
        lang=lang or "pt",
    )


def generate_daily_farm_order_for_game(
    game_id: str, roster_data: List[Dict[str, Any]], selected_chars: Optional[str] = None, lang: str = "pt"
) -> Dict[str, Any]:
    selected_list = [s.strip() for s in selected_chars.split(",") if s.strip()] if selected_chars else None
    meta_data = build_calculator.get_meta_data(game_id)
    return build_calculator.generate_daily_farm_order(
        game_id=game_id,
        roster=roster_data,
        meta_data=meta_data,
        selected_chars=selected_list,
        lang=lang or "pt",
    )


def toggle_farm_order_task(game_id: str, task_id: str, completed: bool) -> Dict[str, Any]:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    new_state = database.set_farm_task_completed(
        date_str=today_str,
        game_id=game_id,
        task_id=task_id,
        completed=completed,
    )
    return {"status": "success", "game_id": game_id, "task_id": task_id, "completed": new_state}


def send_daily_farm_order_notification(game_id: str, roster_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Gera a Ordem Diária e envia o resumo para Discord/Telegram sem emojis decorativos."""
    order = generate_daily_farm_order_for_game(game_id, roster_data, None, "pt")
    server_mod = sys.modules.get("server")
    cfg_fn = server_mod.get_config if (server_mod and hasattr(server_mod, "get_config")) else get_config
    notif = server_mod.notifier if (server_mod and hasattr(server_mod, "notifier")) else notifier
    cfg = cfg_fn()

    fields = []
    for t in order.get("tasks", []):
        status_tag = "[OK]" if t.get("completed") else "[Pendente]"
        status_label = "Disponível Agora" if t.get("available_now") else t.get("time_estimate")
        fields.append(
            {
                "name": f"{status_tag} Passo {t.get('step')}: {t.get('type_label')} ({t.get('target_character')})",
                "value": (
                    f"**Material:** {t.get('material_name')}\n"
                    f"**Local:** {t.get('location')}\n"
                    f"**Custo:** {t.get('cost_energy')} {t.get('energy_name')} ({status_label})"
                ),
                "inline": False,
            }
        )

    energy_info = order.get("energy", {})
    header_desc = (
        f"**Energia:** {energy_info.get('current')}/{energy_info.get('max')} {energy_info.get('name')}\n"
        f"**Dia:** {order.get('weekday_name')} ({order.get('date')})\n"
        f"**Progresso:** {order.get('completed_count')}/{order.get('total_tasks')} ({order.get('completion_percentage')}%)"
    )

    res = notif.send_notification(
        title=f"Ordem de Farm Diário • {order.get('game_name')}",
        message=header_desc,
        config=cfg,
        color=0x10B981,
        fields=fields,
    )
    return {"status": "success", "results": res, "quick_summary_text": order.get("quick_summary_text")}
