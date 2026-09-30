import time
from typing import Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
import security_vault
import database

# Gestão de Sessões Ativas para PIN e Autenticação
active_sessions: Dict[str, float] = {}

def create_session() -> str:
    """Cria e registra um token efêmero de sessão para desbloqueio local."""
    token = security_vault.generate_session_token()
    active_sessions[token] = time.time() + 86400  # 24 horas de validade
    return token

def is_valid_session(token: Optional[str]) -> bool:
    """Verifica a validade do token de sessão ativo."""
    if not token or token not in active_sessions:
        return False
    if time.time() > active_sessions[token]:
        del active_sessions[token]
        return False
    return True

async def security_guard_middleware(request: Request, call_next):
    """Middleware de controle de acesso de rede (LAN), isolamento de rotas e bloqueio por PIN."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_loopback = client_ip in ("127.0.0.1", "::1", "localhost", "testclient")
    path = request.url.path
    
    # 1. Proteção de Rede LAN: rejeita conexões externas se LAN estiver desativada
    if not is_loopback and not database.is_lan_access_allowed():
        return JSONResponse(
            status_code=403,
            content={"error": "Acesso de outros dispositivos na rede local (LAN) está desativado nas Configurações do servidor."}
        )
        
    # 2. Proteção de Endpoints Críticos para clientes na LAN
    if not is_loopback and path in ("/api/config", "/api/reset-data", "/api/security/clear_credentials"):
        token = request.cookies.get("hoyo_session") or request.headers.get("X-Session-Token")
        if not is_valid_session(token):
            return JSONResponse(
                status_code=401,
                content={"error": "Acesso administrativo via LAN bloqueado. Autentique-se com o PIN de segurança."}
            )

    # 3. Proteção por PIN Local (se habilitado)
    sec_settings = database.get_security_settings()
    if sec_settings.get("pin_enabled"):
        is_public = (
            path == "/"
            or path.startswith("/assets")
            or path.startswith("/static")
            or path in ("/api/security/status", "/api/security/pin/verify", "/api/proxy_image")
            or not path.startswith("/api")
        )
        if not is_public:
            token = request.cookies.get("hoyo_session") or request.headers.get("X-Session-Token")
            if not is_valid_session(token):
                return JSONResponse(
                    status_code=423,
                    content={"error": "Aplicação bloqueada por PIN. Digite seu PIN de acesso para desbloquear.", "locked": True}
                )

    response = await call_next(request)
    return response

async def add_no_cache_header(request: Request, call_next):
    """Middleware para desabilitar cache em respostas HTTP."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
