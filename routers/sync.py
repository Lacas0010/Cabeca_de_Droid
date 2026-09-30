from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from schemas.sync import SyncRequest
from services.sync_service import sync_status, _bg_sync_thread

router = APIRouter(tags=["Sync"])

@router.post("/api/sync/{game_id}")
async def start_sync(game_id: str, request: SyncRequest, background_tasks: BackgroundTasks):
    """Trigga a sincronização do roster, guias e metagame de um jogo específico."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    if sync_status[game_id]["running"]:
        return JSONResponse(status_code=409, content={"status": "error", "message": "A sincronização para este jogo já está em execução."})
        
    # Limpa logs anteriores
    sync_status[game_id] = {
        "running": True,
        "progress": 0.0,
        "message": "Inicializando...",
        "logs": []
    }
    
    # Executa a thread de background
    background_tasks.add_task(
        _bg_sync_thread,
        game_id,
        request.run_roster,
        request.run_guides,
        request.run_meta
    )
    
    return {"status": "started", "message": "Sincronização iniciada com sucesso."}

@router.get("/api/status/{game_id}")
async def get_sync_status(game_id: str):
    """Retorna o progresso atual e os logs da sincronização."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    return sync_status[game_id]
