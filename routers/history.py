import traceback
from fastapi import APIRouter, Body, HTTPException

import database
from schemas.history import CreateSnapshotRequest, CreateSnapshotResponse
from services import history_service

router = APIRouter(tags=["Account History & Evolution"])


@router.get("/api/history/{game_id}")
async def get_account_history_endpoint(game_id: str, limit: int = 50, offset: int = 0):
    """Retorna a timeline de evolução da conta com métricas salvas em snapshots com paginação."""
    try:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        history = database.get_account_history(game_id=game_id, limit=limit, offset=offset)
        total_count = database.get_account_history_count(game_id=game_id)
        return {
            "game_id": game_id,
            "history": history,
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/history/{game_id}/snapshot", response_model=CreateSnapshotResponse)
async def create_snapshot_endpoint(
    game_id: str,
    payload: CreateSnapshotRequest = Body(default_factory=CreateSnapshotRequest),
):
    """Cria um novo snapshot manual de evolução da conta para o jogo informado."""
    try:
        res = await history_service.create_manual_snapshot(
            game_id=game_id,
            refresh_from_hoyolab=payload.refresh_from_hoyolab,
        )
        return CreateSnapshotResponse(**res)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history/{game_id}/compare/{snap_id_a}/{snap_id_b}")
async def compare_snapshots_endpoint(game_id: str, snap_id_a: int, snap_id_b: int):
    """Retorna a comparação rica entre quaisquer dois snapshots selecionados pelo usuário."""
    try:
        res = database.compare_two_snapshots(game_id=game_id, snap_id_a=snap_id_a, snap_id_b=snap_id_b)
        if not res:
            raise HTTPException(status_code=404, detail="Um ou ambos os snapshots selecionados não foram encontrados.")
        return res
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
