from typing import Optional
from fastapi import APIRouter

from schemas.updater import UpdaterCheckResponse, UpdaterStartRequest, UpdaterStatusResponse
import updater as updater_core

router = APIRouter(prefix="/api/updater", tags=["Auto-Updater"])


@router.get("/check", response_model=UpdaterCheckResponse)
async def check_github_release_update():
    """Verifica de forma assíncrona se há nova versão disponível no GitHub Releases."""
    return await updater_core.check_for_updates()


@router.post("/start", response_model=UpdaterStatusResponse)
async def start_github_release_update(payload: Optional[UpdaterStartRequest] = None):
    """Inicia download e substituição segura no Windows (.exe) ou orienta atualização no modo dev."""
    req = payload or UpdaterStartRequest()
    return await updater_core.start_update_process(
        download_url=req.download_url,
        target_version=req.target_version,
        release_url=req.release_url,
    )


@router.get("/status", response_model=UpdaterStatusResponse)
async def get_github_release_update_status():
    """Retorna o estágio e o progresso (0.0 a 1.0) da atualização em andamento."""
    return updater_core.get_updater_status()
