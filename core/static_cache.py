"""Injeção dinâmica de cache-busters baseados em __version__ e mtime para assets estáticos."""

import os
import re
import threading
import time
from typing import Dict, Optional, Tuple

from version import __version__

_INDEX_ASSET_RE = re.compile(
    r'(?P<attr>\b(?:src|href)=")(?P<path>(?!https?://|//|data:)[^"?]+\.(?:css|js))(?:\?v=[^"]*)?(?P<end>")'
)
_APP_MODULE_RE = re.compile(
    r'(?P<prefix>(?:import\s+|import\()\s*["\']\./modules/)(?P<file>[^"?]+\.js)(?:\?v=[^"\']*)?(?P<suffix>["\'])'
)

ASSET_TOKEN_TTL_SECONDS = 2.0
_CACHE_LOCK = threading.Lock()
_ASSET_TOKEN_CACHE: Dict[Tuple[str, str], Tuple[float, str]] = {}


def invalidate_static_cache() -> None:
    """Limpa o cache em memória de tokens de assets estáticos."""
    with _CACHE_LOCK:
        _ASSET_TOKEN_CACHE.clear()


def _safe_asset_path(static_dir: str, url_path: str) -> Optional[str]:
    clean = url_path.lstrip("/")
    if clean.startswith("static/"):
        clean = clean[len("static/") :]
    base_abs = os.path.abspath(static_dir)
    target_abs = os.path.abspath(os.path.join(base_abs, *clean.split("/")))
    if os.path.commonpath([base_abs, target_abs]) != base_abs:
        return None
    return target_abs


def _file_mtime_ms(path: Optional[str]) -> int:
    if not path or not os.path.isfile(path):
        return 0
    try:
        return int(os.stat(path).st_mtime_ns // 1_000_000)
    except OSError:
        return 0


def get_asset_version_token(static_dir: str, url_path: str) -> str:
    """Retorna token único '<versao>-<mtime_ms>' (com cache TTL de 2s para evitar scandir/stat repetidos)."""
    base_abs = os.path.abspath(static_dir)
    normalized = url_path.lstrip("/").removeprefix("static/")
    cache_key = (base_abs, normalized)
    now = time.monotonic()

    with _CACHE_LOCK:
        cached = _ASSET_TOKEN_CACHE.get(cache_key)
        if cached is not None and (now - cached[0]) < ASSET_TOKEN_TTL_SECONDS:
            return cached[1]

    target = _safe_asset_path(static_dir, url_path)
    mtime_ms = _file_mtime_ms(target)

    if normalized == "js/app.js":
        modules_dir = _safe_asset_path(static_dir, "js/modules")
        if modules_dir and os.path.isdir(modules_dir):
            try:
                for entry in os.scandir(modules_dir):
                    if entry.is_file() and entry.name.endswith(".js"):
                        try:
                            entry_mtime = int(entry.stat().st_mtime_ns // 1_000_000)
                            if entry_mtime > mtime_ms:
                                mtime_ms = entry_mtime
                        except OSError:
                            pass
            except OSError:
                pass

    token = f"{__version__}-{mtime_ms}"
    with _CACHE_LOCK:
        _ASSET_TOKEN_CACHE[cache_key] = (now, token)
    return token


def inject_index_cache_busters(html: str, static_dir: str) -> str:
    """Atualiza ?v= nos links CSS/JS locais de index.html usando versão e mtime reais."""

    def _replace(match: re.Match) -> str:
        asset_path = match.group("path")
        token = get_asset_version_token(static_dir, asset_path)
        return f'{match.group("attr")}{asset_path}?v={token}{match.group("end")}'

    return _INDEX_ASSET_RE.sub(_replace, html)


def inject_app_js_cache_busters(js_source: str, static_dir: str) -> str:
    """Atualiza ?v= nos imports ./modules/*.js dentro de static/js/app.js."""

    def _replace(match: re.Match) -> str:
        filename = match.group("file")
        token = get_asset_version_token(static_dir, f"js/modules/{filename}")
        return f'{match.group("prefix")}{filename}?v={token}{match.group("suffix")}'

    return _APP_MODULE_RE.sub(_replace, js_source)
