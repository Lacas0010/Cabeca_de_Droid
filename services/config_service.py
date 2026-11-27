"""Serviço de configurações locais, notificações e captura de sessão HoYoLAB."""

import asyncio
import threading
from typing import Any, Dict

import security_vault
from auth import capturar_cookies_hoyolab
from core.config import get_config, get_cookies, parse_cookie_string
from core.security import mask_token
from notifications import notifier
from schemas.config import ConfigSaveRequest, NotificationTestRequest

_AUTO_LOGIN_LOCK = threading.Lock()
_AUTO_LOGIN_STATE = {"status": "idle", "error": ""}


def is_masked_secret(value: str) -> bool:
    return "***" in value or value.startswith("***")


def get_sanitized_configuration() -> Dict[str, Any]:
    """Retorna configurações sanitizadas sob premissa Zero-Exposure (tokens e webhooks sempre mascarados)."""
    cookies_dict = get_cookies()
    config_dict = get_config()

    cookies_summary = security_vault.get_masked_cookies_preview(cookies_dict)

    raw_tg_token = config_dict.get("telegram_bot_token", "")
    masked_tg_token = mask_token(raw_tg_token, 4, 3) if raw_tg_token else ""

    raw_discord_url = config_dict.get("discord_webhook_url", "")
    masked_discord_url = mask_token(raw_discord_url, 12, 4) if raw_discord_url else ""

    return {
        "cookies_raw": "",
        "cookies_preview": cookies_summary["preview"],
        "cookies_summary": cookies_summary,
        "has_cookies": len(cookies_dict) > 0,
        "auto_sync_enabled": config_dict.get("auto_sync_enabled", True),
        "auto_sync_time": config_dict.get("auto_sync_time", "04:00"),
        "auto_sync_roster": config_dict.get("auto_sync_roster", True),
        "auto_sync_guides": config_dict.get("auto_sync_guides", True),
        "last_auto_sync_date": config_dict.get("last_auto_sync_date", ""),
        "notifications_enabled": config_dict.get("notifications_enabled", False),
        "discord_webhook_url": masked_discord_url,
        "discord_webhook_url_configured": bool(raw_discord_url),
        "telegram_bot_token": masked_tg_token,
        "telegram_bot_token_configured": bool(raw_tg_token),
        "telegram_chat_id": config_dict.get("telegram_chat_id", ""),
        "notify_on_checkin": config_dict.get("notify_on_checkin", True),
        "notify_on_energy_cap": config_dict.get("notify_on_energy_cap", True),
        "energy_cap_threshold_pct": config_dict.get("energy_cap_threshold_pct", 90),
        "notify_on_endgame": config_dict.get("notify_on_endgame", True),
        "notify_on_codes": config_dict.get("notify_on_codes", True),
        "quiet_hours_enabled": config_dict.get("quiet_hours_enabled", False),
        "quiet_hours_start": config_dict.get("quiet_hours_start", "23:00"),
        "quiet_hours_end": config_dict.get("quiet_hours_end", "07:00"),
        "notify_windows_toast": config_dict.get("notify_windows_toast", True),
        "language": config_dict.get("language", "pt"),
        "vault_info": security_vault.get_vault_security_info(),
    }


def save_configuration_changes(req: ConfigSaveRequest) -> Dict[str, str]:
    """Aplica atualizações de configuração e cookies no cofre criptográfico DPAPI/AES-256."""
    config = get_config()
    changed = False

    direct_fields = (
        "auto_sync_enabled",
        "auto_sync_roster",
        "auto_sync_guides",
        "notifications_enabled",
        "notify_on_checkin",
        "notify_on_energy_cap",
        "energy_cap_threshold_pct",
        "notify_on_endgame",
        "notify_on_codes",
        "quiet_hours_enabled",
        "notify_windows_toast",
    )
    for field in direct_fields:
        val = getattr(req, field, None)
        if val is not None:
            config[field] = val
            changed = True

    stripped_fields = ("auto_sync_time", "telegram_chat_id", "quiet_hours_start", "quiet_hours_end")
    for field in stripped_fields:
        val = getattr(req, field, None)
        if val is not None:
            config[field] = val.strip()
            changed = True

    for secret_field in ("discord_webhook_url", "telegram_bot_token"):
        val = getattr(req, secret_field, None)
        if val is not None:
            clean_val = val.strip()
            if clean_val and not is_masked_secret(clean_val):
                config[secret_field] = clean_val
                changed = True
            elif not clean_val:
                config[secret_field] = ""
                changed = True

    if req.language is not None:
        lang_val = req.language.lower().strip()
        if lang_val in ("pt", "en"):
            config["language"] = lang_val
            changed = True

    if changed:
        security_vault.save_secure_config(config)

    if req.cookies_raw is not None:
        c_raw = req.cookies_raw.strip()
        if c_raw and "REDACTED" not in c_raw and "***" not in c_raw:
            cookies = parse_cookie_string(c_raw)
            if cookies:
                security_vault.save_secure_cookies(cookies)
        elif not c_raw:
            security_vault.save_secure_cookies({})

    return {"status": "success", "message": "Configurações salvas no cofre criptografado."}


def run_test_notifications(req: NotificationTestRequest) -> Dict[str, Any]:
    """Dispara notificações de teste para Discord, Telegram e Windows Toast."""
    config = get_config()
    discord_url = (
        req.discord_webhook_url
        if req.discord_webhook_url is not None and not is_masked_secret(req.discord_webhook_url)
        else config.get("discord_webhook_url", "")
    )
    tg_token = (
        req.telegram_bot_token
        if req.telegram_bot_token is not None and not is_masked_secret(req.telegram_bot_token)
        else config.get("telegram_bot_token", "")
    )
    tg_chat = req.telegram_chat_id if req.telegram_chat_id is not None else config.get("telegram_chat_id", "")
    test_win = req.test_windows if req.test_windows is not None else True

    res = notifier.test_channels(
        discord_url=discord_url,
        tg_token=tg_token,
        tg_chat=tg_chat,
        test_windows=test_win,
    )
    return {"status": "success", "results": res}


def get_auto_login_state() -> Dict[str, str]:
    with _AUTO_LOGIN_LOCK:
        return dict(_AUTO_LOGIN_STATE)


def begin_auto_login_run() -> bool:
    """Marca o início da captura de cookies; retorna False se já houver execução em andamento."""
    with _AUTO_LOGIN_LOCK:
        if _AUTO_LOGIN_STATE["status"] == "running":
            return False
        _AUTO_LOGIN_STATE["status"] = "running"
        _AUTO_LOGIN_STATE["error"] = ""
        return True


def execute_auto_login_background() -> None:
    """Executa a captura de cookies via Playwright e persiste no cofre criptografado."""
    print("[INFO] Abrindo navegador para login no HoYoLAB...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            cookies_captured = loop.run_until_complete(capturar_cookies_hoyolab())
        finally:
            loop.close()

        if cookies_captured:
            security_vault.save_secure_cookies(cookies_captured)
            with _AUTO_LOGIN_LOCK:
                _AUTO_LOGIN_STATE["status"] = "success"
                _AUTO_LOGIN_STATE["error"] = ""
            print("[SUCCESS] Cookies salvos no cofre DPAPI.")
        else:
            with _AUTO_LOGIN_LOCK:
                _AUTO_LOGIN_STATE["status"] = "error"
                _AUTO_LOGIN_STATE["error"] = "Nenhum cookie capturado."
    except Exception as e:
        with _AUTO_LOGIN_LOCK:
            _AUTO_LOGIN_STATE["status"] = "error"
            _AUTO_LOGIN_STATE["error"] = str(e)
        print(f"[ERROR] Falha no login automático: {e}")
