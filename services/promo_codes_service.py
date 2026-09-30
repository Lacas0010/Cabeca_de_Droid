import sys
import asyncio
import threading
import time
from typing import Dict, Any, List, Optional
import genshin

import database
import build_calculator
import extractor
from core.config import get_cookies, get_config
from notifications import notifier

def _get_active_cookies() -> Dict[str, Any]:
    server_mod = sys.modules.get("server")
    if server_mod and hasattr(server_mod, "get_cookies"):
        return server_mod.get_cookies()
    return get_cookies()

async def perform_auto_promo_code_redeem() -> Dict[str, Any]:
    """
    Rastreador autônomo: Busca códigos promocionais ativos e tenta resgatá-los
    em todas as contas registradas no HoYoLAB, evitando códigos já tentados anteriormente.
    """
    cookies = _get_active_cookies()
    if not cookies:
        return {"status": "no_cookies", "redeemed": {}}

    client = genshin.Client(cookies=cookies, lang="pt-pt")
    try:
        accounts = await client.get_game_accounts()
    except Exception as e:
        print(f"[AUTO-CODES] Erro ao obter contas vinculadas do HoYoLAB: {e}")
        return {"status": "error", "error": str(e)}

    all_redeemed_results = {}

    for acc in accounts:
        game_biz = acc.game_biz
        uid = str(acc.uid)

        game_key = None
        if game_biz.startswith("hk4e"):
            game_key = "genshin"
        elif game_biz.startswith("hkrpg"):
            game_key = "hsr"
        elif game_biz.startswith("nap"):
            game_key = "zzz"

        if not game_key:
            continue

        active_codes = build_calculator.fetch_active_promo_codes(game_key)
        if not active_codes:
            continue

        already_redeemed = database.get_redeemed_codes(game_key, uid)
        pending_codes = [c for c in active_codes if c["code"].upper() not in already_redeemed]

        if not pending_codes:
            continue

        print(f"[AUTO-CODES] {game_key.upper()} (UID {uid}): Encontrados {len(pending_codes)} novos códigos pendentes para resgate automático!")
        newly_claimed = []

        for c_entry in pending_codes:
            code = c_entry["code"]
            res = await extractor.redeem_promo_code(cookies=cookies, game_id=game_key, code=code)
            st = res.get("status", "error")
            msg = res.get("message", "")

            database.save_code_redemption(game_key, uid, code, st, msg)

            if st == "success":
                newly_claimed.append({"code": code, "rewards": c_entry.get("rewards", msg), "message": msg})
                print(f"[AUTO-CODES] [SUCCESS] {game_key.upper()} ({uid}): Código {code} resgatado com sucesso!")
            elif st == "claimed":
                print(f"[AUTO-CODES] [INFO] {game_key.upper()} ({uid}): Código {code} já havia sido resgatado.")
            elif st == "invalid":
                print(f"[AUTO-CODES] [WARN] {game_key.upper()} ({uid}): Código {code} expirou ou é inválido.")

            # Pausa de 5 segundos para respeitar os rate limits oficiais da HoYoverse
            await asyncio.sleep(5.0)

        if newly_claimed:
            all_redeemed_results[game_key] = newly_claimed
            try:
                config = get_config()
                notifier.notify_promo_codes(game_key, newly_claimed, config)
            except Exception as notif_err:
                print(f"[AUTO-CODES] Erro ao disparar notificação de novos códigos: {notif_err}")

    return {"status": "success", "redeemed": all_redeemed_results}

async def redeem_promo_codes_for_game(game_id: str, code: Optional[str] = None) -> Dict[str, Any]:
    """Resgata código(s) para um jogo específico e atualiza banco SQLite e notificações."""
    cookies = _get_active_cookies()
    if not cookies:
        raise ValueError("Cookies da HoYoLAB ausentes. Configure-os na aba de Configurações.")
        
    codes_to_redeem = []
    if code:
        codes_to_redeem.append(code)
    else:
        active = build_calculator.fetch_active_promo_codes(game_id)
        codes_to_redeem = [c["code"] for c in active]
        
    if not codes_to_redeem:
        return {"status": "info", "message": "Nenhum código para resgatar.", "results": []}

    client = genshin.Client(cookies=cookies)
    uid = "default"
    try:
        accounts = await client.get_game_accounts()
        for acc in accounts:
            if (game_id == "genshin" and acc.game_biz.startswith("hk4e")) or \
               (game_id == "hsr" and acc.game_biz.startswith("hkrpg")) or \
               (game_id == "zzz" and acc.game_biz.startswith("nap")):
                uid = str(acc.uid)
                break
    except Exception:
        pass
        
    results = []
    newly_claimed = []
    for c in codes_to_redeem:
        res = await extractor.redeem_promo_code(cookies=cookies, game_id=game_id, code=c)
        results.append(res)
        st = res.get("status", "error")
        msg = res.get("message", "")
        database.save_code_redemption(game_id, uid, c, st, msg)
        if st == "success":
            newly_claimed.append({"code": c, "message": msg})
        await asyncio.sleep(5.0)

    if newly_claimed:
        try:
            config = get_config()
            notifier.notify_promo_codes(game_id, newly_claimed, config)
        except Exception:
            pass
        
    return {"game_id": game_id, "results": results}

def start_auto_code_redeemer() -> None:
    """Inicia thread de verificação e resgate autônomo de códigos promocionais a cada 3 horas."""
    def auto_codes_loop():
        time.sleep(45)
        while True:
            try:
                config = get_config()
                if config.get("auto_sync_enabled", True) or config.get("notify_on_codes", True):
                    cookies = _get_active_cookies()
                    if cookies:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(perform_auto_promo_code_redeem())
                        loop.close()
            except Exception as c_err:
                print(f"[AUTO-CODES] Erro no loop de auto-redeem: {c_err}")
            time.sleep(10800)

    threading.Thread(target=auto_codes_loop, daemon=True).start()
