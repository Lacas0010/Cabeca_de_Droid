import asyncio
from fastapi import APIRouter, BackgroundTasks

import security_vault
from core.config import get_cookies, get_config, parse_cookie_string
from schemas.config import ConfigSaveRequest, NotificationTestRequest
from notifications import notifier
from auth import capturar_cookies_hoyolab

router = APIRouter(tags=["Config & Notifications"])

@router.get("/api/config")
async def get_configuration():
    """Retorna as configurações sanitizadas e o resumo criptografado dos cookies."""
    cookies_dict = get_cookies()
    config_dict = get_config()
    
    cookies_summary = security_vault.get_masked_cookies_preview(cookies_dict)
    raw_api_key = config_dict.get("groq_api_key") or config_dict.get("gemini_api_key") or ""
    masked_key = security_vault.mask_secret_string(raw_api_key, 6, 4) if raw_api_key else ""
    
    raw_tg_token = config_dict.get("telegram_bot_token", "")
    masked_tg_token = security_vault.mask_secret_string(raw_tg_token, 4, 3) if raw_tg_token else ""

    return {
        "groq_api_key": masked_key,
        "groq_api_key_configured": bool(raw_api_key),
        "cookies_raw": "",
        "cookies_preview": cookies_summary["preview"],
        "cookies_summary": cookies_summary,
        "has_cookies": len(cookies_dict) > 0,
        "has_api_key": bool(raw_api_key),
        "auto_sync_enabled": config_dict.get("auto_sync_enabled", True),
        "auto_sync_time": config_dict.get("auto_sync_time", "04:00"),
        "auto_sync_roster": config_dict.get("auto_sync_roster", True),
        "auto_sync_guides": config_dict.get("auto_sync_guides", True),
        "last_auto_sync_date": config_dict.get("last_auto_sync_date", ""),
        "notifications_enabled": config_dict.get("notifications_enabled", False),
        "discord_webhook_url": config_dict.get("discord_webhook_url", ""),
        "telegram_bot_token": masked_tg_token,
        "telegram_bot_token_configured": bool(raw_tg_token),
        "telegram_chat_id": config_dict.get("telegram_chat_id", ""),
        "notify_on_checkin": config_dict.get("notify_on_checkin", True),
        "notify_on_energy_cap": config_dict.get("notify_on_energy_cap", True),
        "energy_cap_threshold_pct": config_dict.get("energy_cap_threshold_pct", 90),
        "notify_on_endgame": config_dict.get("notify_on_endgame", True),
        "notify_on_codes": config_dict.get("notify_on_codes", True),
        "vault_info": security_vault.get_vault_security_info()
    }

@router.post("/api/config")
async def save_configuration(req: ConfigSaveRequest):
    """Salva a chave API, cookies e configurações de agendamento e notificações de forma criptografada no cofre."""
    config = get_config()
    changed = False

    if req.groq_api_key is not None:
        key_val = req.groq_api_key.strip()
        if key_val and not key_val.startswith("***") and "REDACTED" not in key_val and "***" not in key_val:
            config["groq_api_key"] = key_val
            changed = True
        elif not key_val:
            config["groq_api_key"] = ""
            changed = True
            
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
        config["discord_webhook_url"] = req.discord_webhook_url.strip()
        changed = True
    if req.telegram_bot_token is not None:
        tg_val = req.telegram_bot_token.strip()
        if tg_val and not tg_val.startswith("***") and "***" not in tg_val:
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
    """Dispara notificações de teste em tempo real para validar o canal Discord e Telegram."""
    config = get_config()
    discord_url = req.discord_webhook_url if req.discord_webhook_url is not None and not req.discord_webhook_url.startswith("***") else config.get("discord_webhook_url", "")
    tg_token = req.telegram_bot_token if req.telegram_bot_token is not None and not req.telegram_bot_token.startswith("***") else config.get("telegram_bot_token", "")
    tg_chat = req.telegram_chat_id if req.telegram_chat_id is not None else config.get("telegram_chat_id", "")

    res = notifier.test_channels(discord_url=discord_url, tg_token=tg_token, tg_chat=tg_chat)
    return {"status": "success", "results": res}

@router.post("/api/login/auto")
async def auto_login_hoyolab(background_tasks: BackgroundTasks):
    """Dispara a janela do navegador via Playwright para capturar os cookies e salvá-los no cofre criptografado."""
    def _run_login():
        print("[INFO] Abrindo navegador Playwright para capturar cookies...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cookies_captured = loop.run_until_complete(capturar_cookies_hoyolab())
            loop.close()
            
            if cookies_captured:
                security_vault.save_secure_cookies(cookies_captured)
                print("[SUCCESS] Cookies capturados, criptografados e salvos com sucesso no cofre DPAPI!")
        except Exception as e:
            print(f"[ERROR] Falha na captura automática de cookies: {e}")
            
    background_tasks.add_task(_run_login)
    return {"status": "started", "message": "Navegador de Login Automático iniciado em segundo plano."}
