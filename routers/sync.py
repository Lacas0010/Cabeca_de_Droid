from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from core.config import validate_game_id
from schemas.sync import SyncRequest
from schemas.history import GlobalSyncResponse
from services import history_service
from services.sync_service import sync_status, _bg_sync_thread

router = APIRouter(tags=["Sync"])


@router.post("/api/sync/global", response_model=GlobalSyncResponse)
async def sync_global_endpoint():
    """Executa sincronização rápida e cria snapshots de evolução para todos os jogos configurados."""
    try:
        res = await history_service.sync_global_and_snapshot()
        return GlobalSyncResponse(**res)
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/sync/{game_id}")
async def start_sync(game_id: str, request: SyncRequest, background_tasks: BackgroundTasks):
    """Trigga a sincronização do roster, guias e metagame de um jogo específico."""
    clean_game = validate_game_id(game_id)

    if sync_status[clean_game]["running"]:
        return JSONResponse(
            status_code=409,
            content={"status": "error", "message": "A sincronização para este jogo já está em execução."},
        )

    # Limpa logs anteriores
    sync_status[clean_game] = {"running": True, "progress": 0.0, "message": "Inicializando...", "logs": []}

    # Executa a thread de background
    background_tasks.add_task(_bg_sync_thread, clean_game, request.run_roster, request.run_guides, request.run_meta)

    return {"status": "started", "message": "Sincronização iniciada com sucesso."}


@router.get("/api/status/{game_id}")
async def get_sync_status(game_id: str):
    """Retorna o progresso atual e os logs da sincronização."""
    clean_game = validate_game_id(game_id)
    return sync_status[clean_game]
