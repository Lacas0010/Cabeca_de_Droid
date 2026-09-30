from fastapi import APIRouter, HTTPException

import database
from core.config import get_config
from notifications import notifier
from services.checkin_service import perform_auto_checkin, fetch_realtime_notes

router = APIRouter(tags=["Checkin, Notes & Morning Briefing"])

@router.get("/api/notes")
async def get_notes():
    """Busca as notas diárias (resina, energia, diárias) em tempo real via API do HoYoLAB."""
    return await fetch_realtime_notes()

@router.post("/api/checkin/run")
async def run_manual_checkin():
    """Roda o check-in manual na HoYoLAB e retorna o resultado."""
    logs = await perform_auto_checkin()
    return {"status": "completed", "logs": logs}

@router.get("/api/checkin/today")
async def get_checkin_today():
    """Retorna os logs de check-in efetuados hoje."""
    try:
        return database.get_today_checkin_logs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/briefing/today")
async def get_today_morning_briefing():
    """Retorna os dados consolidados do Morning Briefing do dia atual."""
    try:
        config = get_config()
        briefing = notifier.generate_morning_briefing(config)
        return briefing
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/briefing/send-now")
async def send_morning_briefing_now():
    """Envia manualmente o Morning Briefing para os webhooks ativos (Discord / Telegram)."""
    try:
        config = get_config()
        result = notifier.send_morning_briefing(config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
