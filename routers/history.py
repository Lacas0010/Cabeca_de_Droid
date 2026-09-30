import traceback
from fastapi import APIRouter, HTTPException

import database

router = APIRouter(tags=["Account History & Evolution"])

@router.get("/api/history/{game_id}")
async def get_account_history_endpoint(game_id: str):
    """Retorna a timeline de evolução da conta com métricas salvas em snapshots."""
    try:
        history = database.get_account_history(game_id=game_id)
        return {"game_id": game_id, "history": history}
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
