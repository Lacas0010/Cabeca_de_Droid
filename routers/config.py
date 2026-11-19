import asyncio
import threading
from fastapi import APIRouter, BackgroundTasks, Request

import security_vault
from core.config import get_cookies, get_config, parse_cookie_string
from core.security import is_loopback_request
from schemas.config import ConfigSaveRequest, NotificationTestRequest
from notifications import notifier
from auth import capturar_cookies_hoyolab

router = APIRouter(tags=["Config & Notifications"])


def _is_masked_secret(value: str) -> bool:
    return "***" in value or value.startswith("***")


@router.get("/api/config")
async def get_configuration(request: Request):
    """Retorna as configurações sanitizadas e o resumo criptografado dos cookies."""
    cookies_dict = get_cookies()
    config_dict = get_config()

    cookies_summary = security_vault.get_masked_cookies_preview(cookies_dict)

    raw_tg_token = config_dict.get("telegram_bot_token", "")
    masked_tg_token = security_vault.mask_secret_string(raw_tg_token, 4, 3) if raw_tg_token else ""

    raw_discord_url = config_dict.get("discord_webhook_url", "")
    if raw_discord_url and not is_loopback_request(request):
        discord_url_out = security_vault.mask_secret_string(raw_discord_url, 12, 4)
    else:
        discord_url_out = raw_discord_url

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
        "discord_webhook_url": discord_url_out,
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


@router.post("/api/config")
async def save_configuration(req: ConfigSaveRequest):
    """Salva cookies e configurações de agendamento e notificações de forma criptografada no cofre."""
    config = get_config()
    changed = False

    if req.auto_sync_enabled is not None:
        config["auto_sync_enabled"] = req.auto_sync_enabled
        changed = True
    if req.auto_sync_time is not None:
        config["auto_sync_time"] = req.auto_sync_time.strip()
        changed = True
    if req.auto_sync_roster is not None:
        config["auto_sync_roster"] = req.auto_sync_roster
        changed = True
    if req.auto_sync_guides is not None:
        config["auto_sync_guides"] = req.auto_sync_guides
        changed = True

    # Configurações de Notificações Proativas
    if req.notifications_enabled is not None:
        config["notifications_enabled"] = req.notifications_enabled
        changed = True
    if req.discord_webhook_url is not None:
        discord_val = req.discord_webhook_url.strip()
        if discord_val and not _is_masked_secret(discord_val):
            config["discord_webhook_url"] = discord_val
            changed = True
        elif not discord_val:
            config["discord_webhook_url"] = ""
            changed = True
    if req.telegram_bot_token is not None:
        tg_val = req.telegram_bot_token.strip()
        if tg_val and not _is_masked_secret(tg_val):
            config["telegram_bot_token"] = tg_val
            changed = True
        elif not tg_val:
            config["telegram_bot_token"] = ""
            changed = True
    if req.telegram_chat_id is not None:
        config["telegram_chat_id"] = req.telegram_chat_id.strip()
        changed = True
    if req.notify_on_checkin is not None:
        config["notify_on_checkin"] = req.notify_on_checkin
        changed = True
    if req.notify_on_energy_cap is not None:
        config["notify_on_energy_cap"] = req.notify_on_energy_cap
        changed = True
    if req.energy_cap_threshold_pct is not None:
        config["energy_cap_threshold_pct"] = req.energy_cap_threshold_pct
        changed = True
    if req.notify_on_endgame is not None:
        config["notify_on_endgame"] = req.notify_on_endgame
        changed = True
    if req.notify_on_codes is not None:
        config["notify_on_codes"] = req.notify_on_codes
        changed = True
    if req.quiet_hours_enabled is not None:
        config["quiet_hours_enabled"] = req.quiet_hours_enabled
        changed = True
    if req.quiet_hours_start is not None:
        config["quiet_hours_start"] = req.quiet_hours_start.strip()
        changed = True
    if req.quiet_hours_end is not None:
        config["quiet_hours_end"] = req.quiet_hours_end.strip()
        changed = True
    if req.notify_windows_toast is not None:
        config["notify_windows_toast"] = req.notify_windows_toast
        changed = True
    if req.language is not None:
        lang_val = req.language.lower().strip()
        if lang_val in ["pt", "en"]:
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

    return {"status": "success", "message": "Configurações salvas e criptografadas localmente com segurança."}


@router.post("/api/notifications/test")
async def test_notifications_endpoint(req: NotificationTestRequest):
    """Dispara notificações de teste em tempo real para validar o canal Discord, Telegram e Windows Toast."""
    config = await asyncio.to_thread(get_config)
    discord_url = (
        req.discord_webhook_url
        if req.discord_webhook_url is not None and not _is_masked_secret(req.discord_webhook_url)
        else config.get("discord_webhook_url", "")
    )
    tg_token = (
        req.telegram_bot_token
        if req.telegram_bot_token is not None and not _is_masked_secret(req.telegram_bot_token)
        else config.get("telegram_bot_token", "")
    )
    tg_chat = req.telegram_chat_id if req.telegram_chat_id is not None else config.get("telegram_chat_id", "")
    test_win = req.test_windows if req.test_windows is not None else True

    res = await asyncio.to_thread(
        notifier.test_channels,
        discord_url=discord_url,
        tg_token=tg_token,
        tg_chat=tg_chat,
        test_windows=test_win,
    )
    return {"status": "success", "results": res}


_AUTO_LOGIN_LOCK = threading.Lock()
_AUTO_LOGIN_STATE = {"status": "idle", "error": ""}


@router.get("/api/login/auto/status")
def get_auto_login_status():
    """Retorna o estado atual da captura automática de cookies sem expor tokens."""
    with _AUTO_LOGIN_LOCK:
        return dict(_AUTO_LOGIN_STATE)


@router.post("/api/login/auto")
async def auto_login_hoyolab(background_tasks: BackgroundTasks):
    """Dispara a janela do navegador via Playwright para capturar os cookies e salvá-los no cofre criptografado."""
    with _AUTO_LOGIN_LOCK:
        if _AUTO_LOGIN_STATE["status"] == "running":
            return {"status": "running", "message": "Login automático já está em andamento."}
        _AUTO_LOGIN_STATE["status"] = "running"
        _AUTO_LOGIN_STATE["error"] = ""

    def _run_login():
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

    background_tasks.add_task(_run_login)
    return {"status": "started", "message": "Navegador de Login Automático iniciado em segundo plano."}
