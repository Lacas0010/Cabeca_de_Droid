import json
import os
from typing import Any, Dict, Iterable, Optional

from curl_cffi import requests

from core.config import get_data_path, get_resource_path

_HOYOWIKI_SEARCH_API = "https://sg-wiki-api.hoyolab.com/hoyowiki/wapi/search"
_STARRAILRES_ITEM_API = "https://api.github.com/repos/Mar-7th/StarRailRes/contents/icon/item"

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

_HOYOWIKI_RESOURCE_QUERIES: Dict[str, Dict[str, str]] = {
    "genshin": {
        "energy": "Original Resin",
        "currency": "Primogem",
        "ticket": "Intertwined Fate",
    },
    "hsr": {
        "energy": "Trailblaze Power",
        "reserve": "Reserved Trailblaze Power",
        "currency": "Stellar Jade",
        "ticket": "Star Rail Special Pass",
    },
    "zzz": {
        "energy": "Battery Charge",
        "currency": "Polychrome",
        "ticket": "Encrypted Master Tape",
    },
}

_HSR_STARRAILRES_FALLBACK_FILES = {
    "energy": "11.png",
    "currency": "101.png",
    "ticket": "102.png",
}


def _resource_icons_json_path() -> str:
    return get_data_path(os.path.join("static_data", "resource_icons.json"))


def load_saved_resource_icons() -> Dict[str, Dict[str, str]]:
    """Carrega o manifesto consolidado static_data/resource_icons.json."""
    for path in (
        _resource_icons_json_path(),
        get_resource_path(os.path.join("static_data", "resource_icons.json")),
    ):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                continue
    return {}


def save_resource_icons(icons_map: Dict[str, Dict[str, str]]) -> str:
    """Persiste atomicamente o manifesto de ícones em static_data/resource_icons.json."""
    path = _resource_icons_json_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(icons_map, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def _is_tutorial_or_guide_entry(item: Dict[str, Any]) -> bool:
    """Identifica verbetes de tutorial/guia no HoYoWiki que usam ícone genérico em vez do ícone do item."""
    menu = item.get("menu") if isinstance(item.get("menu"), dict) else {}
    styles = [str(menu.get("style") or "").lower(), str(menu.get("name") or "").lower()]
    for sub in menu.get("sub_menus") or []:
        if isinstance(sub, dict):
            styles.append(str(sub.get("style") or "").lower())
            styles.append(str(sub.get("name") or "").lower())
    return any(tok in s for s in styles for tok in ("tutorial", "adventure_guide", "guide"))


def _query_hoyowiki_exact_icon(session: Any, wiki_app: str, keyword: str) -> Optional[str]:
    """Busca o ícone oficial na API pública do HoYoWiki priorizando o item real (rejeitando ícones de tutorial)."""
    headers = {
        **_DEFAULT_HEADERS,
        "x-rpc-language": "en-us",
        "x-rpc-wiki_app": wiki_app,
        "Referer": "https://wiki.hoyolab.com/",
    }
    try:
        resp = session.get(_HOYOWIKI_SEARCH_API, params={"keyword": keyword}, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        entries = payload.get("data", {}).get("list", []) if isinstance(payload, dict) else []
        kw_low = keyword.strip().lower()

        # Prioriza verbetes exatos que NÃO sejam tutorial/guia (ex: Materials / Teyvat's Resources)
        non_tutorial_exact = [
            item
            for item in entries
            if str(item.get("name") or "").strip().lower() == kw_low
            and str(item.get("icon_url") or "").strip().startswith("http")
            and not _is_tutorial_or_guide_entry(item)
        ]
        if non_tutorial_exact:
            return str(non_tutorial_exact[0].get("icon_url")).strip()

        for item in entries:
            name = str(item.get("name") or "").strip().lower()
            icon_url = str(item.get("icon_url") or "").strip()
            if name == kw_low and icon_url.startswith("http"):
                return icon_url
        for item in entries:
            name = str(item.get("name") or "").strip().lower()
            icon_url = str(item.get("icon_url") or "").strip()
            if kw_low in name and icon_url.startswith("http") and not _is_tutorial_or_guide_entry(item):
                return icon_url
    except Exception:
        return None
    return None


def _fetch_hsr_starrailres_fallback(session: Any, missing_keys: Iterable[str]) -> Dict[str, str]:
    """Fallback para ícones oficiais de recursos do HSR via StarRailRes GitHub API."""
    needed = {k: _HSR_STARRAILRES_FALLBACK_FILES[k] for k in missing_keys if k in _HSR_STARRAILRES_FALLBACK_FILES}
    if not needed:
        return {}
    found: Dict[str, str] = {}
    try:
        resp = session.get(_STARRAILRES_ITEM_API, headers=_DEFAULT_HEADERS, timeout=12)
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list):
                by_name = {
                    str(it.get("name") or ""): str(it.get("download_url") or "")
                    for it in items
                    if isinstance(it, dict)
                }
                for key, fname in needed.items():
                    url = by_name.get(fname, "").strip()
                    if url.startswith("http"):
                        found[key] = url
    except Exception:
        return {}
    return found


def fetch_game_resource_icons(game_id: str, session: Optional[Any] = None) -> Dict[str, str]:
    """Descobre dinamicamente os ícones oficiais de energia, moeda e passe de um jogo via HoYoWiki API."""
    g = str(game_id or "").lower().strip()
    queries = _HOYOWIKI_RESOURCE_QUERIES.get(g)
    if not queries:
        return {}

    sess = session or requests.Session(impersonate="chrome")
    found: Dict[str, str] = {}
    for res_key, kw in queries.items():
        url = _query_hoyowiki_exact_icon(sess, g, kw)
        if url:
            found[res_key] = url

    if g == "hsr":
        missing = [k for k in _HSR_STARRAILRES_FALLBACK_FILES if k not in found]
        if missing:
            for k, v in _fetch_hsr_starrailres_fallback(sess, missing).items():
                found.setdefault(k, v)

    return found


def sync_resource_icons(
    games: Optional[Iterable[str]] = None,
    session: Optional[Any] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Descobre dinamicamente os ícones oficiais de Energia (Resina/Poder/Bateria), Moedas e Passes
    via API oficial do HoYoWiki e consolida automaticamente em static_data/resource_icons.json.
    """
    target_games = [str(g).lower().strip() for g in (games or ("genshin", "hsr", "zzz"))]
    existing = load_saved_resource_icons()
    merged: Dict[str, Dict[str, str]] = {
        g: dict(v) for g, v in existing.items() if isinstance(v, dict)
    }

    sess = session or requests.Session(impersonate="chrome")
    for g in target_games:
        fetched = fetch_game_resource_icons(g, session=sess)
        if fetched:
            merged.setdefault(g, {})
            for res_key, url in fetched.items():
                if url and isinstance(url, str) and url.startswith("http"):
                    merged[g][res_key] = url

    if merged:
        save_resource_icons(merged)
    return merged
