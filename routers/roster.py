from typing import Optional
from fastapi import APIRouter, HTTPException

import database
from build_calculator import normalize_char_name
from services.roster_service import (
    get_roster,
    get_overview,
    parse_character_build_data,
    parse_meta_target,
)
from schemas.accounts import AccountsListResponse, SwitchAccountRequest

router = APIRouter(tags=["Roster & Characters"])


@router.get("/api/accounts", response_model=AccountsListResponse)
async def list_accounts_endpoint():
    """Retorna todas as contas cadastradas com nickname, level, quantidade de personagens e status ativo."""
    try:
        accounts = database.get_all_saved_accounts()
        active_map = database.get_active_accounts_map()
        return {"accounts": accounts, "active_accounts": active_map}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/accounts/switch")
async def switch_account_endpoint(req: SwitchAccountRequest):
    """Alterna a conta ativa para um determinado jogo (Multi-UID)."""
    game_clean = (req.game_id or "").lower().strip()
    if game_clean not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    try:
        database.set_active_account(game_clean, req.uid)
        return {
            "status": "success",
            "success": True,
            "game_id": game_clean,
            "active_uid": req.uid,
            "message": f"Conta ativa de {game_clean.upper()} alterada para o UID {req.uid} com sucesso!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/accounts/{uid}")
async def delete_account_endpoint(uid: str):
    """Exclui com segurança os dados de um UID específico (personagens, relíquias, notas)."""
    try:
        deleted = database.delete_account_profile(uid)
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
    """Gera dados resumidos consolidados dos 3 jogos mesclando SQLite e arquivos locais."""
    return get_overview()


@router.get("/api/account/{game_id}")
async def get_account_endpoint(game_id: str, uid: Optional[str] = None):
    """Retorna os dados da conta ativa do jogador ou de um UID específico."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")

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

    # Fallback para overview se não houver registro específico no SQLite
    ov = get_overview().get(game_id, {})
    return {
        "game_id": game_id,
        "uid": ov.get("uid", "Não sincronizado"),
        "nickname": ov.get("nickname") or "Jogador",
        "level": str(ov.get("level", "N/A")),
        "active_days": 0,
        "updated_at": "",
    }


@router.get("/api/build/{game_id}/{char_name}")
async def get_build_detail_endpoint(game_id: str, char_name: str):
    """Retorna os dados detalhados da build de um personagem, parseando o MD consolidado ou SQLite."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    return parse_character_build_data(game_id, char_name)


@router.get("/api/compare/{game_id}/{char_name}")
async def compare_build_endpoint(game_id: str, char_name: str):
    """Retorna os dados da build do jogador comparados aos dados ideais do metagame."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")

    element = ""
    try:
        roster = database.get_roster_data(game_id)
        c_norm = normalize_char_name(char_name)
        for char in roster:
            if normalize_char_name(char.get("name", "")) == c_norm or char.get("name", "").lower() == char_name.lower():
                element = char.get("element", "").lower()
                break
    except Exception as e:
        print(f"Erro ao buscar elemento do personagem no SQLite: {e}")

    build_data = parse_character_build_data(game_id, char_name)
    meta_target = parse_meta_target(game_id, char_name, element)

    return {
        "character": char_name,
        "game_id": game_id,
        "player_build": {
            "weapon": build_data.get("weapon", "Não informado"),
            "weapon_clean": build_data.get("weapon_clean", ""),
            "sets": build_data.get("sets", []),
            "stats": build_data.get("stats", {}),
            "pieces": build_data.get("pieces", []),
        },
        "meta_target": meta_target,
    }


@router.get("/api/optimize/{game_id}/{char_name}")
async def optimize_character_build(game_id: str, char_name: str):
    """Gera sugestões determinísticas de otimização de build com base nos dados do roster e no guia de meta."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")

    build_data = parse_character_build_data(game_id, char_name)
    if not build_data.get("raw") and not build_data.get("sets") and not build_data.get("pieces"):
        return {
            "suggestions": [
                "Nenhum dado de Roster/Build encontrado para este personagem. Faça a sincronização primeiro na aba do jogo."
            ]
        }

    return {
        "suggestions": [
            "1. Priorizar os atributos principais recomendados nas peças de Relíquias/Artefatos.",
            "2. Tentar alcançar os bônus máximos de conjunto equipando 4 peças ideais.",
            "3. Fortalecer o nível das relíquias equipadas para maximizar os atributos base.",
        ]
    }
