from fastapi import APIRouter, HTTPException
from typing import Optional

import database
from build_calculator import simulate_gacha_probabilities, calculate_gacha_forecast
from schemas.gacha import (
    GachaRequest,
    GachaForecastRequest,
    GachaGoalSaveRequest,
    GachaGoalsListResponse,
    GachaSimulatorDefaultsResponse,
    GameBannersData,
)
from schemas.gacha_tracker import (
    GachaTrackerOverviewResponse,
    GachaHistoryListResponse,
    ImportGachaRequest,
    ImportGachaResponse,
)
from services.gacha_service import (
    get_gacha_characters,
    get_current_banners,
    get_gacha_simulator_defaults,
    get_saved_gacha_goals,
    create_saved_gacha_goal,
)
from services.gacha_tracker_service import (
    calculate_gacha_tracker_stats,
    get_gacha_pulls_history_detailed,
    import_gacha_log_data,
    export_gacha_log_uigf,
)

router = APIRouter(tags=["Gacha & Banners"])


@router.post("/api/gacha/calculate")
async def calculate_gacha_sim(req: GachaRequest):
    """Executa simulação Monte Carlo para probabilidade de obtenção em banners gacha."""
    try:
        res = simulate_gacha_probabilities(
            game_id=req.game_id,
            banner_type=req.banner_type or "character",
            current_pity=req.current_pity,
            is_guaranteed=req.is_guaranteed,
            pulls_available=req.pulls_available,
            target_copies=req.target_copies or 1,
            current_copies=req.current_copies or 0,
            current_rank=req.current_rank,
            target_rank=req.target_rank,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gacha/forecast/calculate")
async def calculate_gacha_forecast_endpoint(req: GachaForecastRequest):
    """
    Calcula o acúmulo futuro de tiros/gemas (diárias, passe, eventos, resets de loja/endgame)
    e roda o Monte Carlo para prever a probabilidade de bater a meta de banner.
    """
    try:
        res = calculate_gacha_forecast(
            game_id=req.game_id,
            banner_type=req.banner_type or "character",
            character_name=req.character_name or "",
            current_pulls=req.current_pulls or 0,
            current_pity=req.current_pity or 0,
            is_guaranteed=bool(req.is_guaranteed),
            target_rank=req.target_rank if req.target_rank is not None else 0,
            current_rank=req.current_rank if req.current_rank is not None else -1,
            target_days=req.target_days or 21,
            has_daily_pass=bool(req.has_daily_pass),
            has_battle_pass=bool(req.has_battle_pass),
            include_shop_resets=bool(req.include_shop_resets),
            include_events_estimate=bool(req.include_events_estimate),
            include_endgame_resets=bool(req.include_endgame_resets),
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gacha/goals", response_model=GachaGoalsListResponse)
@router.get("/api/gacha/goals/{game_id}", response_model=GachaGoalsListResponse)
async def list_gacha_goals(game_id: Optional[str] = "all"):
    """Retorna a lista de metas de banners salvas no banco de dados SQLite com progresso temporal em tempo real."""
    try:
        return get_saved_gacha_goals(game_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gacha/goals")
async def save_gacha_goal_endpoint(req: GachaGoalSaveRequest):
    """Salva uma nova meta de gacha forecast no SQLite com data de criação e data alvo da atualização."""
    try:
        return create_saved_gacha_goal(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/gacha/goals/{goal_id}")
async def delete_gacha_goal_endpoint(goal_id: int):
    """Exclui uma meta de gacha forecast pelo ID."""
    try:
        success = database.delete_gacha_goal(goal_id)
        if not success:
            raise HTTPException(status_code=404, detail="Meta não encontrada.")
        return {"status": "deleted", "goal_id": goal_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gacha/characters/{game_id}")
async def get_gacha_characters_endpoint(game_id: str):
    """Retorna a lista de personagens 5★ (Lendários / Rank S) para o simulador de gacha."""
    try:
        return await get_gacha_characters(game_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gacha/defaults/{game_id}", response_model=GachaSimulatorDefaultsResponse)
async def get_gacha_simulator_defaults_endpoint(
    game_id: str, uid: Optional[str] = None, banner_type: Optional[str] = "character"
):
    """
    Retorna os valores padrão do simulador de gacha:
    - Pity atual do jogador no banner relevante (extraído do histórico real no banco de dados).
    - Status do 50/50 ou 75/25 (garantido vs disputa).
    - Personagem ou arma do banner oficial ativo no jogo com arte/imagem do banner.
    - Suporta banner_type: 'character' ou 'weapon'.
    """
    try:
        return get_gacha_simulator_defaults(game_id=game_id, uid=uid, banner_type=banner_type or "character")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gacha/current-banners")
@router.get("/api/gacha/current-banners/{game_id}")
async def get_current_banners_endpoint(game_id: Optional[str] = None):
    """Retorna os dados dos banners atuais de personagens extraídos do manifesto ou raspados dinamicamente."""
    try:
        return get_current_banners(game_id=game_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gacha/current-banners/sync")
async def sync_current_banners_endpoint(game_id: Optional[str] = None):
    """Força a raspagem atualizada dos banners e artes oficiais de personagens no Prydwen."""
    try:
        from scrapers.scraper_prydwen import PrydwenScraper

        scraper = PrydwenScraper()
        res = scraper.get_current_banners(game_id=game_id)
        return {"status": "success", "message": "Banners atuais sincronizados com sucesso.", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==========================================================================
# RASTREADOR REAL DE TIROS / GACHA TRACKER (ETAPA 8)
# ==========================================================================


@router.get("/api/gacha/tracker/{game_id}", response_model=GachaTrackerOverviewResponse)
async def get_gacha_tracker_overview(game_id: str, uid: Optional[str] = None):
    """
    Retorna o status exato do histórico oficial de tiros do jogador:
    - Pity Atual em cada banner (Personagem, Arma, Padrão)
    - Status do 50/50 (Garantido vs Disputa)
    - Lista dos últimos 5★ com seus respectivos pities
    - Médias e Taxa de Vitórias no 50/50
    """
    try:
        return calculate_gacha_tracker_stats(game_id=game_id, uid=uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gacha/tracker/history/{game_id}", response_model=GachaHistoryListResponse)
async def get_gacha_tracker_history(
    game_id: str,
    uid: Optional[str] = None,
    banner_category: Optional[str] = None,
    rarity: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Retorna o histórico detalhado e paginado de puxadas com ícones oficiais de personagens, bangboos e armas.
    """
    try:
        return get_gacha_pulls_history_detailed(
            game_id=game_id,
            uid=uid,
            banner_category=banner_category,
            rarity=rarity,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gacha/tracker/import", response_model=ImportGachaResponse)
@router.post("/api/gacha/tracker/import/{game_id}", response_model=ImportGachaResponse)
async def import_gacha_tracker_endpoint(req: ImportGachaRequest, game_id: Optional[str] = "all"):
    """
    Importa dados de histórico de tiros via JSON nos formatos UIGF v4.1 (multi-jogo), UIGF v2.4+, SRGF ou lista bruta.
    """
    try:
        raw_payload = req.raw_data if req.raw_data is not None else req.pulls_list
        return import_gacha_log_data(game_id=game_id or "all", raw_data=raw_payload, uid=req.uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gacha/tracker/export/{game_id}")
async def export_gacha_tracker_endpoint(game_id: str, uid: Optional[str] = None):
    """
    Exporta o histórico de tiros do usuário no formato universal UIGF v2.4 para backup e migração.
    """
    try:
        return export_gacha_log_uigf(game_id=game_id, uid=uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/gacha/tracker/{game_id}")
async def clear_gacha_tracker_endpoint(game_id: str, uid: Optional[str] = None, banner_category: Optional[str] = None):
    """
    Exclui o histórico de puxadas para o jogo e UID selecionados.
    """
    try:
        deleted = database.delete_gacha_pulls(game_id=game_id, uid=uid, banner_category=banner_category)
        return {
            "status": "success",
            "game_id": game_id,
            "deleted_pulls": deleted,
            "message": f"{deleted} puxadas foram removidas do histórico com sucesso.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
