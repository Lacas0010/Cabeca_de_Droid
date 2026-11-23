import asyncio
import json
import os
import re
from typing import Any, Dict, Iterable, Optional

from curl_cffi import requests

from core.config import get_cookies, get_data_path, get_resource_path

_STARRAILRES_SIGN_API = "https://api.github.com/repos/Mar-7th/StarRailRes/contents/icon/sign"
_HOYOWIKI_SEARCH_API = "https://sg-wiki-api.hoyolab.com/hoyowiki/wapi/search"
_ZZZ_INDEX_API = "https://sg-public-api.hoyolab.com/event/game_record_zzz/api/zzz/index"

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

_HSR_STARRAILRES_FILES = {
    "moc": "AbyssIcon01.png",
    "pure_fiction": "ChallengeStory.png",
    "apocalyptic_shadow": "ChallengeBoss.png",
}

_HOYOWIKI_MODE_QUERIES = {
    "hsr": {
        "moc": "Memory of Chaos",
        "pure_fiction": "Pure Fiction",
        "apocalyptic_shadow": "Apocalyptic Shadow",
    },
    "genshin": {
        "spiral_abyss": "Spiral Abyss",
        "imaginarium_theater": "Imaginarium Theater",
    },
}


def _endgame_icons_json_path() -> str:
    return get_data_path(os.path.join("static_data", "endgame_icons.json"))


def load_saved_endgame_icons() -> Dict[str, Dict[str, str]]:
    """Carrega o manifesto consolidado de ícones de endgame (data dir com fallback resource dir)."""
    for path in (
        _endgame_icons_json_path(),
        get_resource_path(os.path.join("static_data", "endgame_icons.json")),
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


def save_endgame_icons(icons_map: Dict[str, Dict[str, str]]) -> str:
    """Persiste atomicamente o manifesto de ícones de endgame em static_data/endgame_icons.json."""
    path = _endgame_icons_json_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(icons_map, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def _query_hoyowiki_icon(session: Any, wiki_app: str, keyword: str) -> Optional[str]:
    """Consulta a API pública oficial do HoYoWiki e retorna o icon_url do verbete exato."""
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
        for item in entries:
            name = str(item.get("name") or "").strip().lower()
            icon_url = str(item.get("icon_url") or "").strip()
            if name == kw_low and icon_url.startswith("http"):
                return icon_url
        for item in entries:
            name = str(item.get("name") or "").strip().lower()
            icon_url = str(item.get("icon_url") or "").strip()
            if kw_low in name and icon_url.startswith("http"):
                return icon_url
    except Exception:
        return None
    return None


def fetch_hsr_endgame_icons(session: Optional[Any] = None) -> Dict[str, str]:
    """Busca ícones oficiais de MoC, Ficção Pura e Sombra Apocalíptica via StarRailRes e HoYoWiki API."""
    sess = session or requests.Session(impersonate="chrome")
    found: Dict[str, str] = {}

    # 1. API oficial de datamine StarRailRes (ícones transparentes nítidos do jogo)
    try:
        resp = sess.get(_STARRAILRES_SIGN_API, headers=_DEFAULT_HEADERS, timeout=10)
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list):
                by_name = {
                    str(it.get("name") or ""): str(it.get("download_url") or "")
                    for it in items
                    if isinstance(it, dict)
                }
                for mode_id, fname in _HSR_STARRAILRES_FILES.items():
                    url = by_name.get(fname, "").strip()
                    if url.startswith("http"):
                        found[mode_id] = url
    except Exception:
        pass

    # 2. Fallback via API oficial do HoYoWiki para qualquer modo não encontrado
    for mode_id, query in _HOYOWIKI_MODE_QUERIES["hsr"].items():
        if mode_id not in found:
            wiki_url = _query_hoyowiki_icon(sess, "hsr", query)
            if wiki_url:
                found[mode_id] = wiki_url

    return found


def fetch_genshin_endgame_icons(session: Optional[Any] = None) -> Dict[str, str]:
    """Busca ícones oficiais de Abismo Espiral e Teatro Imaginário via API oficial do HoYoWiki."""
    sess = session or requests.Session(impersonate="chrome")
    found: Dict[str, str] = {}
    for mode_id, query in _HOYOWIKI_MODE_QUERIES["genshin"].items():
        wiki_url = _query_hoyowiki_icon(sess, "genshin", query)
        if wiki_url:
            found[mode_id] = wiki_url
    return found


def _recognize_zzz_server(uid: str) -> str:
    clean = str(uid or "").strip()
    if clean.startswith("10"):
        return "prod_gf_us"
    if clean.startswith("13"):
        return "prod_gf_jp"
    if clean.startswith("15"):
        return "prod_gf_eu"
    if clean.startswith("17"):
        return "prod_gf_sg"
    return "prod_gf_us"


def _extract_zzz_icons_from_medals(medals: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    """Extrai ícones de Defesa Shiyu e Assalto Mortal da lista oficial de medalhas da HoYoLAB."""
    found: Dict[str, str] = {}
    for medal in medals or []:
        if not isinstance(medal, dict):
            continue
        mtype = str(medal.get("medal_type") or "").lower()
        mname = str(medal.get("medal_name") or medal.get("name") or "").lower()
        icon = str(medal.get("medal_icon") or "").strip()
        if not icon.startswith("http"):
            continue

        if "shiyu_defense" not in found and (
            ("hadal" in mtype and "memhadal" not in mtype) or "shiyu" in mname
        ):
            found["shiyu_defense"] = icon
        elif "deadly_assault" not in found and (
            "memhadal" in mtype
            or "deadly assault" in mname
            or "assalto mortal" in mname
            or "investida fatal" in mname
        ):
            found["deadly_assault"] = icon
    return found


async def fetch_zzz_endgame_icons_async(
    client: Optional[Any] = None,
    uid: Optional[str] = None,
) -> Dict[str, str]:
    """Busca os emblemas oficiais de Defesa Shiyu e Assalto Mortal na API HoYoLAB ZZZ Index."""
    own_client = client is None
    if own_client:
        cookies = get_cookies()
        if not cookies:
            return {}
        try:
            import genshin

            client = genshin.Client(cookies)
        except Exception:
            return {}

    target_uid = str(uid or "").strip()
    if not target_uid or not target_uid.isdigit():
        try:
            import database

            target_uid = str(database.get_active_uid("zzz") or "").strip()
        except Exception:
            target_uid = ""
    if not target_uid or not target_uid.isdigit():
        try:
            import genshin

            accounts = await client.get_game_accounts()
            for acc in accounts:
                if getattr(acc, "game", None) == genshin.Game.ZZZ:
                    target_uid = str(acc.uid)
                    break
        except Exception:
            return {}

    if not target_uid or not target_uid.isdigit():
        return {}

    try:
        raw = await client.request_hoyolab(
            _ZZZ_INDEX_API,
            params={"role_id": int(target_uid), "server": _recognize_zzz_server(target_uid)},
        )
        gds = raw.get("game_data_show", {}) if isinstance(raw, dict) else {}
        medals = list(gds.get("all_medal_list") or []) + list(gds.get("medal_item_list") or [])
        return _extract_zzz_icons_from_medals(medals)
    except Exception:
        return {}


def fetch_zzz_endgame_icons(uid: Optional[str] = None) -> Dict[str, str]:
    """Wrapper síncrono para busca dos ícones oficiais de endgame do ZZZ via HoYoLAB API."""
    try:
        asyncio.get_running_loop()
        # Evita RuntimeError se chamado dentro de um loop ativo (nesse caso, usar fetch_zzz_endgame_icons_async)
        return {}
    except RuntimeError:
        pass
    try:
        return asyncio.run(fetch_zzz_endgame_icons_async(uid=uid))
    except Exception:
        return {}


def sync_endgame_icons(
    games: Optional[Iterable[str]] = None,
    uid_by_game: Optional[Dict[str, str]] = None,
    session: Optional[Any] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Descobre dinamicamente os ícones oficiais dos modos de endgame via APIs (StarRailRes, HoYoWiki, HoYoLAB)
    e consolida automaticamente em static_data/endgame_icons.json.
    """
    target_games = [str(g).lower().strip() for g in (games or ("hsr", "genshin", "zzz"))]
    existing = load_saved_endgame_icons()
    merged: Dict[str, Dict[str, str]] = {
        g: dict(v) for g, v in existing.items() if isinstance(v, dict)
    }

    sess = session or requests.Session(impersonate="chrome")
    uid_map = uid_by_game or {}

    for g in target_games:
        fetched: Dict[str, str] = {}
        if g == "hsr":
            fetched = fetch_hsr_endgame_icons(session=sess)
        elif g == "genshin":
            fetched = fetch_genshin_endgame_icons(session=sess)
        elif g == "zzz":
            fetched = fetch_zzz_endgame_icons(uid=uid_map.get("zzz"))

        if fetched:
            merged.setdefault(g, {})
            for mode_id, url in fetched.items():
                if url and isinstance(url, str) and url.startswith("http"):
                    merged[g][mode_id] = url

    if merged:
        save_endgame_icons(merged)
    return merged
