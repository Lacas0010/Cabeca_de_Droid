import os
from typing import Dict, Any
import security_vault
from core.paths import (
    APP_NAME,
    PROJECT_ROOT,
    is_frozen,
    get_bundle_root,
    get_data_dir,
    get_data_path,
    get_resource_path,
    seed_bundled_resources,
    load_local_env,
)


def get_cookies() -> Dict[str, Any]:
    """Carrega cookies autenticados do cofre seguro."""
    return security_vault.load_secure_cookies()


def get_config() -> Dict[str, Any]:
    """Carrega as configurações salvas no cofre seguro."""
    return security_vault.load_secure_config()


def parse_cookie_string(raw_cookie: str) -> Dict[str, str]:
    """Realiza o parsing de uma string crua de cookies no formato key=val; ..."""
    cookies = {}
    if not raw_cookie:
        return cookies
    raw_cookie = raw_cookie.strip()
    parts = raw_cookie.split(";")
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies
