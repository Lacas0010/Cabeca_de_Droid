import traceback
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

import database
import security_vault
from core.config import get_cookies, get_config, parse_cookie_string
from core.security import is_valid_session, create_session
from schemas.auth_security import (
    ManualCookieRequest,
    PinSetRequest,
    PinVerifyRequest,
    PinDisableRequest,
    LanToggleRequest,
)

router = APIRouter(tags=["Security & Auth"])

@router.get("/api/security/status")
async def get_security_status_endpoint(request: Request):
    """Retorna o status consolidado de segurança da aplicação."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_loopback = client_ip in ("127.0.0.1", "::1", "localhost", "testclient")
    token = request.cookies.get("hoyo_session") or request.headers.get("X-Session-Token")
    is_auth = is_valid_session(token)
    
    sec_settings = database.get_security_settings()
    vault_info = security_vault.get_vault_security_info()
    cookies = get_cookies()
    preview = security_vault.get_masked_cookies_preview(cookies)
    
    return {
        "status": "success",
        "storage_backend": vault_info.get("engine", "Windows DPAPI (Hardware-Tied User Key)"),
        "dpapi_available": vault_info.get("is_windows", False),
        "pin_enabled": sec_settings.get("pin_enabled", False),
        "is_authenticated": is_auth or not sec_settings.get("pin_enabled", False),
        "allow_lan_access": sec_settings.get("allow_lan_access", False),
        "client_ip": client_ip,
        "is_local_client": is_loopback,
        "vault_info": vault_info,
        "cookies_summary": preview
    }

@router.post("/api/security/pin/set")
async def set_security_pin_endpoint(req: PinSetRequest):
    """Configura ou atualiza o PIN local de proteção."""
    clean_pin = str(req.pin).strip()
    if len(clean_pin) < 4:
        raise HTTPException(status_code=400, detail="O PIN deve ter no mínimo 4 dígitos.")
    success = database.set_security_pin(clean_pin)
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao gravar PIN de segurança.")
    token = create_session()
    resp = JSONResponse({"status": "ok", "message": "PIN de segurança ativado com sucesso!", "token": token})
    resp.set_cookie(key="hoyo_session", value=token, httponly=True, samesite="strict", max_age=86400)
    return resp

@router.post("/api/security/pin/verify")
async def verify_security_pin_endpoint(req: PinVerifyRequest):
    """Valida o PIN digitado pelo usuário e emite token de sessão para desbloqueio."""
    valid = database.verify_security_pin_attempt(req.pin)
    if not valid:
        raise HTTPException(status_code=401, detail="PIN incorreto. Tente novamente.")
    token = create_session()
    resp = JSONResponse({"status": "ok", "message": "Autenticado com sucesso!", "token": token})
    resp.set_cookie(key="hoyo_session", value=token, httponly=True, samesite="strict", max_age=86400)
    return resp

@router.post("/api/security/pin/disable")
async def disable_security_pin_endpoint(req: PinDisableRequest):
    """Desativa o PIN após confirmação do PIN atual se fornecido."""
    success = database.disable_security_pin(req.current_pin)
    if not success:
        raise HTTPException(status_code=401, detail="PIN atual incorreto. Não foi possível desativar.")
    return {"status": "ok", "message": "Bloqueio por PIN desativado com sucesso."}

@router.post("/api/security/lan/toggle")
async def toggle_lan_access_endpoint(req: LanToggleRequest):
    """Ativa ou desativa a permissão para acesso de outros dispositivos na rede local."""
    val = req.enabled if req.enabled is not None else bool(req.allow_lan)
    database.set_lan_access(val)
    return {"status": "ok", "allow_lan_access": val, "message": f"Acesso na rede local {'ativado' if val else 'desativado'}."}

@router.post("/api/security/clear_credentials")
async def clear_credentials_endpoint():
    """Remove permanentemente do cofre local todos os cookies e chaves de IA."""
    security_vault.save_secure_cookies({})
    config = get_config()
    config["groq_api_key"] = ""
    config["gemini_api_key"] = ""
    security_vault.save_secure_config(config)
    return {"status": "success", "message": "Credenciais e cookies locais removidos com sucesso!"}

@router.post("/api/auth/manual_cookies")
async def save_manual_cookies(req: ManualCookieRequest):
    """Permite salvar cookies colados manualmente pelo usuário de forma criptografada no cofre."""
    try:
        parsed = parse_cookie_string(req.cookie_string)
        if not parsed or not any(k in parsed for k in ["ltuid_v2", "ltoken_v2", "ltuid", "ltoken", "cookie_token_v2", "cookie_token"]):
            raise HTTPException(status_code=400, detail="String de cookie inválida ou sem os parâmetros de autenticação HoYoLAB.")
            
        security_vault.save_secure_cookies(parsed)
        preview = security_vault.get_masked_cookies_preview(parsed)
        return {
            "status": "success",
            "message": "Cookies criptografados e salvos com sucesso no cofre seguro!",
            "keys": list(parsed.keys()),
            "preview": preview["preview"]
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
