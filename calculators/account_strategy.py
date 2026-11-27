"""Diagnóstico estratégico de lacunas da conta e recomendador de síntese de equipamentos."""

import json
import os
import re
import unicodedata
from typing import Any, Dict, List

from core.paths import get_data_path, get_resource_path

_RE_NON_ALNUM = re.compile(r"[^a-z0-9]")
_RE_NUM_VAL = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")
_ELEMENTS_JSON_CACHE: Dict[str, Dict[str, str]] | None = None
_STATIC_JSON_CACHE: Dict[str, Any] = {}


def _load_static_json(filename: str) -> Any:
    """Carrega e faz cache de um manifesto JSON de static_data/."""
    if filename in _STATIC_JSON_CACHE:
        return _STATIC_JSON_CACHE[filename]
    rel = os.path.join("static_data", filename)
    loaded: Any = {}
    for p in (get_data_path(rel), get_resource_path(rel)):
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                break
            except Exception:
                continue
    _STATIC_JSON_CACHE[filename] = loaded
    return loaded


def _load_meta_tier_ranks(game_id: str) -> Dict[str, int]:
    """Lê ranks de tier (0 = T0, 1 = T0.5, 2 = T1...) dos relatórios raspados em disco."""
    g = (game_id or "").lower().strip()
    candidates = {
        "hsr": ["hsr/meta_e_tierlists_atual.md", "hsr/meta_endgame_hsr.md"],
        "zzz": ["zzz/meta_endgame_zzz.md"],
        "genshin": ["genshin/meta_endgame_genshin.md"],
    }.get(g, [])

    ranks: Dict[str, int] = {}
    for rel in candidates:
        path = None
        for cand_p in (get_data_path(rel), get_resource_path(rel)):
            if os.path.exists(cand_p):
                path = cand_p
                break
        if not path:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError:
            continue

        tier_rank = 5
        genshin_tier_idx = 0
        for raw_line in lines:
            line = raw_line.strip()
            if g == "genshin" and line.startswith("### Tier"):
                tier_rank = genshin_tier_idx
                genshin_tier_idx += 1
                continue
            m_tier = re.search(r"\bT(0\.5|0|1\.5|1|2|3|4|5)\b", line)
            if line.startswith("#") and m_tier:
                tier_map = {"0": 0, "0.5": 1, "1": 2, "1.5": 3, "2": 4, "3": 5, "4": 6, "5": 7}
                tier_rank = tier_map.get(m_tier.group(1), 5)
                continue
            if line.startswith("- ") and "(" in line:
                name_part = line[2:].split("(", 1)[0].strip()
                nk = _norm_str(name_part)
                if nk:
                    ranks[nk] = min(ranks.get(nk, 99), tier_rank)
            elif g == "genshin" and line.startswith("**Personagens:**"):
                raw_chars = line.split(":**", 1)[-1]
                for tok in raw_chars.split(","):
                    cleaned = re.sub(r"^[Cc]\d+\s*", "", tok.strip())
                    cleaned = re.sub(r"(expert|comfort|flexible|partner|high app|driver|reaction|NEW|CC).*$", "", cleaned, flags=re.I).strip()
                    nk = _norm_str(cleaned)
                    if nk:
                        ranks[nk] = min(ranks.get(nk, 99), tier_rank)
        if ranks:
            break
    return ranks


def _load_dynamic_archetype_catalog(game_id: str) -> Dict[str, List[str]]:
    """
    Constrói grupos de arquétipos dinamicamente a partir de static_data/
    ({game}_manifest.json, character_benchmarks.json, team_archetypes.json e meta_*.md),
    sem listas hardcoded de personagens.
    """
    g = (game_id or "").lower().strip()
    manifest = _load_static_json(f"{g}_manifest.json")
    manifest_chars = manifest.get("characters") if isinstance(manifest, dict) else {}
    if not isinstance(manifest_chars, dict):
        manifest_chars = {}

    benchmarks_all = _load_static_json("character_benchmarks.json")
    bm_game = benchmarks_all.get(g) if isinstance(benchmarks_all, dict) else {}
    if not isinstance(bm_game, dict):
        bm_game = {}
    bm_norm: Dict[str, Dict[str, str]] = {_norm_str(k): v for k, v in bm_game.items() if isinstance(v, dict)}

    teams_all = _load_static_json("team_archetypes.json")
    teams_game = teams_all.get(g) if isinstance(teams_all, dict) else []
    if not isinstance(teams_game, list):
        teams_game = []

    tier_ranks = _load_meta_tier_ranks(g)

    # Indexa papéis provenientes de team_archetypes.json
    team_roles: Dict[str, List[str]] = {}
    team_names_display: Dict[str, str] = {}
    team_member_order: Dict[str, int] = {}
    order_seq = 0
    for team in teams_game:
        if not isinstance(team, dict):
            continue
        team_title = str(team.get("team_name") or "").lower()
        for mem in team.get("members") or []:
            if not isinstance(mem, dict):
                continue
            m_name = str(mem.get("name") or "").strip()
            m_role = str(mem.get("role") or "").lower()
            nk = _norm_str(m_name)
            if not nk:
                continue
            team_roles.setdefault(nk, []).append(f"{m_role} {team_title}")
            team_names_display.setdefault(nk, m_name)
            if nk not in team_member_order:
                team_member_order[nk] = order_seq
                order_seq += 1

    # Consolida metadados de cada personagem conhecido em static_data/
    entries: Dict[str, Dict[str, Any]] = {}
    for slug, info in manifest_chars.items():
        if not isinstance(info, dict):
            continue
        disp_name = str(info.get("name") or slug).strip()
        nk = _norm_str(disp_name) or _norm_str(slug)
        if not nk:
            continue
        entries[nk] = {
            "name": disp_name,
            "rarity": _safe_int(info.get("rarity"), 4),
            "element": str(info.get("element") or "").lower(),
            "path": str(info.get("path") or "").lower(),
            "specialty": str(info.get("specialty") or "").lower(),
            "benchmarks": bm_norm.get(nk) or bm_norm.get(_norm_str(slug)) or {},
            "roles": " ".join(team_roles.get(nk, [])),
            "in_team": nk in team_roles,
            "tier": tier_ranks.get(nk, 99),
            "team_order": team_member_order.get(nk, 999),
        }

    # Inclui personagens presentes em benchmarks ou team_archetypes mesmo se ausentes no manifest
    for nk, bm in bm_norm.items():
        if nk not in entries:
            entries[nk] = {
                "name": team_names_display.get(nk, nk.title()),
                "rarity": 5 if nk in team_roles else 4,
                "element": "",
                "path": "",
                "specialty": "",
                "benchmarks": bm,
                "roles": " ".join(team_roles.get(nk, [])),
                "in_team": nk in team_roles,
                "tier": tier_ranks.get(nk, 99),
                "team_order": team_member_order.get(nk, 999),
            }

    def _sort_names(nk_list: List[str]) -> List[str]:
        unique = list(dict.fromkeys(nk_list))
        unique.sort(
            key=lambda k: (
                0 if entries[k]["in_team"] else 1,
                entries[k]["tier"],
                -entries[k]["rarity"],
                entries[k]["team_order"],
                entries[k]["name"],
            )
        )
        return [entries[k]["name"] for k in unique]

    def _bm_has(bm: Dict[str, str], frags: tuple[str, ...]) -> bool:
        return any(any(f in _norm_str(bk) for f in frags) for bk in bm.keys())

    def _bm_num(bm: Dict[str, str], frags: tuple[str, ...]) -> float:
        for bk, bv in bm.items():
            if any(f in _norm_str(bk) for f in frags):
                val = _safe_float(str(bv).replace(".", "").replace(",", "."), 0.0)
                if val > 0:
                    return val
        return 0.0

    groups: Dict[str, List[str]] = {}

    if g == "genshin":
        sustain_t0, sustain_all = [], []
        buffers_t0, buffers_all = [], []
        vv_shredders, offfield_hydro, main_dps = [], [], []

        for nk, e in entries.items():
            bm = e["benchmarks"]
            roles = e["roles"]
            el = e["element"]
            has_heal_bm = _bm_has(bm, ("bonusdecura", "cura", "heal"))
            has_shield_role = any(w in roles for w in ("sustent", "cura", "escud", "heal", "shield"))
            has_hp_only = _bm_has(bm, ("vida", "hp")) and not _bm_has(bm, ("taxacrit", "danocrit", "crit"))
            has_crit_bm = _bm_has(bm, ("taxacrit", "critrate")) and _bm_has(bm, ("danocrit", "critdmg"))
            em_val = _bm_num(bm, ("proficiencia", "elementalmastery", "em"))
            er_val = _bm_num(bm, ("recarga", "energyrecharge"))

            is_sustain = has_heal_bm or has_shield_role or (has_hp_only and _bm_num(bm, ("vida", "hp")) >= 35000)
            if is_sustain:
                sustain_all.append(nk)
                if e["in_team"] or e["rarity"] == 5 or e["tier"] <= 3:
                    sustain_t0.append(nk)

            is_vv = el == "anemo" and (em_val >= 600 or "buffer" in roles or "controle" in roles)
            if is_vv:
                vv_shredders.append(nk)

            is_buffer = (
                is_vv
                or any(w in roles for w in ("buffer", "suporte"))
                or (er_val >= 180 and not has_crit_bm and not is_sustain)
            )
            if is_buffer:
                buffers_all.append(nk)
                if e["in_team"] or e["rarity"] == 5 or e["tier"] <= 3 or is_vv:
                    buffers_t0.append(nk)

            is_off_hydro = el == "hydro" and (
                any(w in roles for w in ("sub-dps", "aplicacao", "aplicação", "buffer"))
                or (er_val >= 170 and has_crit_bm)
            )
            if is_off_hydro:
                offfield_hydro.append(nk)

            is_dps = ("dps principal" in roles) or (has_crit_bm and not is_sustain and not is_off_hydro and not is_vv)
            if is_dps:
                main_dps.append(nk)

        groups = {
            "sustain_t0": _sort_names(sustain_t0),
            "sustain_all": _sort_names(sustain_all),
            "buffers_t0": _sort_names(buffers_t0),
            "buffers_all": _sort_names(buffers_all),
            "vv_shredders": _sort_names(vv_shredders),
            "offfield_hydro": _sort_names(offfield_hydro),
            "main_dps": _sort_names(main_dps),
        }

    elif g == "hsr":
        harmony_t0, sustain_5star, sustain_all = [], [], []
        break_group, pf_erudition, crit_dps = [], [], []

        for nk, e in entries.items():
            bm = e["benchmarks"]
            roles = e["roles"]
            path = e["path"]

            if path == "harmony" and (e["rarity"] == 5 or e["in_team"] or e["tier"] <= 2):
                harmony_t0.append(nk)
            if path in ("preservation", "abundance"):
                sustain_all.append(nk)
                if e["rarity"] == 5:
                    sustain_5star.append(nk)
            if _bm_has(bm, ("efeitodequebra", "quebra", "break")) or "break" in roles:
                break_group.append(nk)
            if path == "erudition" or ("pure fiction" in roles):
                pf_erudition.append(nk)
            if (
                path in ("destruction", "hunt", "erudition", "nihility", "remembrance")
                and e["rarity"] == 5
                and (_bm_has(bm, ("taxacrit", "danocrit", "crit")) or "dps principal" in roles)
            ):
                crit_dps.append(nk)

        groups = {
            "harmony_t0": _sort_names(harmony_t0),
            "sustain_5star": _sort_names(sustain_5star),
            "sustain_all": _sort_names(sustain_all),
            "break": _sort_names(break_group),
            "pf_erudition": _sort_names(pf_erudition),
            "crit_dps": _sort_names(crit_dps),
        }

    elif g == "zzz":
        stunners_s, stunners_all = [], []
        supports_s, supports_all = [], []
        attack_dps, anomaly_dps = [], []

        for nk, e in entries.items():
            bm = e["benchmarks"]
            spec = e["specialty"]

            has_imp_bm = _bm_has(bm, ("impacto", "impact"))
            if spec == "stun" or (spec == "defense" and has_imp_bm):
                stunners_all.append(nk)
                if e["rarity"] == 5:
                    stunners_s.append(nk)
            if spec in ("support", "defense"):
                supports_all.append(nk)
                if e["rarity"] == 5:
                    supports_s.append(nk)
            if spec in ("attack", "rupture"):
                attack_dps.append(nk)
            if spec == "anomaly":
                anomaly_dps.append(nk)

        groups = {
            "stunners_s": _sort_names(stunners_s),
            "stunners_all": _sort_names(stunners_all),
            "supports_s": _sort_names(supports_s),
            "supports_all": _sort_names(supports_all),
            "attack_dps": _sort_names(attack_dps),
            "anomaly_dps": _sort_names(anomaly_dps),
        }

    return groups

_ELEMENT_META = {
    "genshin": [
        ("Pyro", "fa-fire", "#ef4444", {"pyro", "fogo", "fire"}),
        ("Hydro", "fa-droplet", "#0284c7", {"hydro", "agua"}),
        ("Dendro", "fa-leaf", "#10b981", {"dendro", "planta"}),
        ("Electro", "fa-bolt", "#a855f7", {"electro", "eletrico", "raio", "lightning", "electric"}),
        ("Anemo", "fa-wind", "#14b8a6", {"anemo", "vento", "wind"}),
        ("Cryo", "fa-snowflake", "#38bdf8", {"cryo", "gelo", "ice"}),
        ("Geo", "fa-mountain", "#f59e0b", {"geo", "terra"}),
    ],
    "hsr": [
        ("Físico", "fa-hand-fist", "#e2e8f0", {"physical", "fisico"}),
        ("Fogo", "fa-fire", "#ef4444", {"fire", "fogo", "pyro"}),
        ("Gelo", "fa-snowflake", "#38bdf8", {"ice", "gelo", "cryo"}),
        ("Raio", "fa-bolt", "#a855f7", {"lightning", "raio", "electro", "electric", "eletrico"}),
        ("Vento", "fa-wind", "#10b981", {"wind", "vento", "anemo"}),
        ("Quântico", "fa-atom", "#6366f1", {"quantum", "quantico"}),
        ("Imaginário", "fa-sun", "#f59e0b", {"imaginary", "imaginario"}),
    ],
    "zzz": [
        ("Físico", "fa-hand-fist", "#e2e8f0", {"physical", "fisico"}),
        ("Fogo", "fa-fire", "#ef4444", {"fire", "fogo", "pyro"}),
        ("Gelo", "fa-snowflake", "#38bdf8", {"ice", "gelo", "cryo", "frost"}),
        ("Elétrico", "fa-bolt", "#a855f7", {"electric", "eletrico", "lightning", "raio", "electro"}),
        ("Éter", "fa-circle-radiation", "#10b981", {"ether", "eter"}),
    ],
}


def _safe_int(val: Any, default: int = 0) -> int:
    """Converte um valor qualquer em int com fallback seguro."""
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        return int(val)
    m = _RE_NUM_VAL.search(str(val))
    if m:
        try:
            return int(float(m.group(0)))
        except (ValueError, TypeError):
            return default
    return default


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Converte um valor qualquer em float com fallback seguro."""
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    m = _RE_NUM_VAL.search(str(val).replace(",", "."))
    if m:
        try:
            return float(m.group(0))
        except (ValueError, TypeError):
            return default
    return default


def _norm_str(text: str) -> str:
    """Normaliza strings removendo acentos, pontuação e espaços em excesso."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("utf-8").lower()
    return _RE_NON_ALNUM.sub("", text)


def _get_static_elements_map(game_id: str) -> Dict[str, str]:
    """Carrega mapa dinâmico de elemento por personagem de static_data/ (character_elements + manifest)."""
    global _ELEMENTS_JSON_CACHE
    if _ELEMENTS_JSON_CACHE is None:
        loaded: Dict[str, Dict[str, str]] = {}
        rel = os.path.join("static_data", "character_elements.json")
        for p in (get_data_path(rel), get_resource_path(rel)):
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    break
                except Exception:
                    pass
        _ELEMENTS_JSON_CACHE = loaded

    elem_map: Dict[str, str] = {}
    for k, v in (_ELEMENTS_JSON_CACHE.get(game_id) or {}).items():
        nk = _norm_str(k)
        if nk and v:
            elem_map[nk] = str(v)

    try:
        from static_data_manager import static_data_manager

        manifest_chars = static_data_manager._cache.get(game_id, {}).get("characters", {})
        for ck, cv in manifest_chars.items():
            if isinstance(cv, dict) and cv.get("element"):
                elem_val = str(cv["element"])
                for raw_key in (ck, cv.get("name", "")):
                    nk = _norm_str(raw_key)
                    if nk and nk not in elem_map:
                        elem_map[nk] = elem_val
    except Exception:
        pass
    return elem_map


def _compute_elemental_coverage(
    game_id: str, owned_chars_map: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Calcula a cobertura elemental dinamicamente a partir do roster e dos manifestos de static_data/."""
    static_elems = _get_static_elements_map(game_id)
    meta_list = _ELEMENT_META.get(game_id, [])
    coverage: List[Dict[str, Any]] = []

    for elem_name, elem_icon, elem_color, aliases in meta_list:
        matched_names: List[str] = []
        built_count = 0
        for norm_k, info in owned_chars_map.items():
            raw_el = info.get("element") or static_elems.get(norm_k, "")
            el_clean = unicodedata.normalize("NFKD", str(raw_el)).encode("ASCII", "ignore").decode("utf-8").lower().strip()
            if el_clean in aliases or _norm_str(raw_el) in aliases:
                if info["name"] not in matched_names:
                    matched_names.append(info["name"])
                    if info["is_built"]:
                        built_count += 1
        status = "Forte" if built_count >= 2 else ("Moderado" if len(matched_names) >= 1 else "Faltando")
        coverage.append(
            {
                "element": elem_name,
                "icon": elem_icon,
                "color": elem_color,
                "count": len(matched_names),
                "built_count": built_count,
                "characters": matched_names,
                "status": status,
            }
        )
    return coverage


def analyze_account_gaps(game_id: str, roster: list, endgame_data: dict = None) -> dict:
    """
    Realiza uma auditoria estratégica profunda da conta do jogador (Genshin, HSR ou ZZZ),
    identificando carências de arquétipos (Sustentação, Buffers de Ação, DPSs, Sub-DPS),
    cobertura elemental, prontidão para os modos de Endgame e recomendações ranqueadas de gacha.
    """
    _ = endgame_data
    g = game_id.lower().strip()
    game_names = {"genshin": "Genshin Impact", "hsr": "Honkai: Star Rail", "zzz": "Zenless Zone Zero"}

    # Extrai e normaliza personagens do roster
    owned_chars_map = {}
    for item in roster or []:
        if isinstance(item, dict):
            c_name = item.get("name") or ""
            c_lvl = _safe_int(item.get("level"), 1)
            c_rarity = _safe_int(item.get("rarity"), 4)
            c_rank = _safe_int(item.get("rank") or item.get("constellation") or item.get("eidolon"), 0)
            c_elem = item.get("element") or ""
        elif isinstance(item, str):
            c_name = item
            c_lvl = 80
            c_rarity = 5
            c_rank = 0
            c_elem = ""
        else:
            continue

        norm_key = _norm_str(c_name)
        if norm_key:
            owned_chars_map[norm_key] = {
                "name": c_name,
                "level": c_lvl,
                "rarity": c_rarity,
                "rank": c_rank,
                "element": c_elem,
                "is_built": c_lvl >= (70 if g != "zzz" else 50),
            }

    def has_any(alias_list: list, min_built: bool = False) -> tuple[bool, list]:
        """Verifica se o jogador possui ao menos um personagem da lista de aliases."""
        matched = []
        for alias in alias_list:
            norm_a = _norm_str(alias)
            for k, info in owned_chars_map.items():
                if norm_a in k or k in norm_a:
                    if not min_built or info["is_built"]:
                        if info["name"] not in matched:
                            matched.append(info["name"])
        return (len(matched) > 0, matched)

    def count_in_group(alias_groups: list, min_built: bool = False) -> list:
        """Retorna lista de nomes únicos encontrados a partir de uma lista de aliases."""
        found = set()
        for alias in alias_groups:
            _, matches = has_any([alias], min_built)
            for m in matches:
                found.add(m)
        return list(found)

    # Definição das matrizes por jogo
    overall_score = 100
    critical_gaps = []
    pull_recommendations = []
    archetypes_summary = []
    elemental_coverage = []
    endgame_readiness = {}

    total_chars = len(owned_chars_map)
    built_chars = sum(1 for c in owned_chars_map.values() if c["is_built"])
    dyn_groups = _load_dynamic_archetype_catalog(g)

    def _top_unowned(group_key: str, limit: int = 4) -> List[str]:
        candidates = dyn_groups.get(group_key) or []
        unowned = [c for c in candidates if not has_any([c])[0]]
        picked = unowned[:limit] if unowned else candidates[:limit]
        return picked

    # ==========================================
    # 1. GENSHIN IMPACT
    # ==========================================
    if g == "genshin":
        sustain_t0 = dyn_groups.get("sustain_t0") or []
        sustain_all = dyn_groups.get("sustain_all") or []
        owned_sustain_t0 = count_in_group(sustain_t0)
        owned_sustain_all = count_in_group(sustain_all)

        buffers_t0 = dyn_groups.get("buffers_t0") or []
        buffers_all = dyn_groups.get("buffers_all") or []
        owned_buffers_t0 = count_in_group(buffers_t0)
        owned_buffers_all = count_in_group(buffers_all)

        offfield_hydro = dyn_groups.get("offfield_hydro") or []
        owned_offfield_hydro = count_in_group(offfield_hydro)

        main_dps_list = dyn_groups.get("main_dps") or []
        owned_main_dps = count_in_group(main_dps_list)

        vv_shredders = dyn_groups.get("vv_shredders") or []

        # Status dos Arquétipos
        def get_status_data(count, t0_count, ideal_min=2):
            if t0_count >= ideal_min or count >= ideal_min + 2:
                return "Excelente", "#10b981"
            elif count >= ideal_min:
                return "Suficiente", "#3b82f6"
            elif count == 1:
                return "Atenção", "#f59e0b"
            else:
                return "Crítico", "#ef4444"

        st_sust, col_sust = get_status_data(len(owned_sustain_all), len(owned_sustain_t0), 2)
        archetypes_summary.append(
            {
                "key": "sustain",
                "title": "Sustentação (Shield / Healer)",
                "icon": "fa-shield-halved",
                "status": st_sust,
                "status_color": col_sust,
                "owned_count": len(owned_sustain_all),
                "target_count": 2,
                "owned_characters": owned_sustain_all,
                "description": "Sustain pros 2 lados do Abismo 12.",
            }
        )

        st_buff, col_buff = get_status_data(len(owned_buffers_all), len(owned_buffers_t0), 2)
        archetypes_summary.append(
            {
                "key": "buffers",
                "title": "Buffers & RES Shred (VV / Suportes)",
                "icon": "fa-wand-magic-sparkles",
                "status": st_buff,
                "status_color": col_buff,
                "owned_count": len(owned_buffers_all),
                "target_count": 2,
                "owned_characters": owned_buffers_all,
                "description": "Buffs globais, 4p VV e amplificação de reação.",
            }
        )

        st_hydro, col_hydro = get_status_data(len(owned_offfield_hydro), len(owned_offfield_hydro), 2)
        archetypes_summary.append(
            {
                "key": "offfield_hydro",
                "title": "Aplicadores Hydro Off-Field",
                "icon": "fa-droplet",
                "status": st_hydro,
                "status_color": col_hydro,
                "owned_count": len(owned_offfield_hydro),
                "target_count": 2,
                "owned_characters": owned_offfield_hydro,
                "description": "Base para Vaporize, Hyperbloom, Taser e Freeze.",
            }
        )

        st_dps, col_dps = get_status_data(len(owned_main_dps), len(owned_main_dps), 2)
        archetypes_summary.append(
            {
                "key": "main_dps",
                "title": "DPS Principal (Hypercarry / Driver)",
                "icon": "fa-khanda",
                "status": st_dps,
                "status_color": col_dps,
                "owned_count": len(owned_main_dps),
                "target_count": 2,
                "owned_characters": owned_main_dps,
                "description": "Carries para fechar os dois lados do Abismo.",
            }
        )

        # Cobertura Elemental (dinâmica via roster + static_data/)
        elemental_coverage.extend(_compute_elemental_coverage("genshin", owned_chars_map))

        # Lacunas Críticas
        if len(owned_sustain_t0) == 0:
            rec_sust = _top_unowned("sustain_t0", 4)
            overall_score -= 22
            critical_gaps.append(
                {
                    "id": "genshin_no_t0_sustain",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "Sustain em Falta",
                    "title": "Sem Sustain T0",
                    "description": f"Nenhum healer/shielder T0 no roster ({', '.join(rec_sust[:4])}).",
                    "endgame_impact": "Interrupções e perda de rotação no Abismo 12.",
                    "suggested_archetype": "Shielder ou Healer com buff",
                    "recommended_characters": rec_sust,
                }
            )

        if len(owned_offfield_hydro) < 2:
            rec_hydro = _top_unowned("offfield_hydro", 3)
            overall_score -= 18
            critical_gaps.append(
                {
                    "id": "genshin_lack_hydro",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "Falta Hydro Off-Field",
                    "title": "Menos de 2 Aplicadores Hydro Off-Field",
                    "description": f"Menos de 2 aplicadores Hydro off-field ({', '.join(rec_hydro[:3])}).",
                    "endgame_impact": "Trava times simultâneos de Vaporize, Hyperbloom ou Freeze.",
                    "suggested_archetype": "Sub-DPS / Buffer Hydro Off-Field",
                    "recommended_characters": rec_hydro,
                }
            )

        has_vv, _ = has_any(vv_shredders)
        if not has_vv:
            rec_vv = _top_unowned("vv_shredders", 3)
            overall_score -= 15
            critical_gaps.append(
                {
                    "id": "genshin_no_vv_shred",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "Sem 4p VV",
                    "title": "Sem Anemo de Sombra Verde (VV)",
                    "description": "Sem buffer Anemo para aplicar 40% RES shred de 4p VV.",
                    "endgame_impact": "Perda de ~25–30% de DPS em times de reação.",
                    "suggested_archetype": "Buffer / Agrupador Anemo",
                    "recommended_characters": rec_vv,
                }
            )

        if len(owned_main_dps) < 2:
            rec_dps = _top_unowned("main_dps", 4)
            overall_score -= 20
            critical_gaps.append(
                {
                    "id": "genshin_lack_main_dps",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "Falta Carry",
                    "title": "Menos de 2 Hypercarries/Drivers",
                    "description": "Falta DPS principal buildado pros dois lados do Abismo 12.",
                    "endgame_impact": "Falta teto de DPS para fechar 36★.",
                    "suggested_archetype": "Main DPS T0",
                    "recommended_characters": rec_dps,
                }
            )

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_sustain_t0) == 0:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Sustentador / Shielder T0",
                    "badge": "Prioridade Máxima",
                    "tag": "Sustain",
                    "characters": _top_unowned("sustain_t0", 3),
                    "reason": "Fecha sobrevivência e resistência a interrupção no Abismo 12.",
                    "impact_score": "Estabiliza os 2 lados do Abismo",
                }
            )
            rank_idx += 1

        if len(owned_buffers_t0) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Buffer Universal (DMG% / RES Shred)",
                    "badge": "Alta Prioridade",
                    "tag": "Buff Global",
                    "characters": _top_unowned("buffers_t0", 3),
                    "reason": "Entra em quase todo time com DMG% alto e 40% RES shred.",
                    "impact_score": "+30–40% DPS no time",
                }
            )
            rank_idx += 1

        if len(owned_main_dps) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Hypercarry On-Field",
                    "badge": "Alta Prioridade",
                    "tag": "Main DPS",
                    "characters": _top_unowned("main_dps", 3),
                    "reason": "Carries flexíveis com scaling alto que fecham um lado sem depender de suportes travados.",
                    "impact_score": "Fecha 1 lado do Abismo 12",
                }
            )
            rank_idx += 1

    # ==========================================
    # 2. HONKAI: STAR RAIL
    # ==========================================
    elif g == "hsr":
        harmony_t0 = dyn_groups.get("harmony_t0") or []
        owned_harmony_t0 = count_in_group(harmony_t0)

        sustain_5star = dyn_groups.get("sustain_5star") or []
        sustain_all = dyn_groups.get("sustain_all") or []
        owned_sustain_5star = count_in_group(sustain_5star)
        owned_sustain_all = count_in_group(sustain_all)

        break_archetype = dyn_groups.get("break") or []
        owned_break = count_in_group(break_archetype)

        pf_erudition = dyn_groups.get("pf_erudition") or []
        owned_pf = count_in_group(pf_erudition)

        crit_hypercarries = dyn_groups.get("crit_dps") or []
        owned_crit_dps = count_in_group(crit_hypercarries)

        # Status dos Arquétipos
        def get_hsr_status(count, t0_count, ideal_min=2):
            if t0_count >= ideal_min:
                return "Excelente", "#10b981"
            elif count >= ideal_min:
                return "Suficiente", "#3b82f6"
            elif count == 1:
                return "Atenção", "#f59e0b"
            else:
                return "Crítico", "#ef4444"

        st_harm, col_harm = get_hsr_status(len(owned_harmony_t0), len(owned_harmony_t0), 2)
        archetypes_summary.append(
            {
                "key": "harmony",
                "title": "Harmonia & Manipulação de Ação (Tier 0)",
                "icon": "fa-music",
                "status": st_harm,
                "status_color": col_harm,
                "owned_count": len(owned_harmony_t0),
                "target_count": 2,
                "owned_characters": owned_harmony_t0,
                "description": "Avanço de ação, RES PEN e buffs de CRIT.",
            }
        )

        st_sust, col_sust = get_hsr_status(len(owned_sustain_all), len(owned_sustain_5star), 2)
        archetypes_summary.append(
            {
                "key": "sustain",
                "title": "Sustain Limitado (Preservação / Abundância)",
                "icon": "fa-shield-halved",
                "status": st_sust,
                "status_color": col_sust,
                "owned_count": len(owned_sustain_all),
                "target_count": 2,
                "owned_characters": owned_sustain_5star if owned_sustain_5star else owned_sustain_all,
                "description": "Cleanse/RES a CC, escudos e cura reativa para MoC 12 e AS 4.",
            }
        )

        st_break, col_break = (
            ("Excelente", "#10b981")
            if len(owned_break) >= 3
            else (("Suficiente", "#3b82f6") if len(owned_break) >= 2 else ("Atenção", "#f59e0b"))
        )
        archetypes_summary.append(
            {
                "key": "break",
                "title": "Núcleo de Quebra / Super Break",
                "icon": "fa-burst",
                "status": st_break,
                "status_color": col_break,
                "owned_count": len(owned_break),
                "target_count": 3,
                "owned_characters": owned_break,
                "description": "Quebra de tenacidade rápida para Sombra Apocalíptica e MoC.",
            }
        )

        st_pf, col_pf = (
            ("Excelente", "#10b981")
            if len(owned_pf) >= 2
            else (("Suficiente", "#3b82f6") if len(owned_pf) >= 1 else ("Crítico", "#ef4444"))
        )
        archetypes_summary.append(
            {
                "key": "pure_fiction",
                "title": "AoE / Pura Ficção",
                "icon": "fa-meteor",
                "status": st_pf,
                "status_color": col_pf,
                "owned_count": len(owned_pf),
                "target_count": 2,
                "owned_characters": owned_pf,
                "description": "Erudição e AoE contínuo para bater 60.000+ pts na Pura Ficção.",
            }
        )

        # Cobertura Elemental (dinâmica via roster + static_data/)
        elemental_coverage.extend(_compute_elemental_coverage("hsr", owned_chars_map))

        # Lacunas Críticas
        if len(owned_harmony_t0) < 2:
            rec_harm = _top_unowned("harmony_t0", 4)
            overall_score -= 22
            critical_gaps.append(
                {
                    "id": "hsr_lack_tier0_harmony",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "Déficit de Harmonia T0",
                    "title": "Menos de 2 Suportes Harmonia T0",
                    "description": f"Menos de 2 buffers Harmonia T0 no roster ({', '.join(rec_harm[:4])}).",
                    "endgame_impact": "Mais ciclos gastos no MoC e teto baixo na Pura Ficção.",
                    "suggested_archetype": "Harmonia Limitada (Action Advance / RES PEN / DMG%)",
                    "recommended_characters": rec_harm,
                }
            )

        if len(owned_sustain_5star) < 2:
            rec_sust = _top_unowned("sustain_5star", 4)
            overall_score -= 20
            critical_gaps.append(
                {
                    "id": "hsr_lack_5star_sustain",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "Falta Sustain 5★",
                    "title": "Menos de 2 Sustains Limitados 5★",
                    "description": f"Faltam 2 sustains 5★ ({', '.join(rec_sust[:4])}).",
                    "endgame_impact": "Risco de CC e one-shot nos andares 11 e 12.",
                    "suggested_archetype": "Preservação / Abundância 5★",
                    "recommended_characters": rec_sust,
                }
            )

        if len(owned_pf) == 0:
            rec_pf = _top_unowned("pf_erudition", 3)
            overall_score -= 15
            critical_gaps.append(
                {
                    "id": "hsr_no_pure_fiction_core",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "Falta Núcleo de PF",
                    "title": "Sem Especialista em AoE para PF",
                    "description": "Nenhum personagem de Erudição / AoE buildado.",
                    "endgame_impact": "Dificuldade para bater 60.000 pts na Pura Ficção.",
                    "suggested_archetype": "Erudição / FuA em AoE",
                    "recommended_characters": rec_pf,
                }
            )

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_harmony_t0) < 2:
            rec_harm_pull = _top_unowned("harmony_t0", 4)
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Harmonia Universal (Action Advance / RES PEN)",
                    "badge": "Prioridade Máxima",
                    "tag": "Buffer de Conta",
                    "characters": rec_harm_pull,
                    "reason": "Maior ganho de dano por pull no HSR — corta ciclos em praticamente qualquer time.",
                    "impact_score": "-2 a 4 ciclos no MoC",
                }
            )
            rank_idx += 1

        if len(owned_sustain_5star) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Sustain 5★ (Preservação / Abundância)",
                    "badge": "Alta Prioridade",
                    "tag": "Sustain & Utilidade",
                    "characters": _top_unowned("sustain_5star", 3),
                    "reason": "Fecha sobrevivência, cleanse e utilidade ofensiva para o MoC 12.",
                    "impact_score": "Sustain seguro no MoC 12",
                }
            )
            rank_idx += 1

        if len(owned_crit_dps) == 0 and len(owned_break) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Main DPS T0 (Endgame Carry)",
                    "badge": "Alta Prioridade",
                    "tag": "Carry de Endgame",
                    "characters": _top_unowned("crit_dps", 3),
                    "reason": "Carries de alto teto com ignore de fraqueza ou burst consistente.",
                    "impact_score": "Fecha 36★ MoC / 12★ AS",
                }
            )
            rank_idx += 1

    # ==========================================
    # 3. ZENLESS ZONE ZERO
    # ==========================================
    elif g == "zzz":
        stunners_s = dyn_groups.get("stunners_s") or []
        stunners_all = dyn_groups.get("stunners_all") or []
        owned_stunners_s = count_in_group(stunners_s)
        owned_stunners_all = count_in_group(stunners_all)

        supports_all = dyn_groups.get("supports_all") or []
        owned_supports_all = count_in_group(supports_all)

        attack_dps = dyn_groups.get("attack_dps") or []
        owned_attack_dps = count_in_group(attack_dps)

        anomaly_dps = dyn_groups.get("anomaly_dps") or []
        owned_anomaly_dps = count_in_group(anomaly_dps)

        # Status
        st_stun = (
            "Excelente" if len(owned_stunners_s) >= 2 else ("Suficiente" if len(owned_stunners_all) >= 2 else "Atenção")
        )
        col_stun = "#10b981" if st_stun == "Excelente" else ("#3b82f6" if st_stun == "Suficiente" else "#f59e0b")
        archetypes_summary.append(
            {
                "key": "stunners",
                "title": "Atordoadores (Stun / Daze)",
                "icon": "fa-bolt",
                "status": st_stun,
                "status_color": col_stun,
                "owned_count": len(owned_stunners_all),
                "target_count": 2,
                "owned_characters": owned_stunners_all,
                "description": "Multiplicador de 150%+ na janela de Stun.",
            }
        )

        st_supp = (
            "Excelente"
            if len(owned_supports_all) >= 3
            else ("Suficiente" if len(owned_supports_all) >= 2 else "Atenção")
        )
        col_supp = "#10b981" if st_supp == "Excelente" else ("#3b82f6" if st_supp == "Suficiente" else "#f59e0b")
        archetypes_summary.append(
            {
                "key": "supports",
                "title": "Suporte & Defesa (ATK / DEF Shred)",
                "icon": "fa-shield-halved",
                "status": st_supp,
                "status_color": col_supp,
                "owned_count": len(owned_supports_all),
                "target_count": 2,
                "owned_characters": owned_supports_all,
                "description": "Quick Assist, buff de ATK flat e DEF shred.",
            }
        )

        st_atk = (
            "Excelente" if len(owned_attack_dps) >= 2 else ("Suficiente" if len(owned_attack_dps) >= 1 else "Atenção")
        )
        col_atk = "#10b981" if st_atk == "Excelente" else ("#3b82f6" if st_atk == "Suficiente" else "#f59e0b")
        archetypes_summary.append(
            {
                "key": "attack_dps",
                "title": "Ataque (Burst / Dano Direto)",
                "icon": "fa-crosshairs",
                "status": st_atk,
                "status_color": col_atk,
                "owned_count": len(owned_attack_dps),
                "target_count": 2,
                "owned_characters": owned_attack_dps,
                "description": "Burst concentrado em janela de Stun e Chain Attack.",
            }
        )

        st_anom = (
            "Excelente" if len(owned_anomaly_dps) >= 2 else ("Suficiente" if len(owned_anomaly_dps) >= 1 else "Atenção")
        )
        col_anom = "#10b981" if st_anom == "Excelente" else ("#3b82f6" if st_anom == "Suficiente" else "#f59e0b")
        archetypes_summary.append(
            {
                "key": "anomaly_dps",
                "title": "Anomalia (DoT / Desordem)",
                "icon": "fa-flask-vial",
                "status": st_anom,
                "status_color": col_anom,
                "owned_count": len(owned_anomaly_dps),
                "target_count": 2,
                "owned_characters": owned_anomaly_dps,
                "description": "Procs de Anomalia e Desordem sem depender de janela de Stun.",
            }
        )

        # Cobertura de Atributos ZZZ (dinâmica via roster + static_data/)
        elemental_coverage.extend(_compute_elemental_coverage("zzz", owned_chars_map))

        # Lacunas Críticas
        if len(owned_stunners_s) == 0:
            rec_stun = _top_unowned("stunners_s", 4)
            overall_score -= 22
            critical_gaps.append(
                {
                    "id": "zzz_no_s_stunner",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "Stun Lento",
                    "title": "Sem Stunner Rank S",
                    "description": "Sem atordoador Rank S para os dois lados da Shiyu.",
                    "endgame_impact": "Barra de Daze lenta nos chefes da Shiyu Crítica 5–7.",
                    "suggested_archetype": "Stunner Rank S de alto Impacto",
                    "recommended_characters": rec_stun,
                }
            )

        if len(owned_attack_dps) + len(owned_anomaly_dps) < 2:
            rec_dps_z = (_top_unowned("attack_dps", 2) + _top_unowned("anomaly_dps", 2))[:4]
            overall_score -= 25
            critical_gaps.append(
                {
                    "id": "zzz_lack_dps",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "Falta DPS",
                    "title": "Menos de 2 Main DPS",
                    "description": "Menos de 2 agentes de Ataque ou Anomalia buildados.",
                    "endgame_impact": "Falta DPS para Rank S nos dois lados da Shiyu.",
                    "suggested_archetype": "DPS Rank S (Ataque ou Anomalia)",
                    "recommended_characters": rec_dps_z,
                }
            )

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_stunners_s) == 0:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Stunner Rank S",
                    "badge": "Prioridade Máxima",
                    "tag": "Stun",
                    "characters": _top_unowned("stunners_s", 4),
                    "reason": "Acelera a barra de Daze e sobe o multiplicador de Stun nos chefes da Shiyu 7.",
                    "impact_score": "-40s no clear da Shiyu 7",
                }
            )
            rank_idx += 1

        if len(owned_anomaly_dps) == 0:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Anomalia / Desordem",
                    "badge": "Alta Prioridade",
                    "tag": "Anomalia",
                    "characters": _top_unowned("anomaly_dps", 3),
                    "reason": "Ignora janela de Stun e fecha DPS alto via Desordem em chefes de Daze resistente.",
                    "impact_score": "Alternativa contra chefes anti-Stun",
                }
            )
            rank_idx += 1

    # Normalização final da pontuação
    overall_score = max(20, min(100, overall_score))
    if overall_score >= 85:
        score_grade = "S"
        score_label = "Cobertura fechada para endgame"
        score_color = "#10b981"
    elif overall_score >= 70:
        score_grade = "A"
        score_label = "Conta equilibrada, poucos ajustes"
        score_color = "#3b82f6"
    elif overall_score >= 50:
        score_grade = "B"
        score_label = "Faltam peças em arquétipos-base"
        score_color = "#f59e0b"
    else:
        score_grade = "C"
        score_label = "Faltam suportes e sustain de base"
        score_color = "#ef4444"

    # Avaliação de Prontidão de Endgame
    endgame_teams_ready = 2 if len(critical_gaps) <= 1 and built_chars >= 6 else (1 if built_chars >= 3 else 0)
    endgame_readiness = {
        "status": f"{endgame_teams_ready}/2 Times Prontos",
        "teams_ready": endgame_teams_ready,
        "summary": (
            "Os 2 times fecham endgame com folga."
            if endgame_teams_ready == 2
            else "1 time fechado; falta reforçar o segundo nos arquétipos abaixo."
            if endgame_teams_ready == 1
            else "Foque resina em fechar o primeiro time completo antes de abrir novos bonecos."
        ),
        "details": [gap["title"] for gap in critical_gaps],
    }

    # Resumo formatado em Markdown consolidado
    rag_lines = [
        f"### DIAGNÓSTICO DA CONTA ({game_names.get(g, g.upper())}):",
        f"- **Nota da Conta:** {overall_score}/100 ({score_grade} — {score_label})",
        f"- **Buildados:** {built_chars} de {total_chars}",
        f"- **Endgame:** {endgame_teams_ready}/2 times",
    ]
    if critical_gaps:
        rag_lines.append("- **Gargalos:**")
        for cg in critical_gaps:
            rag_lines.append(
                f"  * [{cg['severity']}] {cg['title']}: {cg['description']} -> *Alvos:* {', '.join(cg['recommended_characters'])}"
            )
    else:
        rag_lines.append("- **Gargalos:** Nenhum gargalo crítico.")

    if pull_recommendations:
        rag_lines.append("- **Prioridade de Pulls:**")
        for pr in pull_recommendations:
            rag_lines.append(
                f"  {pr['priority_rank']}. **{pr['archetype']}** ({', '.join(pr['characters'])}): {pr['reason']}"
            )

    rag_summary_markdown = "\n".join(rag_lines)

    return {
        "game_id": g,
        "game_name": game_names.get(g, g.upper()),
        "overall_score": overall_score,
        "score_grade": score_grade,
        "score_label": score_label,
        "score_color": score_color,
        "total_characters": total_chars,
        "built_characters": built_chars,
        "archetypes_summary": archetypes_summary,
        "elemental_coverage": elemental_coverage,
        "critical_gaps": critical_gaps,
        "pull_recommendations": pull_recommendations,
        "endgame_readiness": endgame_readiness,
        "rag_summary_markdown": rag_summary_markdown,
    }


def recommend_relic_crafting(game_id: str, roster: list) -> dict:
    """
    Analisa os personagens de maior prioridade do Roster e identifica as piores peças equipadas
    (ou peças com atributos principais incorretos), recomendando os melhores alvos para uso
    de Resina Automodeladora (HSR), Elixir Santificador (Genshin) ou Calibrador de Discos (ZZZ).
    """
    g = game_id.lower().strip()
    game_names = {"genshin": "Genshin Impact", "hsr": "Honkai: Star Rail", "zzz": "Zenless Zone Zero"}

    item_names = {
        "genshin": "Elixir Santificador & Relic Strongbox",
        "hsr": "Resina Automodeladora & Síntese Omnipotente",
        "zzz": "Sintetizador de Discos & Calibrador Hi-Fi",
    }

    item_icons = {"genshin": "fa-flask-round-potion", "hsr": "fa-cube", "zzz": "fa-compact-disc"}

    # Ordena personagens por nível / raridade / prioridade de investimento
    top_candidates = []
    for item in roster or []:
        if isinstance(item, dict):
            c_name = item.get("name") or ""
            c_lvl = _safe_int(item.get("level"), 1)
            c_rarity = _safe_int(item.get("rarity"), 4)
            c_score = _safe_float(item.get("overall_score") or item.get("score"), 0.0)
            c_grade = str(item.get("overall_grade") or item.get("grade") or "B")
            c_icon = item.get("icon")
            relics = item.get("relics") or []
            if c_lvl >= 50 or c_rarity == 5:
                top_candidates.append(
                    {
                        "name": c_name,
                        "level": c_lvl,
                        "rarity": c_rarity,
                        "score": c_score,
                        "grade": c_grade,
                        "icon": c_icon,
                        "relics": relics,
                    }
                )

    # Prioriza quem tem score baixo ou nota B/C/D mas é personagem forte
    top_candidates.sort(key=lambda x: (x["rarity"], -x["score"]), reverse=True)

    def _derive_dynamic_craft_cfg(cand_name: str, game_key: str) -> dict:
        """Deriva alvo de síntese dinamicamente via guia consolidado e static_data/ (sem tabelas hardcoded)."""
        default_by_game = {
            "genshin": {
                "set": "Set BiS do Guia",
                "slot": "Cálice Elemental (Slot 4) ou Tiara Crítica (Slot 5)",
                "main": "Bônus Elemental ou Taxa/Dano Crítico",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%/HP%", "Recarga"],
                "gain": "Fecha main stat raro do set BiS",
                "icon": "fa-wand-magic-sparkles",
            },
            "hsr": {
                "set": "Ornamento Planar / Relíquia BiS",
                "slot": "Corda de Ligação (Slot 6) ou Pés de VEL (Slot 4)",
                "main": "Taxa de Regeneração de Energia (ERR) ou Velocidade (SPD)",
                "substats": ["Velocidade", "Taxa Crítica", "Dano Crítico", "ATK%/HP%"],
                "gain": "Fecha main stat raro de ERR/VEL ou CRIT",
                "icon": "fa-cube",
            },
            "zzz": {
                "set": "Disco de Drive BiS",
                "slot": "Disco 6 (Impacto / ERR) ou Disco 5 (Elemental)",
                "main": "Impacto% / Regeneração de Energia / Dano Elemental",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "PEN"],
                "gain": "Fecha main stat raro no Disco 5/6",
                "icon": "fa-compact-disc",
            },
        }
        cfg = dict(default_by_game.get(game_key, default_by_game["hsr"]))

        try:
            from meta_comparator import find_best_guide_file, parse_meta_target

            if find_best_guide_file(game_key, cand_name):
                parsed = parse_meta_target(game_key, cand_name) or {}
            else:
                parsed = {}
        except Exception:
            parsed = {}

        sets_list = [s for s in (parsed.get("sets") or []) if s and "não informado" not in str(s).lower()]
        if sets_list:
            cfg["set"] = str(sets_list[0])

        stats_map = parsed.get("stats") or {}
        if isinstance(stats_map, dict) and stats_map:
            # Escolhe o slot de menor taxa natural de drop (Corda ERR > Cálice/Esfera/Disco 5 Elemental > Disco 6 > Corpo/Tiara CRIT > Pés/Areia)
            slot_items = [(str(k), str(v)) for k, v in stats_map.items() if v and "qualquer" not in str(v).lower()]

            def _slot_craft_priority(item_pair: tuple[str, str]) -> int:
                sk, sv = _norm_str(item_pair[0]), _norm_str(item_pair[1])
                if ("corda" in sk or "rope" in sk) and any(t in sv for t in ("energia", "err", "recarga", "energy")):
                    return 0
                if any(s in sk for s in ("calice", "copo", "goblet", "esfera", "sphere", "disco5", "slot5")):
                    return 1
                if any(s in sk for s in ("disco6", "slot6")) and any(t in sv for t in ("impact", "energia", "err", "mastery", "anomalia")):
                    return 2
                if any(s in sk for s in ("corpo", "body", "tiara", "circlet", "disco4", "slot4")):
                    return 3
                if any(s in sk for s in ("areia", "sands", "bota", "pes", "feet")) and any(t in sv for t in ("vel", "spd", "recarga", "energia", "em", "proficiencia")):
                    return 4
                return 5

            if slot_items:
                slot_items.sort(key=_slot_craft_priority)
                best_slot, best_main = slot_items[0]
                cfg["slot"] = best_slot
                cfg["main"] = best_main
                cfg["gain"] = f"Fecha {best_main} no slot {best_slot}"

        subs_raw = parsed.get("substats") or []
        if isinstance(subs_raw, str):
            subs_list = [x.strip() for x in re.split(r"[>/=,]", subs_raw) if x.strip()]
        elif isinstance(subs_raw, list):
            subs_list = [str(x).strip() for x in subs_raw if str(x).strip()]
        else:
            subs_list = []
        if subs_list:
            cfg["substats"] = subs_list[:4]

        return cfg

    recommendations = []
    rank_counter = 1

    for cand in top_candidates:
        cfg = _derive_dynamic_craft_cfg(cand["name"], g)

        if cand["relics"]:
            lowest_piece = f"Build Atual: Nota {cand['grade']} ({cand['score']}%)" if g == "hsr" else f"Build Atual: Nota {cand['grade']}"
        else:
            lowest_piece = "Sem peças equipadas"

        recommendations.append(
            {
                "priority_rank": rank_counter,
                "character_name": cand["name"],
                "character_icon": cand["icon"],
                "target_set_name": cfg["set"],
                "slot_name": cfg["slot"],
                "slot_icon": cfg["icon"],
                "recommended_main_stat": cfg["main"],
                "recommended_substats": cfg["substats"],
                "current_piece_status": lowest_piece,
                "expected_gain": cfg["gain"],
                "urgency": "MÁXIMA" if rank_counter <= 2 else "ALTA",
            }
        )
        rank_counter += 1
        if rank_counter > 5:
            break

    # Fallback se roster estiver vazio
    if not recommendations:
        recommendations.append(
            {
                "priority_rank": 1,
                "character_name": "Suporte / Buffer Principal",
                "character_icon": None,
                "target_set_name": "Set de Energia ou Velocidade",
                "slot_name": "Corda de ERR / Cálice Elemental / Disco 6",
                "slot_icon": item_icons.get(g, "fa-gem"),
                "recommended_main_stat": "Recuperação de Energia / Dano Elemental / Impacto",
                "recommended_substats": ["Velocidade", "Taxa Crítica", "Dano Crítico"],
                "current_piece_status": "Nenhum personagem de alto nível sincronizado",
                "expected_gain": "Otimização de Rotação Global",
                "urgency": "ALTA",
            }
        )

    summary_tip = (
        f"Guarde {item_names.get(g, 'Resina')} para **Corda ERR**, **Cálice Elemental** ou **Disco 6 de Impacto** "
        "(drop natural de ~3–5%)."
    )

    return {
        "game_id": g,
        "game_name": game_names.get(g, g.upper()),
        "crafting_item_name": item_names.get(g, "Item de Síntese"),
        "crafting_item_icon": item_icons.get(g, "fa-wand-magic-sparkles"),
        "recommendations": recommendations,
        "summary_tip": summary_tip,
    }

