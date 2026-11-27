import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException

import database
from core.config import validate_game_id
from build_calculator import normalize_char_name
from services.roster_service import (
    get_roster,
    get_overview,
    parse_character_build_data,
    parse_meta_target,
    compare_character_build,
    invalidate_roster_cache,
)
from services.endgame_service import invalidate_endgame_cache
from schemas.accounts import AccountsListResponse, SwitchAccountRequest

router = APIRouter(tags=["Roster & Characters"])


def _list_accounts_sync():
    accounts = database.get_all_saved_accounts()
    active_map = database.get_active_accounts_map()
    return {"accounts": accounts, "active_accounts": active_map}


@router.get("/api/accounts", response_model=AccountsListResponse)
async def list_accounts_endpoint():
    """Retorna todas as contas cadastradas com nickname, level, quantidade de personagens e status ativo."""
    try:
        return await asyncio.to_thread(_list_accounts_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _switch_account_sync(game_clean: str, uid: str):
    database.set_active_account(game_clean, uid)
    invalidate_roster_cache(game_clean)
    invalidate_endgame_cache(game_clean)


@router.post("/api/accounts/switch")
async def switch_account_endpoint(req: SwitchAccountRequest):
    """Alterna a conta ativa para um determinado jogo (Multi-UID)."""
    game_clean = validate_game_id(req.game_id or "")
    try:
        await asyncio.to_thread(_switch_account_sync, game_clean, req.uid)
        return {
            "status": "success",
            "success": True,
            "game_id": game_clean,
            "active_uid": req.uid,
            "message": f"Conta ativa de {game_clean.upper()} alterada para o UID {req.uid} com sucesso!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _delete_account_sync(uid: str) -> int:
    deleted = database.delete_account_profile(uid)
    invalidate_roster_cache()
    invalidate_endgame_cache()
    return deleted


@router.delete("/api/accounts/{uid}")
async def delete_account_endpoint(uid: str):
    """Exclui com segurança os dados de um UID específico (personagens, relíquias, notas)."""
    try:
        deleted = await asyncio.to_thread(_delete_account_sync, uid)
        return {
            "status": "success",
            "success": True,
            "uid": uid,
            "deleted_records": deleted,
            "message": f"Perfil do UID {uid} e {deleted} registros associados foram removidos com sucesso.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/roster/{game_id}")
async def get_roster_endpoint(game_id: str, uid: Optional[str] = None):
    """Retorna os dados dos personagens salvos no roster local para a conta ativa ou UID especificado."""
    try:
        return await get_roster(game_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/overview")
async def get_overview_endpoint():
    """Resumo das contas dos 3 jogos (SQLite + cache local)."""
    return await asyncio.to_thread(get_overview)


def _get_account_sync(game_id: str, uid: Optional[str]):
    acc = database.get_game_account(game_id, uid=uid)
    if acc:
        return {
            "game_id": game_id,
            "uid": acc.get("uid", ""),
            "nickname": acc.get("nickname") or "Jogador",
            "level": str(acc.get("level", "0")),
            "active_days": acc.get("active_days", 0),
            "updated_at": acc.get("updated_at", ""),
        }

    ov = get_overview().get(game_id, {})
    return {
        "game_id": game_id,
        "uid": ov.get("uid", "Não sincronizado"),
        "nickname": ov.get("nickname") or "Jogador",
        "level": str(ov.get("level", "N/A")),
        "active_days": 0,
        "updated_at": "",
    }


@router.get("/api/account/{game_id}")
async def get_account_endpoint(game_id: str, uid: Optional[str] = None):
    """Retorna os dados da conta ativa do jogador ou de um UID específico."""
    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(_get_account_sync, clean_game, uid)


@router.get("/api/build/{game_id}/{char_name}")
async def get_build_detail_endpoint(game_id: str, char_name: str):
    """Retorna os dados detalhados da build de um personagem, parseando o MD consolidado ou SQLite."""
    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(parse_character_build_data, clean_game, char_name)


@router.get("/api/compare/{game_id}/{char_name}")
async def compare_build_endpoint(game_id: str, char_name: str):
    """Retorna os dados da build do jogador comparados aos dados ideais do metagame e o payload do Gráfico Radar."""
    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(compare_character_build, clean_game, char_name)


@router.get("/api/optimize/{game_id}/{char_name}")
async def optimize_character_build(game_id: str, char_name: str):
    """Sugestões de melhoria de build comparando o personagem com o guia recomendado."""
    from services.roster_service import get_character_optimization_suggestions

    clean_game = validate_game_id(game_id)
    return await asyncio.to_thread(get_character_optimization_suggestions, clean_game, char_name)
