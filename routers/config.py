"""Rotas de configurações locais, notificações e captura automática de sessão HoYoLAB."""

import asyncio
from fastapi import APIRouter, BackgroundTasks, Request

from schemas.config import ConfigSaveRequest, NotificationTestRequest
from services.config_service import (
    begin_auto_login_run,
    execute_auto_login_background,
    get_auto_login_state,
    get_sanitized_configuration,
    run_test_notifications,
    save_configuration_changes,
)

router = APIRouter(tags=["Config & Notifications"])


@router.get("/api/config")
async def get_configuration(request: Request):
    """Retorna configurações sanitizadas sob premissa Zero-Exposure."""
    _ = request
    return await asyncio.to_thread(get_sanitized_configuration)


@router.post("/api/config")
async def save_configuration(req: ConfigSaveRequest):
    """Salva cookies e configurações de agendamento e notificações no cofre criptografado."""
    return await asyncio.to_thread(save_configuration_changes, req)


@router.post("/api/notifications/test")
async def test_notifications_endpoint(req: NotificationTestRequest):
    """Dispara notificações de teste para validar os canais Discord, Telegram e Windows Toast."""
    return await asyncio.to_thread(run_test_notifications, req)


@router.get("/api/login/auto/status")
def get_auto_login_status():
    """Retorna o estado atual da captura automática de cookies sem expor tokens."""
    return get_auto_login_state()


@router.post("/api/login/auto")
async def auto_login_hoyolab(background_tasks: BackgroundTasks):
    """Dispara a captura de cookies via Playwright em segundo plano."""
    if not begin_auto_login_run():
        return {"status": "running", "message": "Login automático já está em andamento."}
    background_tasks.add_task(execute_auto_login_background)
    return {"status": "started", "message": "Navegador de Login Automático iniciado em segundo plano."}
