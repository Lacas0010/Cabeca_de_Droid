import json
import os
import re
from typing import Any, Dict, Iterable, Optional

from curl_cffi import requests

from core.config import get_data_path, get_resource_path

_STARRAILRES_PATH_API = "https://api.github.com/repos/Mar-7th/StarRailRes/contents/icon/path"
_PRYDWEN_PAGES = {
    "hsr": "https://www.prydwen.gg/star-rail/characters/",
    "genshin": "https://www.prydwen.gg/genshin-impact/characters/",
    "zzz": "https://www.prydwen.gg/zenless/characters/",
}

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
}

_HSR_STARRAILRES_FILES = {
    "destruction": "Destruction.png",
    "hunt": "Hunt.png",
    "erudition": "Erudition.png",
    "harmony": "Harmony.png",
    "nihility": "Nihility.png",
    "preservation": "Preservation.png",
    "abundance": "Abundance.png",
    "remembrance": "Remembrance.png",
    "elation": "Elation.png",
}

_PRYDWEN_SLUG_NORMALIZATION = {
    "hsr": {
        "prefix": "path_",
        "aliases": {
            "remem": "remembrance",
            "remembrance": "remembrance",
            "destruction": "destruction",
            "hunt": "hunt",
            "erudition": "erudition",
            "harmony": "harmony",
            "nihility": "nihility",
            "preservation": "preservation",
            "abundance": "abundance",
            "elation": "elation",
        },
    },
    "genshin": {
        "prefix": "weapon_",
        "aliases": {
            "sword": "sword",
            "claymore": "claymore",
            "polearm": "polearm",
            "bow": "bow",
            "catalyst": "catalyst",
        },
    },
    "zzz": {
        "prefix": "style_",
        "aliases": {
            "attack": "attack",
            "stun": "stun",
            "anomaly": "anomaly",
            "support": "support",
            "defence": "defense",
            "defense": "defense",
            "rupture": "rupture",
            "armorer": "armorer",
        },
    },
}

_RE_PRYDWEN_ICON = re.compile(
    r"https://cdn\.prydwen\.gg/images/[a-z0-9-]+/icons/([a-z0-9_]+)\.(?:webp|png|svg)",
    re.IGNORECASE,
)


def _role_icons_json_path() -> str:
    return get_data_path(os.path.join("static_data", "role_icons.json"))


def load_saved_role_icons() -> Dict[str, Dict[str, str]]:
    """Carrega o manifesto consolidado de ícones de caminhos, armas e especialidades."""
    for path in (
        _role_icons_json_path(),
        get_resource_path(os.path.join("static_data", "role_icons.json")),
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


def save_role_icons(icons_map: Dict[str, Dict[str, str]]) -> str:
    """Persiste atomicamente o manifesto consolidado em static_data/role_icons.json."""
    path = _role_icons_json_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(icons_map, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def _fetch_prydwen_role_icons(game_id: str, session: Any) -> Dict[str, str]:
    """Extrai dinamicamente URLs oficiais de ícones (path_/weapon_/style_) da página de catálogo Prydwen."""
    url = _PRYDWEN_PAGES.get(game_id)
    spec = _PRYDWEN_SLUG_NORMALIZATION.get(game_id)
    if not url or not spec:
        return {}
    prefix = spec["prefix"]
    aliases = spec["aliases"]
    found: Dict[str, str] = {}
    try:
        resp = session.get(url, headers=_DEFAULT_HEADERS, timeout=15)
        if resp.status_code != 200:
            return {}
        for m in _RE_PRYDWEN_ICON.finditer(resp.text):
            full_url = m.group(0)
            stem = m.group(1).lower()
            if not stem.startswith(prefix):
                continue
            raw_key = stem[len(prefix) :]
            canonical = aliases.get(raw_key)
            if canonical and canonical not in found:
                found[canonical] = full_url
    except Exception:
        return {}
    return found


def fetch_hsr_path_icons(session: Optional[Any] = None) -> Dict[str, str]:
    """Busca ícones oficiais HD de Caminhos do HSR via StarRailRes API com fallback Prydwen."""
    sess = session or requests.Session(impersonate="chrome")
    found: Dict[str, str] = {}

    try:
        resp = sess.get(_STARRAILRES_PATH_API, headers=_DEFAULT_HEADERS, timeout=12)
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list):
                by_name = {
                    str(it.get("name") or ""): str(it.get("download_url") or "")
                    for it in items
                    if isinstance(it, dict)
                }
                for canonical, fname in _HSR_STARRAILRES_FILES.items():
                    url = by_name.get(fname, "").strip()
                    if url.startswith("http"):
                        found[canonical] = url
    except Exception:
        pass

    if len(found) < len(_HSR_STARRAILRES_FILES):
        fallback = _fetch_prydwen_role_icons("hsr", sess)
        for k, v in fallback.items():
            found.setdefault(k, v)

    return found


def fetch_genshin_weapon_icons(session: Optional[Any] = None) -> Dict[str, str]:
    """Busca dinamicamente os ícones oficiais de Tipos de Arma do Genshin Impact."""
    sess = session or requests.Session(impersonate="chrome")
    return _fetch_prydwen_role_icons("genshin", sess)


def fetch_zzz_specialty_icons(session: Optional[Any] = None) -> Dict[str, str]:
    """Busca dinamicamente os ícones oficiais de Especialidades de Agentes do ZZZ."""
    sess = session or requests.Session(impersonate="chrome")
    return _fetch_prydwen_role_icons("zzz", sess)


def sync_role_icons(
    games: Optional[Iterable[str]] = None,
    session: Optional[Any] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Extrai dinamicamente os ícones oficiais de Caminhos (HSR), Armas (Genshin) e Especialidades (ZZZ)
    e consolida automaticamente em static_data/role_icons.json sem perder entradas válidas em falhas de rede.
    """
    target_games = [str(g).lower().strip() for g in (games or ("hsr", "genshin", "zzz"))]
    existing = load_saved_role_icons()
    merged: Dict[str, Dict[str, str]] = {
        g: dict(v) for g, v in existing.items() if isinstance(v, dict)
    }

    sess = session or requests.Session(impersonate="chrome")
    for g in target_games:
        fetched: Dict[str, str] = {}
        if g == "hsr":
            fetched = fetch_hsr_path_icons(session=sess)
        elif g == "genshin":
            fetched = fetch_genshin_weapon_icons(session=sess)
        elif g == "zzz":
            fetched = fetch_zzz_specialty_icons(session=sess)

        if fetched:
            merged.setdefault(g, {})
            for role_key, url in fetched.items():
                if url and isinstance(url, str) and url.startswith("http"):
                    merged[g][role_key] = url

    if merged:
        save_role_icons(merged)
    return merged
