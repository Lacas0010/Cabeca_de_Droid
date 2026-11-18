"""Injeção dinâmica de cache-busters baseados em __version__ e mtime para assets estáticos."""

import os
import re
from typing import Optional

from version import __version__

_INDEX_ASSET_RE = re.compile(
    r'(?P<attr>\b(?:src|href)=")(?P<path>(?!https?://|//|data:)[^"?]+\.(?:css|js))(?:\?v=[^"]*)?(?P<end>")'
)
_APP_MODULE_RE = re.compile(
    r'(?P<prefix>(?:import\s+|import\()\s*["\']\./modules/)(?P<file>[^"?]+\.js)(?:\?v=[^"\']*)?(?P<suffix>["\'])'
)


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
    """Retorna token único '<versao>-<mtime_ms>' (inclui submódulos quando url_path é app.js)."""
    target = _safe_asset_path(static_dir, url_path)
    mtime_ms = _file_mtime_ms(target)

    normalized = url_path.lstrip("/").removeprefix("static/")
    if normalized == "js/app.js":
        modules_dir = _safe_asset_path(static_dir, "js/modules")
        if modules_dir and os.path.isdir(modules_dir):
            try:
                for entry in os.scandir(modules_dir):
                    if entry.is_file() and entry.name.endswith(".js"):
                        mtime_ms = max(mtime_ms, _file_mtime_ms(entry.path))
            except OSError:
                pass

    return f"{__version__}-{mtime_ms}"


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
