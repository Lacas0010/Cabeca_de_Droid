import threading
import time
from typing import Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
import security_vault
import database

mask_token = security_vault.mask_secret_string

# Gestão de Sessões Ativas para PIN e Autenticação
active_sessions: Dict[str, float] = {}
_SESSIONS_LOCK = threading.Lock()
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "::ffff:127.0.0.1", "localhost", "testclient"})
_LAN_PROTECTED_EXACT_PATHS = frozenset(
    {
        "/api/config",
        "/api/reset-data",
        "/api/security/clear_credentials",
        "/api/security/pin/set",
        "/api/security/pin/disable",
        "/api/security/lan/toggle",
        "/api/auth/manual_cookies",
        "/api/notifications/test",
        "/api/updater/start",
        "/api/login/auto",
    }
)


def is_loopback_ip(client_ip: Optional[str]) -> bool:
    """Retorna True se o endereço IP pertencer ao loopback local ou TestClient."""
    return (client_ip or "").strip().lower() in _LOOPBACK_HOSTS


def is_loopback_request(request: Request) -> bool:
    """Retorna True se a requisição FastAPI veio do loopback local."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return is_loopback_ip(client_ip)


def _requires_lan_session(path: str, method: str) -> bool:
    if path in _LAN_PROTECTED_EXACT_PATHS:
        return True
    if method.upper() == "DELETE" and path.startswith("/api/accounts/"):
        return True
    return False


def create_session() -> str:
    """Cria e registra um token efêmero de sessão para desbloqueio local."""
    token = security_vault.generate_session_token()
    now = time.time()
    with _SESSIONS_LOCK:
        if len(active_sessions) > 64:
            expired = [k for k, exp in active_sessions.items() if now > exp]
            for k in expired:
                del active_sessions[k]
        active_sessions[token] = now + 86400  # 24 horas de validade
    return token


def is_valid_session(token: Optional[str]) -> bool:
    """Verifica a validade do token de sessão ativo."""
    if not token:
        return False
    now = time.time()
    with _SESSIONS_LOCK:
        exp = active_sessions.get(token)
        if exp is None:
            return False
        if now > exp:
            del active_sessions[token]
            return False
        return True


async def security_guard_middleware(request: Request, call_next):
    """Middleware de controle de acesso de rede (LAN), isolamento de rotas e bloqueio por PIN."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_loopback = is_loopback_ip(client_ip)
    path = request.url.path

    # 1. Proteção de Rede LAN: rejeita conexões externas se LAN estiver desativada
    if not is_loopback and not database.is_lan_access_allowed():
        return JSONResponse(
            status_code=403,
            content={
                "error": "Acesso de outros dispositivos na rede local (LAN) está desativado nas Configurações do servidor."
            },
        )

    # 2. Proteção de Endpoints Críticos/Mutadores para clientes na LAN
    if not is_loopback and _requires_lan_session(path, request.method):
        token = request.cookies.get("hoyo_session") or request.headers.get("X-Session-Token")
        if not is_valid_session(token):
            return JSONResponse(
                status_code=401,
                content={"error": "Acesso administrativo via LAN bloqueado. Autentique-se com o PIN de segurança."},
            )

    # 3. Proteção por PIN Local (se habilitado)
    sec_settings = database.get_security_settings()
    if sec_settings.get("pin_enabled"):
        is_public = (
            path == "/"
            or path.startswith("/assets")
            or path.startswith("/static")
            or path in (
                "/api/security/status",
                "/api/security/pin/verify",
                "/api/proxy_image",
                "/api/system/heartbeat",
                "/api/system/disconnect",
            )
            or not path.startswith("/api")
        )
        if not is_public:
            token = request.cookies.get("hoyo_session") or request.headers.get("X-Session-Token")
            if not is_valid_session(token):
                return JSONResponse(
                    status_code=423,
                    content={
                        "error": "Aplicação bloqueada por PIN. Digite seu PIN de acesso para desbloquear.",
                        "locked": True,
                    },
                )

    response = await call_next(request)
    return response


async def add_no_cache_header(request: Request, call_next):
    """Middleware para gerenciar cache HTTP (permite cache em estáticos e protege rotas dinâmicas)."""
    response = await call_next(request)
    path = request.url.path.lower()

    is_static = (
        path.startswith("/assets")
        or path.startswith("/static")
        or path.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".woff2", ".woff", ".ttf"))
    )
    is_app_entrypoint = path in ("/js/app.js", "/static/js/app.js")
    is_proxy_image = path.startswith("/api/proxy_image")

    if is_proxy_image:
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "public, max-age=604800"
        response.headers["CDN-Cache-Control"] = "public, max-age=2592000"
    elif is_static and path != "/" and not path.endswith(".html") and not is_app_entrypoint:
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "public, max-age=86400"
            response.headers["CDN-Cache-Control"] = "public, max-age=2592000"
        if "Pragma" in response.headers and "no-store" not in response.headers.get("Cache-Control", ""):
            del response.headers["Pragma"]
        if "Expires" in response.headers and "no-store" not in response.headers.get("Cache-Control", ""):
            del response.headers["Expires"]
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
