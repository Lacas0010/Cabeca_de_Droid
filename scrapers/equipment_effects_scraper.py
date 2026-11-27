import json
import os
import re
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from curl_cffi import requests

from core.config import get_data_path, get_resource_path
from extractor import clean_hoyoverse_desc

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

_HOYOWIKI_LIST_API = "https://sg-wiki-api.hoyolab.com/hoyowiki/{app}/wapi/get_entry_page_list"
_HOYOWIKI_ENTRY_API = "https://sg-wiki-api-static.hoyolab.com/hoyowiki/{app}/wapi/entry_page"

_STARRAILRES_MIRRORS = [
    "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master",
    "https://cdn.jsdelivr.net/gh/Mar-7th/StarRailRes@master",
    "https://fastly.jsdelivr.net/gh/Mar-7th/StarRailRes@master",
]

_YATTA_GI_BASE = "https://gi.yatta.moe/api/v2"

_RE_NON_ALNUM = re.compile(r"[^a-z0-9]")
_RE_HSR_PLACEHOLDER = re.compile(r"#(\d+)\[(i|f\d+)\](%?)")
_RE_ZZZ_5TUPLE = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?%?)\s*/\s*(\d+(?:[.,]\d+)?%?)\s*/\s*(\d+(?:[.,]\d+)?%?)\s*/\s*(\d+(?:[.,]\d+)?%?)\s*/\s*(\d+(?:[.,]\d+)?%?)(?!\d)"
)


def normalize_equipment_key(name: str) -> str:
    """Normaliza nome de arma ou conjunto (sem acentos, pontuação ou maiúsculas) para lookup determinístico."""
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(name))
    no_accents = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return _RE_NON_ALNUM.sub("", no_accents.lower())


def equipment_effects_json_path(game_id: str) -> str:
    g = (game_id or "").lower().strip()
    return get_data_path(os.path.join("static_data", f"{g}_equipment_effects.json"))


def load_saved_equipment_effects(game_id: str) -> Dict[str, Any]:
    """Carrega o manifesto static_data/{game_id}_equipment_effects.json se existir."""
    g = (game_id or "").lower().strip()
    if g not in ("hsr", "genshin", "zzz"):
        return {"game_id": g, "weapons": {}, "sets": {}}

    for path in (
        equipment_effects_json_path(g),
        get_resource_path(os.path.join("static_data", f"{g}_equipment_effects.json")),
    ):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("weapons", {})
                    data.setdefault("sets", {})
                    return data
            except Exception:
                continue
    return {"game_id": g, "weapons": {}, "sets": {}}


def save_equipment_effects(game_id: str, payload: Dict[str, Any]) -> str:
    """Persiste atomicamente o catálogo de efeitos em static_data/{game_id}_equipment_effects.json."""
    path = equipment_effects_json_path(game_id)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def _fetch_json(
    urls: List[str],
    headers: Optional[Dict[str, str]] = None,
    method: str = "GET",
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = 12,
    max_retries: int = 2,
) -> Optional[Any]:
    req_headers = dict(_DEFAULT_HEADERS)
    if headers:
        req_headers.update(headers)

    for url in urls:
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "POST":
                    resp = requests.post(
                        url,
                        headers=req_headers,
                        json=json_body,
                        impersonate="chrome124",
                        timeout=timeout,
                    )
                else:
                    resp = requests.get(
                        url,
                        headers=req_headers,
                        impersonate="chrome124",
                        timeout=timeout,
                    )
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code in (403, 429, 503):
                    time.sleep(0.35 * (2**attempt))
                    continue
                break
            except Exception:
                time.sleep(0.35 * (2**attempt))
    return None


def _format_hsr_param(val: Any, fmt: str, is_pct: bool) -> str:
    try:
        num = float(val)
    except (TypeError, ValueError):
        return str(val)
    if is_pct:
        num *= 100.0
    if fmt == "i":
        out = str(int(round(num)))
    else:
        dec = 1
        m_dec = re.match(r"f(\d+)", fmt)
        if m_dec:
            dec = int(m_dec.group(1))
        out = f"{num:.{dec}f}".rstrip("0").rstrip(".")
    return f"{out}%" if is_pct else out


def interpolate_hsr_desc(template: str, params: List[Any]) -> str:
    """Interpola placeholders do StarRailRes (#1[i]%, #2[f1]) usando os parâmetros do nível de sobreposição."""
    if not template:
        return ""
    if not params:
        return clean_hoyoverse_desc(template)

    def _repl(match: re.Match) -> str:
        idx = int(match.group(1)) - 1
        fmt = match.group(2)
        is_pct = bool(match.group(3))
        if 0 <= idx < len(params):
            return _format_hsr_param(params[idx], fmt, is_pct)
        return match.group(0)

    rendered = _RE_HSR_PLACEHOLDER.sub(_repl, template)
    return clean_hoyoverse_desc(rendered)


def _hsr_gender_variants(raw_name: str) -> List[str]:
    """Gera variantes masculina e feminina para nomes do StarRailRes que contenham tags {F#...}/{M#...}."""
    if not raw_name:
        return []
    s = str(raw_name)
    variants: List[str] = []
    fem = re.sub(r"\{M#[^}]*\}", "", s, flags=re.IGNORECASE)
    fem = re.sub(r"\{F#([^}]*)\}", r"\1", fem, flags=re.IGNORECASE)
    masc = re.sub(r"\{F#[^}]*\}", "", s, flags=re.IGNORECASE)
    masc = re.sub(r"\{M#([^}]*)\}", r"\1", masc, flags=re.IGNORECASE)
    for cand in (clean_hoyoverse_desc(fem), clean_hoyoverse_desc(masc), clean_hoyoverse_desc(s)):
        if cand and cand not in variants:
            variants.append(cand)
    return variants


def _sync_hsr_equipment(existing: Dict[str, Any]) -> Dict[str, Any]:
    """Sincroniza passivas de Cones de Luz (S1..S5) e efeitos de Relíquias/Ornamentos (2p/4p) via StarRailRes + HoYoWiki."""
    lc_pt = _fetch_json([f"{m}/index_min/pt/light_cones.json" for m in _STARRAILRES_MIRRORS])
    ranks_pt = _fetch_json([f"{m}/index_min/pt/light_cone_ranks.json" for m in _STARRAILRES_MIRRORS])
    relics_pt = _fetch_json([f"{m}/index_min/pt/relic_sets.json" for m in _STARRAILRES_MIRRORS])

    if not isinstance(lc_pt, dict) and not isinstance(relics_pt, dict):
        return existing

    # Aliases EN opcionais e nomes de peças individuais (fallback quando API retorna nome de peça)
    lc_en = _fetch_json([f"{m}/index_min/en/light_cones.json" for m in _STARRAILRES_MIRRORS]) or {}
    relics_en = _fetch_json([f"{m}/index_min/en/relic_sets.json" for m in _STARRAILRES_MIRRORS]) or {}
    pieces_pt = _fetch_json([f"{m}/index_min/pt/relics.json" for m in _STARRAILRES_MIRRORS]) or {}

    piece_aliases_by_set: Dict[str, List[str]] = {}
    if isinstance(pieces_pt, dict):
        for pinfo in pieces_pt.values():
            if not isinstance(pinfo, dict):
                continue
            sid = str(pinfo.get("set_id") or "")
            raw_pname = pinfo.get("name") or ""
            if sid and raw_pname:
                bucket = piece_aliases_by_set.setdefault(sid, [])
                for var_n in _hsr_gender_variants(raw_pname):
                    if var_n not in bucket:
                        bucket.append(var_n)

    weapons: Dict[str, Dict[str, Any]] = dict(existing.get("weapons") or {})
    sets_map: Dict[str, Dict[str, Any]] = dict(existing.get("sets") or {})

    if isinstance(lc_pt, dict):
        ranks_dict = ranks_pt if isinstance(ranks_pt, dict) else {}
        for lc_id, lc_info in lc_pt.items():
            if not isinstance(lc_info, dict):
                continue
            name = clean_hoyoverse_desc(lc_info.get("name") or "")
            if not name:
                continue
            key = normalize_equipment_key(name)
            if not key:
                continue

            rank_info = ranks_dict.get(str(lc_id)) or {}
            passive_name = clean_hoyoverse_desc(rank_info.get("skill") or "")
            raw_desc = str(rank_info.get("desc") or "")
            params_list = rank_info.get("params") or []

            ranks_rendered: Dict[str, str] = {}
            if raw_desc and isinstance(params_list, list) and params_list:
                for idx, p_row in enumerate(params_list[:5], start=1):
                    if isinstance(p_row, list):
                        ranks_rendered[str(idx)] = interpolate_hsr_desc(raw_desc, p_row)
            elif raw_desc:
                ranks_rendered["1"] = clean_hoyoverse_desc(raw_desc)

            aliases: List[str] = []
            en_entry = lc_en.get(str(lc_id)) if isinstance(lc_en, dict) else None
            if isinstance(en_entry, dict) and en_entry.get("name"):
                en_name = clean_hoyoverse_desc(en_entry["name"])
                if en_name and en_name.lower() != name.lower():
                    aliases.append(en_name)

            rarity_raw = lc_info.get("rarity", 4)
            try:
                rarity = int(rarity_raw)
            except (TypeError, ValueError):
                rarity = 4

            weapons[key] = {
                "id": str(lc_id),
                "name": name,
                "rarity": rarity,
                "passive_name": passive_name,
                "desc": ranks_rendered.get("1") or clean_hoyoverse_desc(lc_info.get("desc") or ""),
                "ranks": ranks_rendered,
                "aliases": aliases,
            }

    if isinstance(relics_pt, dict):
        for rs_id, rs_info in relics_pt.items():
            if not isinstance(rs_info, dict):
                continue
            raw_rs_name = rs_info.get("name") or ""
            variants = _hsr_gender_variants(raw_rs_name)
            if not variants:
                continue
            name = variants[0]
            key = normalize_equipment_key(name)
            if not key:
                continue

            desc_list = rs_info.get("desc") or []
            two_pc = clean_hoyoverse_desc(desc_list[0]) if len(desc_list) >= 1 else ""
            four_pc = clean_hoyoverse_desc(desc_list[1]) if len(desc_list) >= 2 else ""

            aliases = [v for v in variants[1:] if v.lower() != name.lower()]
            en_entry = relics_en.get(str(rs_id)) if isinstance(relics_en, dict) else None
            if isinstance(en_entry, dict) and en_entry.get("name"):
                en_name = clean_hoyoverse_desc(en_entry["name"])
                if en_name and en_name.lower() != name.lower() and en_name not in aliases:
                    aliases.append(en_name)
            for p_alias in piece_aliases_by_set.get(str(rs_id), []):
                if p_alias.lower() != name.lower() and p_alias not in aliases:
                    aliases.append(p_alias)

            sets_map[key] = {
                "id": str(rs_id),
                "name": name,
                "two_pc": two_pc,
                "four_pc": four_pc,
                "is_planar": bool(two_pc and not four_pc),
                "aliases": aliases,
            }

    # Complementa com nomes oficiais do HoYoWiki HSR (menu 108) para cobrir traduções alternativas PT-PT/PT-BR
    try:
        hw_hsr_sets = _fetch_hoyowiki_list("hsr", "108", lang="pt-pt")
        for hw_it in hw_hsr_sets:
            if not isinstance(hw_it, dict):
                continue
            hw_name = clean_hoyoverse_desc(hw_it.get("name") or "")
            if not hw_name:
                continue
            hw_key = normalize_equipment_key(hw_name)
            if not hw_key or hw_key in sets_map:
                continue
            df = hw_it.get("display_field") or {}
            two_hw = clean_hoyoverse_desc(df.get("two_set_effect") or "") if isinstance(df, dict) else ""
            four_hw = clean_hoyoverse_desc(df.get("four_set_effect") or "") if isinstance(df, dict) else ""
            if two_hw or four_hw:
                sets_map[hw_key] = {
                    "id": f"hw_{hw_it.get('entry_page_id', '')}",
                    "name": hw_name,
                    "two_pc": two_hw,
                    "four_pc": four_hw,
                    "is_planar": bool(two_hw and not four_hw),
                    "aliases": [],
                }
    except Exception:
        pass

    return {
        "game_id": "hsr",
        "source": "StarRailRes + HoYoWiki (PT-BR)",
        "updated_at": datetime.now().isoformat(),
        "weapons": weapons,
        "sets": sets_map,
    }


def _fetch_genshin_weapon_detail(wid: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    data = _fetch_json([f"{_YATTA_GI_BASE}/pt/weapon/{wid}"], timeout=10, max_retries=1)
    if not isinstance(data, dict):
        return wid, None
    payload = data.get("data")
    if not isinstance(payload, dict):
        return wid, None
    return wid, payload


def _sync_genshin_equipment(existing: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """Sincroniza passivas de Armas (R1..R5) e efeitos de Artefatos (2p/4p) de Genshin via Yatta API (PT-BR)."""
    rel_pt_resp = _fetch_json([f"{_YATTA_GI_BASE}/pt/reliquary"])
    weap_pt_resp = _fetch_json([f"{_YATTA_GI_BASE}/pt/weapon"])

    rel_pt = (rel_pt_resp or {}).get("data", {}).get("items", {}) if isinstance(rel_pt_resp, dict) else {}
    weap_pt = (weap_pt_resp or {}).get("data", {}).get("items", {}) if isinstance(weap_pt_resp, dict) else {}

    if not rel_pt and not weap_pt:
        return existing

    rel_en_resp = _fetch_json([f"{_YATTA_GI_BASE}/en/reliquary"]) or {}
    weap_en_resp = _fetch_json([f"{_YATTA_GI_BASE}/en/weapon"]) or {}
    rel_en = rel_en_resp.get("data", {}).get("items", {}) if isinstance(rel_en_resp, dict) else {}
    weap_en = weap_en_resp.get("data", {}).get("items", {}) if isinstance(weap_en_resp, dict) else {}

    weapons: Dict[str, Dict[str, Any]] = dict(existing.get("weapons") or {})
    sets_map: Dict[str, Dict[str, Any]] = dict(existing.get("sets") or {})

    # 1. Conjuntos de Artefatos (1 chamada, 100% completo)
    for rid, rinfo in (rel_pt or {}).items():
        if not isinstance(rinfo, dict):
            continue
        name = clean_hoyoverse_desc(rinfo.get("name") or "")
        if not name:
            continue
        key = normalize_equipment_key(name)
        if not key:
            continue

        affix_list = rinfo.get("affixList") or {}
        effects = []
        if isinstance(affix_list, dict):
            for ak in sorted(affix_list.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x)):
                eff_txt = clean_hoyoverse_desc(affix_list.get(ak) or "")
                if eff_txt:
                    effects.append(eff_txt)

        two_pc = effects[0] if len(effects) >= 1 else ""
        four_pc = effects[1] if len(effects) >= 2 else ""

        aliases: List[str] = []
        en_entry = rel_en.get(str(rid)) if isinstance(rel_en, dict) else None
        if isinstance(en_entry, dict) and en_entry.get("name"):
            en_name = clean_hoyoverse_desc(en_entry["name"])
            if en_name and en_name.lower() != name.lower():
                aliases.append(en_name)

        sets_map[key] = {
            "id": str(rid),
            "name": name,
            "two_pc": two_pc,
            "four_pc": four_pc,
            "aliases": aliases,
        }

    # 2. Armas (incremental: só busca detalhe de armas >= 3★ ainda sem passiva em cache, salvo force=True)
    to_fetch: List[Tuple[str, str, Dict[str, Any]]] = []
    for wid, winfo in (weap_pt or {}).items():
        if not isinstance(winfo, dict):
            continue
        name = clean_hoyoverse_desc(winfo.get("name") or "")
        if not name:
            continue
        key = normalize_equipment_key(name)
        if not key:
            continue

        try:
            rarity = int(winfo.get("rank") or 4)
        except (TypeError, ValueError):
            rarity = 4

        aliases = []
        en_entry = weap_en.get(str(wid)) if isinstance(weap_en, dict) else None
        if isinstance(en_entry, dict) and en_entry.get("name"):
            en_name = clean_hoyoverse_desc(en_entry["name"])
            if en_name and en_name.lower() != name.lower():
                aliases.append(en_name)

        cached = weapons.get(key)
        if rarity < 3:
            weapons[key] = {
                "id": str(wid),
                "name": name,
                "rarity": rarity,
                "passive_name": "",
                "desc": "",
                "ranks": {},
                "aliases": aliases,
            }
            continue

        if not force and isinstance(cached, dict) and cached.get("desc") and cached.get("ranks"):
            if aliases and not cached.get("aliases"):
                cached["aliases"] = aliases
            continue

        to_fetch.append((str(wid), key, {"id": str(wid), "name": name, "rarity": rarity, "aliases": aliases}))

    if to_fetch:
        meta_by_wid = {wid: (key, meta) for wid, key, meta in to_fetch}
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(_fetch_genshin_weapon_detail, wid): wid for wid, _, _ in to_fetch}
            for fut in as_completed(futures):
                wid = futures[fut]
                try:
                    _, det = fut.result()
                except Exception:
                    det = None
                key, meta = meta_by_wid[wid]
                passive_name = ""
                ranks_rendered: Dict[str, str] = {}

                if isinstance(det, dict):
                    affix = det.get("affix")
                    if isinstance(affix, dict) and affix:
                        first_affix = next(iter(affix.values()))
                        if isinstance(first_affix, dict):
                            passive_name = clean_hoyoverse_desc(first_affix.get("name") or "")
                            upgrades = first_affix.get("upgrade") or {}
                            if isinstance(upgrades, dict):
                                for rk_idx in sorted(
                                    upgrades.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x)
                                ):
                                    txt = clean_hoyoverse_desc(upgrades.get(rk_idx) or "")
                                    if txt:
                                        rank_num = int(rk_idx) + 1 if str(rk_idx).isdigit() else rk_idx
                                        ranks_rendered[str(rank_num)] = txt

                weapons[key] = {
                    "id": meta["id"],
                    "name": meta["name"],
                    "rarity": meta["rarity"],
                    "passive_name": passive_name,
                    "desc": ranks_rendered.get("1") or "",
                    "ranks": ranks_rendered,
                    "aliases": meta["aliases"],
                }

    return {
        "game_id": "genshin",
        "source": "Yatta API (PT-BR)",
        "updated_at": datetime.now().isoformat(),
        "weapons": weapons,
        "sets": sets_map,
    }


def _fetch_hoyowiki_list(app: str, menu_id: str, lang: str = "pt-pt") -> List[Dict[str, Any]]:
    headers = {
        "x-rpc-language": lang,
        "x-rpc-wiki_app": app,
        "Origin": "https://wiki.hoyolab.com",
        "Referer": "https://wiki.hoyolab.com/",
    }
    url = _HOYOWIKI_LIST_API.format(app=app)
    items: List[Dict[str, Any]] = []
    seen_ids = set()
    page_num = 1
    page_size = 30
    while page_num <= 25:
        resp = _fetch_json(
            [url],
            headers=headers,
            method="POST",
            json_body={"menu_id": str(menu_id), "page_num": page_num, "page_size": page_size},
            timeout=12,
        )
        if not isinstance(resp, dict) or resp.get("retcode") != 0:
            break
        data = resp.get("data") or {}
        batch = data.get("list") or []
        if not batch:
            break
        added = 0
        for it in batch:
            eid = str(it.get("entry_page_id") or "") if isinstance(it, dict) else ""
            if eid and eid in seen_ids:
                continue
            if eid:
                seen_ids.add(eid)
            items.append(it)
            added += 1
        try:
            total = int(data.get("total") or 0)
        except (TypeError, ValueError):
            total = 0
        if added == 0 or (total > 0 and len(items) >= total):
            break
        page_num += 1
    return items


def _build_zzz_rank_variants(desc: str) -> Dict[str, str]:
    ranks_rendered: Dict[str, str] = {}
    if desc and _RE_ZZZ_5TUPLE.search(desc):
        for r_idx in range(5):
            def _pick(match: re.Match, idx: int = r_idx) -> str:
                return match.group(idx + 1)

            ranks_rendered[str(r_idx + 1)] = _RE_ZZZ_5TUPLE.sub(_pick, desc)
    elif desc:
        ranks_rendered["1"] = desc
    return ranks_rendered


def _split_zzz_wengine_skill(raw_html: str) -> Tuple[str, str, Dict[str, str]]:
    """Extrai título da passiva, descrição limpa e variantes W1..W5 de equipment_skill do HoYoWiki ZZZ."""
    if not raw_html:
        return "", "", {}

    passive_name = ""
    body_html = str(raw_html)
    m_p = re.search(r"<p\b[^>]*>", body_html, re.IGNORECASE)
    if m_p:
        prefix = clean_hoyoverse_desc(body_html[: m_p.start()])
        rest = clean_hoyoverse_desc(body_html[m_p.start() :])
        if prefix:
            passive_name = prefix
            if rest.lower().startswith(prefix.lower()):
                rest = rest[len(prefix) :].lstrip(" :—-\n")
            desc = rest
        else:
            desc = rest
    else:
        desc = clean_hoyoverse_desc(body_html)

    ranks_rendered = _build_zzz_rank_variants(desc)
    return passive_name, (ranks_rendered.get("1") or desc), ranks_rendered


def _fetch_zzz_entry_page(entry_id: str, lang: str = "pt-pt") -> Tuple[str, Optional[Dict[str, Any]]]:
    headers = {
        "x-rpc-language": lang,
        "x-rpc-wiki_app": "zzz",
        "Origin": "https://wiki.hoyolab.com",
        "Referer": "https://wiki.hoyolab.com/",
    }
    url = f"{_HOYOWIKI_ENTRY_API.format(app='zzz')}?entry_page_id={entry_id}"
    data = _fetch_json([url], headers=headers, timeout=10, max_retries=1)
    if not isinstance(data, dict) or data.get("retcode") != 0:
        return entry_id, None
    page = (data.get("data") or {}).get("page")
    return entry_id, (page if isinstance(page, dict) else None)


def _extract_zzz_wengine_effect_from_page(page: Dict[str, Any]) -> Tuple[str, str, Dict[str, str]]:
    """Extrai passiva de Motores-W a partir dos módulos baseInfo/equipment_skill do entry_page HoYoWiki ZZZ."""
    passive_name = ""
    desc = ""
    ignore_keys = {
        "nome",
        "name",
        "raridade",
        "rarity",
        "ranque",
        "rank",
        "especialidade",
        "specialty",
        "atributo principal",
        "atributos avançados",
        "base stat",
        "advanced stat",
        "tipo",
        "type",
    }

    for mod in page.get("modules") or []:
        for comp in (mod.get("components") or []) if isinstance(mod, dict) else []:
            if not isinstance(comp, dict):
                continue
            cid = comp.get("component_id")
            raw_data = comp.get("data")
            if not raw_data:
                continue
            try:
                parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue

            if cid == "equipment_skill":
                skill_html = parsed.get("equipment_skill") or parsed.get("desc") or ""
                if skill_html:
                    p_n, p_d, p_r = _split_zzz_wengine_skill(str(skill_html))
                    if p_d:
                        return p_n, p_d, p_r

            if cid == "baseInfo":
                rows = parsed.get("list") or []
                expect_effect = False
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    k_raw = clean_hoyoverse_desc(str(row.get("key") or ""))
                    k_low = k_raw.lower().strip(" :")
                    vals = row.get("value") or []
                    v_txt = (
                        clean_hoyoverse_desc(" ".join(str(v) for v in vals if v))
                        if isinstance(vals, list)
                        else clean_hoyoverse_desc(str(vals))
                    )
                    if "efeito de motor" in k_low or "w-engine effect" in k_low:
                        expect_effect = True
                        if v_txt and len(v_txt) > 85 and "os seguintes efeitos" not in v_txt.lower():
                            desc = v_txt
                        continue
                    if expect_effect and v_txt:
                        passive_name = k_raw if k_low not in ignore_keys else passive_name
                        desc = v_txt
                        break
                    if not expect_effect and k_low not in ignore_keys and len(v_txt) >= 45:
                        passive_name = k_raw
                        desc = v_txt
                if desc:
                    break
        if desc:
            break

    ranks_rendered = _build_zzz_rank_variants(desc)
    return passive_name, (ranks_rendered.get("1") or desc), ranks_rendered


def _extract_zzz_disc_effects_from_page(page: Dict[str, Any]) -> Tuple[str, str]:
    two_pc = ""
    four_pc = ""
    for mod in page.get("modules") or []:
        for comp in (mod.get("components") or []) if isinstance(mod, dict) else []:
            if not isinstance(comp, dict):
                continue
            cid = comp.get("component_id")
            raw_data = comp.get("data")
            if not raw_data:
                continue
            try:
                parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue

            if cid == "reliquary_set_effect":
                t2 = clean_hoyoverse_desc(parsed.get("two_set_effect") or "")
                t4 = clean_hoyoverse_desc(parsed.get("four_set_effect") or "")
                if t2:
                    two_pc = t2
                if t4:
                    four_pc = t4
            elif cid == "baseInfo":
                for row in parsed.get("list") or []:
                    if not isinstance(row, dict):
                        continue
                    k = str(row.get("key") or "").lower().strip()
                    vals = row.get("value") or []
                    val_txt = (
                        clean_hoyoverse_desc(" ".join(str(v) for v in vals if v))
                        if isinstance(vals, list)
                        else clean_hoyoverse_desc(str(vals))
                    )
                    if not val_txt:
                        continue
                    if "2" in k and ("peça" in k or "peca" in k or "piece" in k or "pc" in k):
                        two_pc = two_pc or val_txt
                    elif "4" in k and ("peça" in k or "peca" in k or "piece" in k or "pc" in k):
                        four_pc = four_pc or val_txt
    return two_pc, four_pc


def _search_hoyowiki_entry_id(app: str, keyword: str, lang: str = "pt-pt") -> Optional[Tuple[str, str]]:
    """Busca o entry_page_id exato de um item no HoYoWiki via endpoint público /wapi/search."""
    if not keyword:
        return None
    headers = {
        "x-rpc-language": lang,
        "x-rpc-wiki_app": app,
        "Origin": "https://wiki.hoyolab.com",
        "Referer": "https://wiki.hoyolab.com/",
    }
    resp = _fetch_json(
        [f"https://sg-wiki-api.hoyolab.com/hoyowiki/wapi/search?keyword={urllib.parse.quote(keyword)}"],
        headers=headers,
        timeout=10,
        max_retries=1,
    )
    if not isinstance(resp, dict) or resp.get("retcode") != 0:
        return None
    q_norm = normalize_equipment_key(keyword)
    entries = (resp.get("data") or {}).get("list") or []
    for it in entries:
        if not isinstance(it, dict):
            continue
        nm = clean_hoyoverse_desc(it.get("name") or "")
        eid = str(it.get("entry_page_id") or "")
        if eid and normalize_equipment_key(nm) == q_norm:
            return eid, nm
    for it in entries:
        if not isinstance(it, dict):
            continue
        nm = clean_hoyoverse_desc(it.get("name") or "")
        eid = str(it.get("entry_page_id") or "")
        nm_norm = normalize_equipment_key(nm)
        if eid and nm_norm and (q_norm in nm_norm or nm_norm in q_norm):
            return eid, nm
    return None


def _backfill_zzz_missing_from_roster(
    weapons: Dict[str, Dict[str, Any]],
    sets_map: Dict[str, Dict[str, Any]],
) -> None:
    """Complementa dinamicamente via HoYoWiki Search itens do roster local e dos guias de ZZZ (PT-BR + EN aliases)."""
    # Constrói índice rápido de chaves e aliases já conhecidos para evitar buscas repetidas
    known_w_keys = set(weapons.keys())
    for wobj in weapons.values():
        if isinstance(wobj, dict):
            for al in wobj.get("aliases") or []:
                ak = normalize_equipment_key(al)
                if ak:
                    known_w_keys.add(ak)
    known_s_keys = set(sets_map.keys())
    for sobj in sets_map.values():
        if isinstance(sobj, dict):
            for al in sobj.get("aliases") or []:
                ak = normalize_equipment_key(al)
                if ak:
                    known_s_keys.add(ak)

    missing_weapons: Dict[str, Tuple[str, str]] = {}  # norm_key -> (query_name, search_lang)
    missing_sets: Dict[str, Tuple[str, str]] = {}

    # 1. Itens equipados no roster local (PT-BR)
    try:
        import database

        roster = database.get_roster_data("zzz") or []
    except Exception:
        roster = []

    for c in roster:
        w = c.get("weapon") or {}
        wn = str(w.get("name") or "").strip()
        if wn:
            wk = normalize_equipment_key(wn)
            existing_w = weapons.get(wk) or {}
            if wk and (not existing_w.get("desc") or not existing_w.get("aliases")):
                missing_weapons[wk] = (wn, "pt-pt")
        for s_lbl in c.get("sets") or []:
            s_clean = re.sub(r"^\d+\s*p\s+", "", str(s_lbl or "").strip(), flags=re.IGNORECASE).strip()
            s_clean = re.sub(r"\s*\(\d+\s*peças?\)\s*$", "", s_clean, flags=re.IGNORECASE).strip()
            if not s_clean or s_clean.lower().startswith(("nenhum", "sem ")):
                continue
            sk = normalize_equipment_key(s_clean)
            existing_s = sets_map.get(sk) or {}
            if sk and (not (existing_s.get("two_pc") or existing_s.get("four_pc")) or not existing_s.get("aliases")):
                missing_sets[sk] = (s_clean, "pt-pt")

    # 2. Itens recomendados nos guias oficiais de ZZZ (EN) ainda sem mapeamento no catálogo
    try:
        guides_dir = get_data_path(os.path.join("zzz", "guias"))
        if os.path.isdir(guides_dir):
            for fname in os.listdir(guides_dir):
                if not fname.endswith(".md"):
                    continue
                with open(os.path.join(guides_dir, fname), "r", encoding="utf-8", errors="ignore") as gf:
                    txt = gf.read()
                sec = ""
                for line in txt.splitlines():
                    ls = line.strip()
                    if ls.startswith("##"):
                        low = ls.lower()
                        if "w-engine" in low or "motor" in low:
                            sec = "w"
                        elif "disco" in low or "disc" in low:
                            sec = "s"
                        else:
                            sec = ""
                        continue
                    if sec and ls.startswith("- **"):
                        m = re.search(r"-\s*\*\*([^*]+)\*\*", ls)
                        if not m:
                            continue
                        nm = re.sub(r"\s*\([^)]*\)", "", m.group(1)).strip()
                        if not nm or len(nm) < 4 or "+" in nm:
                            continue
                        nk = normalize_equipment_key(nm)
                        if sec == "w" and nk and nk not in known_w_keys and nk not in missing_weapons:
                            missing_weapons[nk] = (nm, "en-us")
                        elif sec == "s" and nk and nk not in known_s_keys and nk not in missing_sets:
                            missing_sets[nk] = (nm, "en-us")
    except Exception:
        pass

    for wk, (wn, q_lang) in missing_weapons.items():
        found = _search_hoyowiki_entry_id("zzz", wn, lang=q_lang)
        if not found and q_lang != "en-us":
            found = _search_hoyowiki_entry_id("zzz", wn, lang="en-us")
        if not found:
            continue
        eid, found_name = found
        _, page_pt = _fetch_zzz_entry_page(eid, lang="pt-pt")
        _, page_en = _fetch_zzz_entry_page(eid, lang="en-us")
        pt_name = clean_hoyoverse_desc((page_pt or {}).get("name") or "") or (found_name if q_lang == "pt-pt" else wn)
        en_name = clean_hoyoverse_desc((page_en or {}).get("name") or "") or (found_name if q_lang == "en-us" else "")
        p_name, p_desc, p_ranks = ("", "", {})
        for pg in (page_pt, page_en):
            if isinstance(pg, dict):
                p_name, p_desc, p_ranks = _extract_zzz_wengine_effect_from_page(pg)
                if p_desc:
                    break
        target_key = normalize_equipment_key(pt_name) or wk
        existing_w = weapons.get(target_key) or weapons.get(wk) or {}
        aliases = list(existing_w.get("aliases") or [])
        for cand_al in (en_name, wn):
            if cand_al and cand_al.lower() != pt_name.lower() and cand_al not in aliases:
                aliases.append(cand_al)
        if p_desc or aliases:
            weapons[target_key] = {
                "id": eid,
                "name": pt_name,
                "rarity": existing_w.get("rarity", 4),
                "passive_name": p_name or existing_w.get("passive_name", ""),
                "desc": p_desc or existing_w.get("desc", ""),
                "ranks": p_ranks or existing_w.get("ranks", {}),
                "aliases": aliases,
            }

    for sk, (sn, q_lang) in missing_sets.items():
        found = _search_hoyowiki_entry_id("zzz", sn, lang=q_lang)
        if not found and q_lang != "en-us":
            found = _search_hoyowiki_entry_id("zzz", sn, lang="en-us")
        if not found:
            continue
        eid, found_name = found
        _, page_pt = _fetch_zzz_entry_page(eid, lang="pt-pt")
        _, page_en = _fetch_zzz_entry_page(eid, lang="en-us")
        pt_name = clean_hoyoverse_desc((page_pt or {}).get("name") or "") or (found_name if q_lang == "pt-pt" else sn)
        en_name = clean_hoyoverse_desc((page_en or {}).get("name") or "") or (found_name if q_lang == "en-us" else "")
        two_pc, four_pc = "", ""
        for pg in (page_pt, page_en):
            if isinstance(pg, dict):
                two_pc, four_pc = _extract_zzz_disc_effects_from_page(pg)
                if two_pc or four_pc:
                    break
        target_key = normalize_equipment_key(pt_name) or sk
        existing_s = sets_map.get(target_key) or sets_map.get(sk) or {}
        aliases = list(existing_s.get("aliases") or [])
        for cand_al in (en_name, sn):
            if cand_al and cand_al.lower() != pt_name.lower() and cand_al not in aliases:
                aliases.append(cand_al)
        if two_pc or four_pc or aliases:
            sets_map[target_key] = {
                "id": eid,
                "name": pt_name,
                "two_pc": two_pc or existing_s.get("two_pc", ""),
                "four_pc": four_pc or existing_s.get("four_pc", ""),
                "aliases": aliases,
            }


def _sync_zzz_equipment(existing: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """Sincroniza passivas de Motores-W (W1..W5) e efeitos de Discos de Áudio (2p/4p) via HoYoWiki ZZZ (PT-BR)."""
    wengines_pt = _fetch_hoyowiki_list("zzz", "11", lang="pt-pt")
    discs_pt = _fetch_hoyowiki_list("zzz", "12", lang="pt-pt")

    if not wengines_pt and not discs_pt:
        return existing

    # Aliases EN opcionais por entry_page_id
    wengines_en = {str(it.get("entry_page_id")): it.get("name", "") for it in _fetch_hoyowiki_list("zzz", "11", lang="en-us")}
    discs_en = {str(it.get("entry_page_id")): it.get("name", "") for it in _fetch_hoyowiki_list("zzz", "12", lang="en-us")}

    weapons: Dict[str, Dict[str, Any]] = dict(existing.get("weapons") or {})
    sets_map: Dict[str, Dict[str, Any]] = dict(existing.get("sets") or {})

    # 1. Motores-W (display_field.equipment_skill para novos + entry_page em paralelo para antigos)
    wengines_to_fetch: List[Tuple[str, str, Dict[str, Any]]] = []
    for item in wengines_pt:
        if not isinstance(item, dict):
            continue
        eid = str(item.get("entry_page_id") or "")
        name = clean_hoyoverse_desc(item.get("name") or "")
        if not name:
            continue
        key = normalize_equipment_key(name)
        if not key:
            continue

        df = item.get("display_field") or {}
        raw_skill = df.get("equipment_skill") or "" if isinstance(df, dict) else ""
        passive_name, desc, ranks_rendered = _split_zzz_wengine_skill(raw_skill)

        rarity = 4
        fv = item.get("filter_values") or {}
        if isinstance(fv, dict):
            rar_vals = ((fv.get("w_engine_rarity") or fv.get("rarity") or {}).get("values") or [])
            rar_str = " ".join(str(x).upper() for x in rar_vals)
            if "S" in rar_str:
                rarity = 5
            elif "B" in rar_str:
                rarity = 3

        aliases: List[str] = []
        en_name = clean_hoyoverse_desc(wengines_en.get(eid) or "")
        if en_name and en_name.lower() != name.lower():
            aliases.append(en_name)

        if desc:
            weapons[key] = {
                "id": eid,
                "name": name,
                "rarity": rarity,
                "passive_name": passive_name,
                "desc": desc,
                "ranks": ranks_rendered,
                "aliases": aliases,
            }
        else:
            cached = weapons.get(key)
            if not force and isinstance(cached, dict) and cached.get("desc"):
                if aliases and not cached.get("aliases"):
                    cached["aliases"] = aliases
                continue
            if eid:
                wengines_to_fetch.append((eid, key, {"id": eid, "name": name, "rarity": rarity, "aliases": aliases}))

    if wengines_to_fetch:
        meta_by_wid = {eid: (key, meta) for eid, key, meta in wengines_to_fetch}
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(_fetch_zzz_entry_page, eid): eid for eid, _, _ in wengines_to_fetch}
            for fut in as_completed(futures):
                eid = futures[fut]
                try:
                    _, page = fut.result()
                except Exception:
                    page = None
                key, meta = meta_by_wid[eid]
                p_name, p_desc, p_ranks = (
                    _extract_zzz_wengine_effect_from_page(page) if isinstance(page, dict) else ("", "", {})
                )
                if p_desc or key not in weapons:
                    weapons[key] = {
                        "id": meta["id"],
                        "name": meta["name"],
                        "rarity": meta["rarity"],
                        "passive_name": p_name,
                        "desc": p_desc,
                        "ranks": p_ranks,
                        "aliases": meta["aliases"],
                    }

    # 2. Discos de Áudio (busca entry_page em paralelo; incremental salvo force=True)
    discs_to_fetch: List[Tuple[str, str, Dict[str, Any]]] = []
    for item in discs_pt:
        if not isinstance(item, dict):
            continue
        eid = str(item.get("entry_page_id") or "")
        name = clean_hoyoverse_desc(item.get("name") or "")
        if not name or not eid:
            continue
        key = normalize_equipment_key(name)
        if not key:
            continue

        aliases = []
        en_name = clean_hoyoverse_desc(discs_en.get(eid) or "")
        if en_name and en_name.lower() != name.lower():
            aliases.append(en_name)

        cached = sets_map.get(key)
        if not force and isinstance(cached, dict) and cached.get("two_pc") and cached.get("four_pc"):
            if aliases and not cached.get("aliases"):
                cached["aliases"] = aliases
            continue

        discs_to_fetch.append((eid, key, {"id": eid, "name": name, "aliases": aliases}))

    if discs_to_fetch:
        meta_by_eid = {eid: (key, meta) for eid, key, meta in discs_to_fetch}
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(_fetch_zzz_entry_page, eid): eid for eid, _, _ in discs_to_fetch}
            for fut in as_completed(futures):
                eid = futures[fut]
                try:
                    _, page = fut.result()
                except Exception:
                    page = None
                key, meta = meta_by_eid[eid]
                two_pc, four_pc = _extract_zzz_disc_effects_from_page(page) if isinstance(page, dict) else ("", "")
                if two_pc or four_pc or key not in sets_map:
                    sets_map[key] = {
                        "id": meta["id"],
                        "name": meta["name"],
                        "two_pc": two_pc,
                        "four_pc": four_pc,
                        "aliases": meta["aliases"],
                    }

    _backfill_zzz_missing_from_roster(weapons, sets_map)

    return {
        "game_id": "zzz",
        "source": "HoYoWiki ZZZ (PT-BR)",
        "updated_at": datetime.now().isoformat(),
        "weapons": weapons,
        "sets": sets_map,
    }


def sync_equipment_effects(
    target_games: Optional[Iterable[str]] = None,
    force: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Sincroniza dinamicamente efeitos de armas/cones/motores-W e conjuntos de artefatos/relíquias/discos
    para todos os jogos solicitados e salva em static_data/{game}_equipment_effects.json.
    """
    games = [g.lower().strip() for g in (target_games or ("hsr", "genshin", "zzz"))]
    results: Dict[str, Dict[str, Any]] = {}

    for g in games:
        if g not in ("hsr", "genshin", "zzz"):
            continue
        existing = load_saved_equipment_effects(g)
        try:
            if g == "hsr":
                updated = _sync_hsr_equipment(existing)
            elif g == "genshin":
                updated = _sync_genshin_equipment(existing, force=force)
            else:
                updated = _sync_zzz_equipment(existing, force=force)

            if updated and (updated.get("weapons") or updated.get("sets")):
                save_equipment_effects(g, updated)
            results[g] = {
                "weapons": len((updated or {}).get("weapons") or {}),
                "sets": len((updated or {}).get("sets") or {}),
                "source": (updated or {}).get("source", "Local Cache"),
            }
        except Exception as err:
            results[g] = {
                "weapons": len(existing.get("weapons") or {}),
                "sets": len(existing.get("sets") or {}),
                "source": "Local Cache (Fallback)",
                "error": str(err),
            }

    return results
