import traceback
from fastapi import APIRouter, HTTPException

import database
import build_calculator
from schemas.codes import RedeemCodeRequest
from services.promo_codes_service import redeem_promo_codes_for_game

router = APIRouter(tags=["Promo Codes"])

@router.get("/api/codes/{game_id}")
async def get_promo_codes_endpoint(game_id: str):
    """Retorna os códigos promocionais ativos para o jogo selecionado."""
    try:
        codes = build_calculator.fetch_active_promo_codes(game_id=game_id)
        return {"game_id": game_id, "codes": codes}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/codes/history/{game_id}")
async def get_promo_codes_history_endpoint(game_id: str):
    """Retorna o histórico cronológico de códigos promocionais resgatados para o jogo."""
    try:
        history = database.get_code_redemption_history(game_id=game_id)
        return {"game_id": game_id, "history": history}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/codes/redeem")
async def redeem_promo_code_endpoint(req: RedeemCodeRequest):
    """Resgata um ou todos os códigos promocionais ativos usando os cookies da conta e salva no histórico SQLite."""
    try:
        res = await redeem_promo_codes_for_game(game_id=req.game_id, code=req.code)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
