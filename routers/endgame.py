from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from services.endgame_service import get_endgame
from services.team_matcher_service import match_endgame_teams
from schemas.team_matcher import EndgameTeamMatchResponse

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


@router.get("/api/endgame/team-match/{game_id}", response_model=EndgameTeamMatchResponse)
async def get_endgame_team_match_endpoint(
    game_id: str,
    uid: Optional[str] = Query(None, description="UID da conta do jogador"),
    mode: Optional[str] = Query(None, description="Filtro por modo de jogo (MoC, PF, AS, Abismo, Shiyu)"),
    min_match: Optional[float] = Query(0.0, description="Percentual mínimo de compatibilidade (0 a 100)"),
):
    """
    Cruza composições líderes de endgame do metagame com os personagens reais do jogador.
    Calcula percentual de compatibilidade e recomenda substitutos funcionais disponíveis no próprio roster.
    """
    try:
        return match_endgame_teams(game_id=game_id, uid=uid, mode=mode, min_match=min_match or 0.0)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
