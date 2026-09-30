import asyncio
import threading
import time
from typing import List, Dict, Any
import genshin

import database
from core.config import get_cookies, get_config
from notifications import notifier

async def perform_auto_checkin() -> List[Dict[str, Any]]:
    """Executa o check-in diário oficial da HoYoLAB para todas as contas vinculadas."""
    cookies = get_cookies()
    if not cookies:
        print("[CHECKIN] Nenhum cookie configurado para o check-in automático.")
        return []
        
    client = genshin.Client(cookies=cookies, lang="pt-pt")
    
    try:
        accounts = await client.get_game_accounts()
    except Exception as e:
        print(f"[CHECKIN] Erro ao obter contas para check-in: {e}")
        return []
        
    logs = []
    processed = set()
    
    for acc in accounts:
        game_biz = acc.game_biz
        uid = str(acc.uid)
        
        game_type = None
        game_key = None
        if game_biz.startswith("hk4e"):
            game_type = genshin.Game.GENSHIN
            game_key = "genshin"
        elif game_biz.startswith("hkrpg"):
            game_type = genshin.Game.STARRAIL
            game_key = "hsr"
        elif game_biz.startswith("nap"):
            game_type = genshin.Game.ZZZ
            game_key = "zzz"
            
        if not game_type or (game_key, uid) in processed:
            continue
            
        processed.add((game_key, uid))
        client.game = game_type
        
        try:
            reward = await client.claim_daily_reward()
            msg = f"Check-in realizado com sucesso! Recompensa: {reward.name} (x{reward.amount})"
            database.save_checkin_log(game_key, uid, "SUCCESS", msg)
            logs.append({"game_id": game_key, "uid": uid, "status": "SUCCESS", "message": msg})
            print(f"[CHECKIN] {game_key.upper()} ({uid}): {msg}")
        except genshin.AlreadyClaimed:
            msg = "Recompensa diária já foi resgatada hoje."
            database.save_checkin_log(game_key, uid, "ALREADY_CLAIMED", msg)
            logs.append({"game_id": game_key, "uid": uid, "status": "ALREADY_CLAIMED", "message": msg})
            print(f"[CHECKIN] {game_key.upper()} ({uid}): {msg}")
        except Exception as err:
            err_msg = str(err)
            if "1008" in err_msg or "already claimed" in err_msg.lower():
                msg = "Recompensa diária já foi resgatada hoje."
                database.save_checkin_log(game_key, uid, "ALREADY_CLAIMED", msg)
                logs.append({"game_id": game_key, "uid": uid, "status": "ALREADY_CLAIMED", "message": msg})
            else:
                msg = f"Erro no check-in: {err_msg}"
                database.save_checkin_log(game_key, uid, "ERROR", msg)
                logs.append({"game_id": game_key, "uid": uid, "status": "ERROR", "message": msg})
            print(f"[CHECKIN] {game_key.upper()} ({uid}): Erro: {err_msg}")
            
    # Dispara notificação com resumo do check-in automático
    try:
        config = get_config()
        notifier.notify_checkin_summary(logs, config)
    except Exception as notif_err:
        print(f"[NOTIF] Erro ao despachar notificação de check-in: {notif_err}")

    return logs

async def fetch_realtime_notes() -> Dict[str, Any]:
    """Busca as notas diárias (resina, energia, diárias) em tempo real via API do HoYoLAB."""
    cookies = get_cookies()
    if not cookies:
        try:
            return database.get_cached_daily_notes()
        except Exception:
            return {}
            
    client = genshin.Client(cookies=cookies, lang="pt-pt")
    
    try:
        accounts = await client.get_game_accounts()
    except Exception as e:
        print(f"Erro ao obter contas vinculadas no HoYoLAB para notas: {e}")
        try:
            return database.get_cached_daily_notes()
        except Exception:
            return {}
            
    for acc in accounts:
        # 1. Genshin Impact
        if acc.game_biz.startswith("hk4e"):
            try:
                client.game = genshin.Game.GENSHIN
                notes = await client.get_genshin_notes(acc.uid)
                
                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(
                    uid=str(acc.uid),
                    game_id="genshin",
                    nickname=acc.nickname,
                    level=acc.level
                )
                
                expeditions = []
                for exp in notes.expeditions:
                    rem_time = getattr(exp, "remaining_time", getattr(exp, "remained_time", None))
                    expeditions.append({
                        "character_icon": getattr(exp, "character_icon", getattr(getattr(exp, "character", None), "icon", "")),
                        "status": str(exp.status),
                        "remaining_time": str(rem_time) if rem_time is not None else "0"
                    })
                    
                extra_info = {
                    "completed_commissions": notes.completed_commissions,
                    "max_commissions": notes.max_commissions,
                    "claimed_commission_reward": notes.claimed_commission_reward,
                    "expeditions": expeditions,
                    "current_realm_currency": notes.current_realm_currency,
                    "max_realm_currency": notes.max_realm_currency
                }
                
                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="genshin",
                    nickname=acc.nickname,
                    current_energy=notes.current_resin,
                    max_energy=notes.max_resin,
                    recovery_time=str(notes.remaining_resin_recovery_time),
                    extra_info=extra_info
                )
            except Exception as ge:
                print(f"Erro ao obter notas do Genshin: {ge}")
                
        # 2. Honkai: Star Rail
        elif acc.game_biz.startswith("hkrpg"):
            try:
                client.game = genshin.Game.STARRAIL
                notes = await client.get_starrail_notes(acc.uid)
                
                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(
                    uid=str(acc.uid),
                    game_id="hsr",
                    nickname=acc.nickname,
                    level=acc.level
                )
                
                expeditions = []
                for exp in notes.expeditions:
                    rem_time = getattr(exp, "remaining_time", getattr(exp, "remained_time", None))
                    expeditions.append({
                        "name": getattr(exp, "name", "Expedição"),
                        "remaining_time": str(rem_time) if rem_time is not None else "0"
                    })
                    
                extra_info = {
                    "expeditions": expeditions,
                    "current_train_score": notes.current_train_score,
                    "max_train_score": notes.max_train_score,
                    "current_rogue_score": getattr(notes, "current_rogue_score", 0),
                    "max_rogue_score": getattr(notes, "max_rogue_score", 0)
                }
                
                # Stamina recovery time é timedelta, convertemos para segundos (string int) para o front decodificar
                recovery_sec = "0"
                if hasattr(notes, "stamina_recover_time") and notes.stamina_recover_time:
                    recovery_sec = str(int(notes.stamina_recover_time.total_seconds()))
                
                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="hsr",
                    nickname=acc.nickname,
                    current_energy=notes.current_stamina,
                    max_energy=notes.max_stamina,
                    recovery_time=recovery_sec,
                    extra_info=extra_info
                )
            except Exception as he:
                print(f"Erro ao obter notas do HSR: {he}")
                
        # 3. Zenless Zone Zero
        elif acc.game_biz.startswith("nap"):
            try:
                client.game = genshin.Game.ZZZ
                notes = await client.get_zzz_notes(acc.uid)
                
                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(
                    uid=str(acc.uid),
                    game_id="zzz",
                    nickname=acc.nickname,
                    level=acc.level
                )
                
                extra_info = {
                    "engagement": getattr(notes.engagement, "current", 0) if hasattr(notes, "engagement") and hasattr(notes.engagement, "current") else getattr(notes, "engagement", 0),
                    "video_store_state": str(getattr(notes, "video_store_state", "Desconhecido")),
                    "scratch_card_completed": bool(getattr(notes, "scratch_card_completed", False))
                }
                
                # No pydantic model do genshin.py, recovery_time está em battery_charge.seconds_till_full
                recovery_sec = "0"
                if hasattr(notes, "battery_charge"):
                    recovery_sec = str(getattr(notes.battery_charge, "seconds_till_full", 0))
                
                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="zzz",
                    nickname=acc.nickname,
                    current_energy=notes.battery_charge.current if hasattr(notes.battery_charge, "current") else getattr(notes, "battery_charge", 0),
                    max_energy=notes.battery_charge.max if hasattr(notes.battery_charge, "max") else 240,
                    recovery_time=recovery_sec,
                    extra_info=extra_info
                )
            except Exception as ze:
                print(f"Erro ao obter notas do ZZZ: {ze}")
                
    try:
        return database.get_cached_daily_notes()
    except Exception:
        return {}

def start_checkin_scheduler() -> None:
    """Inicia thread de agendamento automático de check-in a cada 6 horas."""
    def checkin_loop():
        time.sleep(10)
        while True:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(perform_auto_checkin())
                loop.close()
            except Exception as loop_err:
                print(f"[CHECKIN] Erro no loop de check-in automático: {loop_err}")
            time.sleep(21600)
            
    threading.Thread(target=checkin_loop, daemon=True).start()

def start_energy_watchdog_scheduler() -> None:
    """Inicia thread de monitoramento de energia/resina e alertas a cada 20 minutos."""
    def watchdog_loop():
        time.sleep(30)
        while True:
            try:
                config = get_config()
                if config.get("notifications_enabled") and config.get("notify_on_energy_cap", True):
                    cached_notes = database.get_cached_daily_notes()
                    if cached_notes:
                        notifier.check_energy_and_alert(cached_notes, config)
            except Exception as w_err:
                print(f"[WATCHDOG] Erro no monitor de energia/notificações: {w_err}")
            time.sleep(1200)

    threading.Thread(target=watchdog_loop, daemon=True).start()
