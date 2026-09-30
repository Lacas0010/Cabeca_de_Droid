from fastapi import APIRouter, HTTPException
from services.endgame_service import get_endgame

router = APIRouter(tags=["Endgame"])

@router.get("/api/endgame/{game_id}")
async def get_endgame_endpoint(game_id: str):
    """Retorna os dados estruturados de Endgame (MoC, Ficção Pura, Sombra, Abismo, Teatro, Shiyu) de um jogo."""
    try:
        return await get_endgame(game_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
