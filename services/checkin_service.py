import asyncio
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import genshin

import database
from core.config import get_cookies, get_config
from notifications import notifier

_RE_ISO_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$",
    re.IGNORECASE,
)
_RE_TIMEDELTA_STR = re.compile(
    r"^(?:(?P<days>\d+)\s+days?,\s*)?(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+(?:\.\d+)?)$",
    re.IGNORECASE,
)


def parse_duration_seconds(val: Any) -> int:
    """Converte timedelta, int/float, string 'HH:MM:SS'/'1 day, HH:MM:SS' ou ISO-8601 'P1DT2H' em segundos inteiros."""
    if val is None or isinstance(val, bool):
        return 0
    if isinstance(val, timedelta):
        return max(0, int(val.total_seconds()))
    if isinstance(val, (int, float)):
        return max(0, int(val))
    raw = str(val).strip()
    if not raw or raw in ("0", "None", "null"):
        return 0
    if raw.isdigit():
        return max(0, int(raw))
    m_td = _RE_TIMEDELTA_STR.match(raw)
    if m_td:
        days = int(m_td.group("days") or 0)
        hours = int(m_td.group("hours") or 0)
        mins = int(m_td.group("minutes") or 0)
        secs = int(float(m_td.group("seconds") or 0))
        return max(0, days * 86400 + hours * 3600 + mins * 60 + secs)
    m_iso = _RE_ISO_DURATION.match(raw)
    if m_iso and any(m_iso.group(k) for k in ("days", "hours", "minutes", "seconds")):
        days = int(m_iso.group("days") or 0)
        hours = int(m_iso.group("hours") or 0)
        mins = int(m_iso.group("minutes") or 0)
        secs = int(float(m_iso.group("seconds") or 0))
        return max(0, days * 86400 + hours * 3600 + mins * 60 + secs)
    try:
        return max(0, int(float(raw)))
    except (TypeError, ValueError):
        return 0


def compute_future_utc_iso(seconds_from_now: int, ref_utc: Optional[datetime] = None) -> Optional[str]:
    """Retorna o timestamp UTC ISO-8601 exato daqui a N segundos (ou None se <= 0)."""
    if not seconds_from_now or seconds_from_now <= 0:
        return None
    base = ref_utc.astimezone(timezone.utc) if ref_utc else datetime.now(timezone.utc)
    return (base + timedelta(seconds=int(seconds_from_now))).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_zzz_coffee_state(notes_zzz: Any, cur_energy: int, max_energy: int) -> str:
    """Identifica o estado do Café do ZZZ a partir da API HoYoLAB (ou overcap de bateria > max)."""
    raw_coffee = getattr(notes_zzz, "coffee", None)
    if raw_coffee is None and hasattr(notes_zzz, "model_extra") and isinstance(notes_zzz.model_extra, dict):
        raw_coffee = notes_zzz.model_extra.get("coffee")
    if isinstance(raw_coffee, bool):
        return "claimed" if raw_coffee else "available"
    if isinstance(raw_coffee, str) and raw_coffee.strip():
        low = raw_coffee.lower()
        if any(k in low for k in ("done", "claimed", "used", "yes", "true")):
            return "claimed"
        if any(k in low for k in ("no", "avail", "false", "pending")):
            return "available"
    if isinstance(raw_coffee, dict):
        if raw_coffee.get("is_claimed") or raw_coffee.get("claimed"):
            return "claimed"
        if raw_coffee.get("available") is True:
            return "available"
    # Quando a API HoYoLAB não expõe o campo coffee, overcap de bateria indica café/bateria extra ativa
    if max_energy > 0 and cur_energy > max_energy:
        return "overcap"
    return "unknown"


def _normalize_cached_notes_response(notes_map: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Garante que todas as entradas (incluindo cache SQLite) tenham recovery_seconds e full_at atualizados."""
    if not isinstance(notes_map, dict):
        return {}
    now_utc = datetime.now(timezone.utc)
    for gid, entry in notes_map.items():
        if not isinstance(entry, dict):
            continue
        extra = entry.get("extra_info")
        if not isinstance(extra, dict):
            extra = {}
            entry["extra_info"] = extra

        rec_sec = extra.get("recovery_seconds")
        if rec_sec is None:
            rec_sec = parse_duration_seconds(entry.get("recovery_time"))
            # Se veio de um cache mais antigo sem full_at, desconta o tempo decorrido desde updated_at
            upd_raw = entry.get("updated_at")
            if rec_sec > 0 and upd_raw:
                try:
                    upd_dt = datetime.fromisoformat(str(upd_raw).replace("Z", "+00:00"))
                    if upd_dt.tzinfo is None:
                        upd_dt = upd_dt.astimezone()
                    elapsed = max(0, int((now_utc - upd_dt.astimezone(timezone.utc)).total_seconds()))
                    rec_sec = max(0, rec_sec - elapsed)
                except Exception:
                    pass
        else:
            rec_sec = parse_duration_seconds(rec_sec)
            # Se já existe full_at salvo, recalcula recovery_seconds restante em relação ao agora
            full_iso = extra.get("full_at")
            if full_iso:
                try:
                    full_dt = datetime.fromisoformat(str(full_iso).replace("Z", "+00:00"))
                    if full_dt.tzinfo is None:
                        full_dt = full_dt.replace(tzinfo=timezone.utc)
                    rec_sec = max(0, int((full_dt - now_utc).total_seconds()))
                except Exception:
                    pass

        extra["recovery_seconds"] = rec_sec
        if rec_sec > 0:
            if not extra.get("full_at"):
                extra["full_at"] = compute_future_utc_iso(rec_sec, now_utc)
        else:
            extra["full_at"] = None

        entry["recovery_seconds"] = rec_sec
        entry["full_at"] = extra.get("full_at")
    return notes_map


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
            return _normalize_cached_notes_response(database.get_cached_daily_notes())
        except Exception:
            return {}

    client = genshin.Client(cookies=cookies, lang="pt-pt")

    try:
        accounts = await client.get_game_accounts()
    except Exception as e:
        print(f"Erro ao obter contas vinculadas no HoYoLAB para notas: {e}")
        try:
            return _normalize_cached_notes_response(database.get_cached_daily_notes())
        except Exception:
            return {}

    now_utc = datetime.now(timezone.utc)

    for acc in accounts:
        # 1. Genshin Impact
        if acc.game_biz.startswith("hk4e"):
            try:
                client.game = genshin.Game.GENSHIN
                notes_genshin = await client.get_genshin_notes(acc.uid)

                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(uid=str(acc.uid), game_id="genshin", nickname=acc.nickname, level=acc.level)

                resin_sec = parse_duration_seconds(getattr(notes_genshin, "remaining_resin_recovery_time", 0))
                resin_full_at = compute_future_utc_iso(resin_sec, now_utc)

                realm_rec_sec = parse_duration_seconds(
                    getattr(notes_genshin, "remaining_realm_currency_recovery_time", 0)
                )
                realm_full_at = compute_future_utc_iso(realm_rec_sec, now_utc)

                raw_transformer = getattr(notes_genshin, "remaining_transformer_recovery_time", None)
                transformer_available = raw_transformer is not None
                transformer_sec = parse_duration_seconds(raw_transformer) if transformer_available else None
                transformer_ready_at = (
                    compute_future_utc_iso(transformer_sec, now_utc)
                    if transformer_available and transformer_sec and transformer_sec > 0
                    else None
                )

                expeditions = []
                for exp_genshin in getattr(notes_genshin, "expeditions", None) or []:
                    rem_time = getattr(exp_genshin, "remaining_time", getattr(exp_genshin, "remained_time", None))
                    exp_sec = parse_duration_seconds(rem_time)
                    expeditions.append(
                        {
                            "character_icon": getattr(
                                exp_genshin,
                                "character_icon",
                                getattr(getattr(exp_genshin, "character", None), "icon", ""),
                            ),
                            "status": str(getattr(exp_genshin, "status", "")),
                            "remaining_time": str(rem_time) if rem_time is not None else "0",
                            "remaining_seconds": exp_sec,
                            "finish_at": compute_future_utc_iso(exp_sec, now_utc),
                        }
                    )

                extra_info = {
                    "recovery_seconds": resin_sec,
                    "full_at": resin_full_at,
                    "completed_commissions": int(getattr(notes_genshin, "completed_commissions", 0) or 0),
                    "max_commissions": int(getattr(notes_genshin, "max_commissions", 4) or 4),
                    "claimed_commission_reward": bool(getattr(notes_genshin, "claimed_commission_reward", False)),
                    "expeditions": expeditions,
                    "max_expeditions": int(getattr(notes_genshin, "max_expeditions", 5) or 5),
                    "remaining_resin_discounts": int(getattr(notes_genshin, "remaining_resin_discounts", 0) or 0),
                    "max_resin_discounts": int(getattr(notes_genshin, "max_resin_discounts", 3) or 3),
                    "transformer_available": transformer_available,
                    "transformer_seconds": transformer_sec,
                    "transformer_ready_at": transformer_ready_at,
                    "current_realm_currency": int(getattr(notes_genshin, "current_realm_currency", 0) or 0),
                    "max_realm_currency": int(getattr(notes_genshin, "max_realm_currency", 2400) or 2400),
                    "realm_currency_recovery_seconds": realm_rec_sec,
                    "realm_currency_full_at": realm_full_at,
                }

                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="genshin",
                    nickname=acc.nickname,
                    current_energy=notes_genshin.current_resin,
                    max_energy=notes_genshin.max_resin,
                    recovery_time=str(notes_genshin.remaining_resin_recovery_time),
                    extra_info=extra_info,
                )
            except Exception as ge:
                print(f"Erro ao obter notas do Genshin: {ge}")

        # 2. Honkai: Star Rail
        elif acc.game_biz.startswith("hkrpg"):
            try:
                client.game = genshin.Game.STARRAIL
                notes_hsr = await client.get_starrail_notes(acc.uid)

                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(uid=str(acc.uid), game_id="hsr", nickname=acc.nickname, level=acc.level)

                recovery_sec_int = parse_duration_seconds(getattr(notes_hsr, "stamina_recover_time", 0))
                hsr_full_at = compute_future_utc_iso(recovery_sec_int, now_utc)

                expeditions = []
                for exp_hsr in getattr(notes_hsr, "expeditions", None) or []:
                    rem_time = getattr(exp_hsr, "remaining_time", getattr(exp_hsr, "remained_time", None))
                    exp_sec = parse_duration_seconds(rem_time)
                    expeditions.append(
                        {
                            "name": getattr(exp_hsr, "name", "Expedição"),
                            "status": str(getattr(exp_hsr, "status", "Finished" if exp_sec == 0 else "Ongoing")),
                            "remaining_time": str(rem_time) if rem_time is not None else "0",
                            "remaining_seconds": exp_sec,
                            "finish_at": compute_future_utc_iso(exp_sec, now_utc),
                        }
                    )

                extra_info = {
                    "recovery_seconds": recovery_sec_int,
                    "full_at": hsr_full_at,
                    "expeditions": expeditions,
                    "accepted_expedition_num": int(
                        getattr(notes_hsr, "accepted_expedition_num", len(expeditions)) or 0
                    ),
                    "total_expedition_num": int(getattr(notes_hsr, "total_expedition_num", 4) or 4),
                    "current_train_score": int(getattr(notes_hsr, "current_train_score", 0) or 0),
                    "max_train_score": int(getattr(notes_hsr, "max_train_score", 500) or 500),
                    "current_rogue_score": int(getattr(notes_hsr, "current_rogue_score", 0) or 0),
                    "max_rogue_score": int(getattr(notes_hsr, "max_rogue_score", 14000) or 14000),
                    "current_reserve_stamina": int(getattr(notes_hsr, "current_reserve_stamina", 0) or 0),
                    "max_reserve_stamina": 2400,
                    "is_reserve_stamina_full": bool(getattr(notes_hsr, "is_reserve_stamina_full", False)),
                    "remaining_weekly_discounts": int(getattr(notes_hsr, "remaining_weekly_discounts", 0) or 0),
                    "max_weekly_discounts": int(getattr(notes_hsr, "max_weekly_discounts", 3) or 3),
                }

                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="hsr",
                    nickname=acc.nickname,
                    current_energy=notes_hsr.current_stamina,
                    max_energy=notes_hsr.max_stamina,
                    recovery_time=str(recovery_sec_int),
                    extra_info=extra_info,
                )
            except Exception as he:
                print(f"Erro ao obter notas do HSR: {he}")

        # 3. Zenless Zone Zero
        elif acc.game_biz.startswith("nap"):
            try:
                client.game = genshin.Game.ZZZ
                notes_zzz = await client.get_zzz_notes(acc.uid)

                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(uid=str(acc.uid), game_id="zzz", nickname=acc.nickname, level=acc.level)

                battery = getattr(notes_zzz, "battery_charge", None)
                cur_battery = int(getattr(battery, "current", 0) if battery is not None else 0)
                max_battery = int(getattr(battery, "max", 240) if battery is not None else 240)
                recovery_sec_int = parse_duration_seconds(
                    getattr(battery, "seconds_till_full", 0) if battery is not None else 0
                )
                zzz_full_at = compute_future_utc_iso(recovery_sec_int, now_utc)

                eng_obj = getattr(notes_zzz, "engagement", None)
                eng_cur = int(getattr(eng_obj, "current", eng_obj or 0) if hasattr(eng_obj, "current") else (eng_obj or 0))
                eng_max = int(getattr(eng_obj, "max", 400) if hasattr(eng_obj, "max") else 400)

                hz_obj = getattr(notes_zzz, "hollow_zero", None)
                bounty_obj = getattr(hz_obj, "bounty_commission", None) if hz_obj is not None else None
                bounty_cur = int(getattr(bounty_obj, "cur_completed", 0) or 0) if bounty_obj is not None else None
                bounty_max = int(getattr(bounty_obj, "total", 0) or 0) if bounty_obj is not None else None

                weekly_obj = getattr(notes_zzz, "weekly_task", None)
                ridu_cur = int(getattr(weekly_obj, "cur_point", 0) or 0) if weekly_obj is not None else None
                ridu_max = int(getattr(weekly_obj, "max_point", 0) or 0) if weekly_obj is not None else None

                extra_info = {
                    "recovery_seconds": recovery_sec_int,
                    "full_at": zzz_full_at,
                    "engagement": eng_cur,
                    "max_engagement": eng_max,
                    "video_store_state": str(getattr(notes_zzz, "video_store_state", "Desconhecido")),
                    "scratch_card_completed": bool(getattr(notes_zzz, "scratch_card_completed", False)),
                    "coffee_state": _extract_zzz_coffee_state(notes_zzz, cur_battery, max_battery),
                    "hollow_zero_bounty_current": bounty_cur,
                    "hollow_zero_bounty_max": bounty_max,
                    "weekly_task_current": ridu_cur,
                    "weekly_task_max": ridu_max,
                }

                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="zzz",
                    nickname=acc.nickname,
                    current_energy=cur_battery,
                    max_energy=max_battery,
                    recovery_time=str(recovery_sec_int),
                    extra_info=extra_info,
                )
            except Exception as ze:
                print(f"Erro ao obter notas do ZZZ: {ze}")

    try:
        return _normalize_cached_notes_response(database.get_cached_daily_notes())
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
