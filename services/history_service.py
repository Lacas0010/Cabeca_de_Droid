from typing import Any, Dict

import database
from core.config import get_cookies
from extractor import MultiGameExtractor
from log_sanitizer import sanitize_log
from services.roster_service import invalidate_roster_cache

SUPPORTED_GAMES = ("hsr", "genshin", "zzz")


async def create_manual_snapshot(game_id: str, refresh_from_hoyolab: bool = True) -> Dict[str, Any]:
    """Cria imediatamente um snapshot de evolução para o jogo informado (atualizando via HoYoLAB se possível)."""
    g = (game_id or "").lower().strip()
    if g not in SUPPORTED_GAMES:
        raise ValueError("Jogo inválido. Use 'hsr', 'genshin' ou 'zzz'.")

    refreshed = False
    if refresh_from_hoyolab:
        cookies = get_cookies()
        if cookies:
            try:
                await MultiGameExtractor(cookies).extrair_jogo(g)
                invalidate_roster_cache(g)
                refreshed = True
            except Exception as extract_err:
                print(f"[SNAPSHOT] Aviso ao atualizar roster HoYoLAB ({g}): {sanitize_log(str(extract_err))}")

    roster_data = database.get_roster_data(g)
    if not roster_data:
        return {
            "success": False,
            "game_id": g,
            "snapshot_id": None,
            "refreshed_from_hoyolab": refreshed,
            "message": f"Nenhum personagem sincronizado encontrado para {g.upper()}.",
        }

    first_uid = (
        str(roster_data[0].get("uid") or "000000000").strip()
        if isinstance(roster_data, list) and roster_data
        else "000000000"
    )
    snap_id = database.save_account_snapshot(uid=first_uid, game_id=g, roster_data=roster_data, force=True)

    return {
        "success": True,
        "game_id": g,
        "snapshot_id": snap_id,
        "refreshed_from_hoyolab": refreshed,
        "message": f"Snapshot #{snap_id} de {g.upper()} gravado com sucesso!",
    }


async def sync_global_and_snapshot() -> Dict[str, Any]:
    """Atualiza e grava snapshots manuais para todos os jogos configurados."""
    results: Dict[str, Any] = {}
    any_success = False

    for g in SUPPORTED_GAMES:
        try:
            res = await create_manual_snapshot(g, refresh_from_hoyolab=True)
            results[g] = res
            if res.get("success"):
                any_success = True
        except Exception as err:
            results[g] = {"success": False, "message": sanitize_log(str(err))}

    return {
        "success": any_success,
        "results": results,
        "message": (
            "Snapshots de evolução criados com sucesso!"
            if any_success
            else "Nenhum jogo possuía dados de roster para gerar snapshot."
        ),
    }
