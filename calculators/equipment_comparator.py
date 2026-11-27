"""
Motor canônico de resolução multilíngue e comparação de equipamentos (Armas, Conjuntos,
Ornamentos Planares e Atributos Principais por Slot) para Genshin Impact, HSR e ZZZ.

Zero Hardcoding: consome dinamicamente os catálogos oficiais em
`static_data/{game_id}_equipment_effects.json` (gerados por `scrapers/equipment_effects_scraper.py`),
garantindo pareamento exato PT-BR <-> EN-US por ID oficial para personagens atuais e futuros.
"""

import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from core.paths import get_data_path, get_resource_path

# Cache em memória invalidado automaticamente por mtime do arquivo JSON
_CATALOG_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

_RE_PARENS_TAIL = re.compile(r"\s*\([^)]*\)\s*$")
_RE_BRACKET_TAG = re.compile(r"\s*\[[^\]]*\]\s*")
_RE_PIECE_PREFIX = re.compile(r"^(\d+)\s*(?:p|pc|pe[çc]as?)\s+", re.IGNORECASE)
_RE_PIECE_SUFFIX = re.compile(r"\s*\(\s*(\d+)\s*(?:p|-?pc|pe[çc]as?)\s*\)\s*$", re.IGNORECASE)
_RE_NON_ALNUM = re.compile(r"[^a-z0-9]")
_RE_SPLIT_OPTIONS = re.compile(r"[=/>|]|\bou\b|\bor\b", re.IGNORECASE)
_RE_NUMBERS_UNITS = re.compile(r"[0-9.,%+]+")

_ELEMENT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "physical": ("fisico", "physical"),
    "fire": ("fogo", "fire", "pyro"),
    "ice": ("gelo", "ice", "cryo"),
    "lightning": ("raio", "lightning", "eletrico", "electric", "electro"),
    "wind": ("vento", "wind", "anemo"),
    "quantum": ("quantico", "quantum"),
    "imaginary": ("imaginario", "imaginary"),
    "hydro": ("hydro",),
    "geo": ("geo",),
    "dendro": ("dendro",),
    "ether": ("eter", "ether"),
}

_JUNK_SET_TOKENS = (
    "rainbow",
    "any 2pc",
    "any 2-pc",
    "mix",
    "flex",
    "nao informado",
    "nenhum",
    "conjunto geral recomendado",
    "cone de luz assinatura",
    "opcao 4",
)


def _strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(c))


def normalize_equipment_key(name: str) -> str:
    """Normaliza nome de arma ou conjunto para chave alfanumérica pura."""
    if not name:
        return ""
    s = str(name).strip()
    s = _RE_BRACKET_TAG.sub(" ", s)
    s = _RE_PIECE_PREFIX.sub("", s)
    s = _RE_PIECE_SUFFIX.sub("", s)
    # Remove sufixos entre parênteses como (S1), (R5), (Nv. 80, R1), (4-PC), (100% de eficácia)
    while True:
        new_s = _RE_PARENS_TAIL.sub("", s).strip()
        if new_s == s:
            break
        s = new_s
    if " - —" in s:
        s = s.split(" - —", 1)[0].strip()
    s = _strip_accents(s).lower()
    return _RE_NON_ALNUM.sub("", s)


def _resolve_catalog_path(game_id: str) -> str:
    g = (game_id or "").lower().strip()
    rel = os.path.join("static_data", f"{g}_equipment_effects.json")
    data_p = get_data_path(rel)
    if os.path.exists(data_p):
        return data_p
    res_p = get_resource_path(rel)
    if os.path.exists(res_p):
        return res_p
    return ""


def _build_index(raw_map: Dict[str, Any]) -> Dict[str, Any]:
    by_norm: Dict[str, Dict[str, Any]] = {}
    entries: List[Tuple[str, Dict[str, Any]]] = []

    for _k, obj in (raw_map or {}).items():
        if not isinstance(obj, dict):
            continue
        name_pt = str(obj.get("name") or "").strip()
        aliases = [str(a).strip() for a in (obj.get("aliases") or []) if str(a).strip()]
        # Primeiro alias EN limpo (evita nomes de peças individuais quando houver alias EN do set)
        name_en = aliases[0] if aliases else name_pt
        entry = {
            "id": str(obj.get("id") or normalize_equipment_key(name_pt)),
            "name_pt": name_pt,
            "name_en": name_en,
            "is_planar": bool(obj.get("is_planar", False)),
            "all_names": [name_pt] + aliases,
        }
        seen_norms = set()
        for nm in entry["all_names"]:
            nk = normalize_equipment_key(nm)
            if nk and nk not in seen_norms:
                seen_norms.add(nk)
                # Prioriza nome principal sobre aliases secundários
                if nk not in by_norm or nm == name_pt:
                    by_norm[nk] = entry
                entries.append((nk, entry))

    return {"by_norm": by_norm, "entries": entries}


def get_equipment_catalog(game_id: str) -> Dict[str, Any]:
    """Carrega e indexa dinamicamente static_data/{game_id}_equipment_effects.json com cache por mtime."""
    g = (game_id or "").lower().strip()
    path = _resolve_catalog_path(g)
    if not path:
        return {"weapons": {"by_norm": {}, "entries": []}, "sets": {"by_norm": {}, "entries": []}}

    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0.0

    cached = _CATALOG_CACHE.get(g)
    if cached and cached[0] == mtime:
        return cached[1]

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        raw = {}

    indexed = {
        "weapons": _build_index(raw.get("weapons") or {}),
        "sets": _build_index(raw.get("sets") or {}),
    }
    _CATALOG_CACHE[g] = (mtime, indexed)
    return indexed


def resolve_equipment_entry(game_id: str, kind: str, raw_name: str) -> Optional[Dict[str, Any]]:
    """
    Resolve um nome de arma ou conjunto (em PT-BR ou EN-US) para sua entrada oficial canônica.
    Suporta nomes abreviados comuns em guias Prydwen (ex.: 'Drill Rig' -> 'Drill Rig - Red Axis').
    """
    if not raw_name:
        return None
    nk = normalize_equipment_key(raw_name)
    if not nk or len(nk) < 3:
        return None

    catalog = get_equipment_catalog(game_id).get(kind) or {}
    by_norm = catalog.get("by_norm") or {}

    # 1. Correspondência exata normalizada (O(1))
    hit = by_norm.get(nk)
    if hit:
        return hit

    # 2. Se houver " - " (ex.: nota anexada ou subtítulo), tenta prefixo antes do hífen
    raw_str = str(raw_name).strip()
    if " - " in raw_str:
        head_nk = normalize_equipment_key(raw_str.split(" - ", 1)[0])
        if head_nk and head_nk in by_norm:
            return by_norm[head_nk]

    # 3. Correspondência segura por prefixo/sufixo para nomes abreviados (ex.: ZZZ 'Drill Rig', 'Peacekeeper')
    if len(nk) >= 6:
        candidates: List[Tuple[int, Dict[str, Any]]] = []
        seen_ids = set()
        for entry_nk, entry in catalog.get("entries") or []:
            if len(entry_nk) < 6:
                continue
            if entry_nk.startswith(nk) or nk.startswith(entry_nk) or (len(nk) >= 8 and (nk in entry_nk or entry_nk in nk)):
                eid = entry["id"]
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    candidates.append((abs(len(entry_nk) - len(nk)), entry))
        if len(candidates) == 1:
            return candidates[0][1]
        if candidates:
            candidates.sort(key=lambda x: x[0])
            # Aceita se o melhor candidato for claramente mais próximo que o segundo
            if len(candidates) == 1 or candidates[0][0] + 4 < candidates[1][0]:
                return candidates[0][1]

    return None


def localize_equipment_name(game_id: str, kind: str, raw_name: str, lang: str = "pt") -> str:
    """
    Traduz nome de arma/conjunto usando exclusivamente o catálogo oficial HoYoVerse.
    Se o item não estiver no catálogo (ex.: patch futuro ainda não sincronizado ou combo '2p + 2p'),
    devolve o nome original limpo sem jamais corrompê-lo com tradução palavra por palavra.
    """
    if not raw_name:
        return ""
    s = str(raw_name).strip()
    if "+" in s:
        parts = [p.strip() for p in s.split("+") if p.strip()]
        if len(parts) == 2:
            return " + ".join(localize_equipment_name(game_id, kind, p, lang=lang) for p in parts)

    entry = resolve_equipment_entry(game_id, kind, s)
    if entry:
        return entry["name_en"] if str(lang).lower().startswith("en") else entry["name_pt"]
    return s


def is_junk_set_name(raw_name: str) -> bool:
    low = _strip_accents(str(raw_name or "")).lower().strip()
    if not low or len(low) < 3:
        return True
    return any(tok in low for tok in _JUNK_SET_TOKENS)


def parse_player_set_entry(game_id: str, raw_label: str) -> Dict[str, Any]:
    """Extrai nome limpo, contagem de peças (2/4) e entrada canônica de um conjunto equipado pelo jogador."""
    s = str(raw_label or "").strip()
    pieces = 0
    m_suf = _RE_PIECE_SUFFIX.search(s)
    if m_suf:
        pieces = int(m_suf.group(1))
        clean = s[: m_suf.start()].strip()
    else:
        m_pre = _RE_PIECE_PREFIX.match(s)
        if m_pre:
            pieces = int(m_pre.group(1))
            clean = s[m_pre.end() :].strip()
        else:
            clean = s

    entry = resolve_equipment_entry(game_id, "sets", clean)
    return {
        "raw": s,
        "clean": clean,
        "pieces": pieces,
        "id": entry["id"] if entry else "",
        "norm": normalize_equipment_key(clean),
        "name_pt": entry["name_pt"] if entry else clean,
        "name_en": entry["name_en"] if entry else clean,
        "is_planar": bool(entry["is_planar"]) if entry else False,
    }


def _items_match(
    game_id: str,
    kind: str,
    player_raw: str,
    target_raw: str,
    player_entry: Optional[Dict[str, Any]] = None,
    target_entry: Optional[Dict[str, Any]] = None,
) -> bool:
    """Compara dois nomes de equipamento por ID canônico oficial, com fallback seguro para nomes não catalogados."""
    p_ent = player_entry if player_entry is not None else resolve_equipment_entry(game_id, kind, player_raw)
    t_ent = target_entry if target_entry is not None else resolve_equipment_entry(game_id, kind, target_raw)

    if p_ent and t_ent:
        return p_ent["id"] == t_ent["id"]

    # Fallback para nomes ainda fora do catálogo (ex.: personagem Day-1 antes de sync de equipamentos)
    p_norm = normalize_equipment_key(player_raw)
    t_norm = normalize_equipment_key(target_raw)
    if not p_norm or not t_norm:
        return False
    if p_norm == t_norm:
        return True
    if len(p_norm) >= 6 and len(t_norm) >= 6 and (p_norm in t_norm or t_norm in p_norm):
        return True
    return False


def _extract_element_tag(clean_text: str) -> str:
    for elem_key, kws in _ELEMENT_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", clean_text) for kw in kws):
            return elem_key
    return ""


def normalize_main_stat_key(raw_str: str) -> Tuple[str, str]:
    """
    Normaliza qualquer atributo principal (PT-BR ou EN-US) em (stat_key, element_tag).
    A ordem de precedência impede colisões clássicas como:
      - 'Taxa de Regen. Energia' / 'Energy Regen Rate' -> 'er' (NUNCA 'crit_rate')
      - 'Taxa de Acerto de Efeito' / 'Effect Hit Rate' -> 'ehr' (NUNCA 'crit_rate')
      - 'Taxa de Perfuração' / 'PEN Ratio' -> 'pen_pct' (NUNCA 'crit_rate')
      - 'Proficiência de Anomalia' != 'Maestria de Anomalia'
    """
    if not raw_str:
        return "", ""

    s = _strip_accents(str(raw_str)).lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = _RE_NUMBERS_UNITS.sub(" ", s)
    s = re.sub(r"[\.\-_/]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return "", ""

    # 1. Curinga / Flex
    if s in ("anything", "any", "qualquer", "flex", "flexible", "flexivel") or "qualquer" in s or "anything" in s:
        return "anything", ""

    # 2. Energia (ER / ERR) — ANTES de 'taxa'/'rate'!
    if any(k in s for k in ("recarga", "recharge", "regen", "recup", "energia", "energy")) or s in ("er", "err"):
        return "er", ""

    # 3. Acerto de Efeito (EHR) — ANTES de 'taxa'/'rate'!
    if any(k in s for k in ("acerto de efeito", "acerto efeito", "effect hit", "ehr")):
        return "ehr", ""

    # 4. Resistência a Efeito (RES)
    if any(k in s for k in ("resistencia a efeito", "res efeito", "res a efeito", "effect res")) or s == "res":
        return "res", ""

    # 5. Perfuração (PEN / PEN Ratio) — ANTES de 'taxa'/'rate'!
    if any(k in s for k in ("perfura", "pen ratio", "pen rate")) or re.search(r"\bpen\b", s):
        return "pen_pct", ""

    # 6. Quebra (HSR)
    if any(k in s for k in ("quebra", "break")) or s == "be":
        return "break_effect", ""

    # 7. ZZZ Anomalia (separa Proficiência vs Maestria!)
    if any(k in s for k in ("proficiencia de anomalia", "prof anomalia", "anomaly proficiency", "anomaly prof")) or s == "ap":
        return "anomaly_prof", ""
    if any(
        k in s
        for k in (
            "maestria de anomalia",
            "maest anomalia",
            "controle de anomalia",
            "taxa de controle",
            "anomaly mastery",
        )
    ) or s == "am":
        return "anomaly_mastery", ""

    # 8. Proficiência Elemental (Genshin)
    if any(k in s for k in ("proficiencia", "elemental mastery", "maestria elemental", "prof element")) or s == "em":
        return "em", ""

    # 9. Taxa / Dano Crítico
    if any(k in s for k in ("taxa crit", "crit rate", "chance de crit", "chance crit", "tx cr", "tx crit")) or s == "cr":
        return "crit_rate", ""
    if any(k in s for k in ("dano crit", "crit dmg", "crit damage", "dano crt")) or s in ("cd", "cdmg"):
        return "crit_dmg", ""
    if "crit" in s:
        return "crit", ""

    # 10. Cura / Impacto / Velocidade
    if any(k in s for k in ("cura", "healing")):
        return "healing", ""
    if "impact" in s:
        return "impact", ""
    if any(k in s for k in ("vel", "spd", "speed")):
        return "spd", ""

    # 11. Bônus de Dano Elemental / Físico (com detecção de elemento específico quando presente)
    elem_tag = _extract_element_tag(s)
    if elem_tag or any(k in s for k in ("dano", "dmg", "damage", "elemental", "bonus")):
        return "elem_dmg", elem_tag

    # 12. Stats base (ATQ / PV / DEF)
    if any(k in s for k in ("atq", "atk", "ataque", "attack")):
        return "atk", ""
    if any(k in s for k in ("pv", "hp", "vida")):
        return "hp", ""
    if any(k in s for k in ("def", "defesa", "defense")):
        return "def", ""

    return s, ""


def _main_stats_match(player_key: Tuple[str, str], opt_key: Tuple[str, str]) -> bool:
    p_stat, p_elem = player_key
    o_stat, o_elem = opt_key
    if not p_stat or not o_stat:
        return False
    if o_stat == "anything":
        return True
    if o_stat == "crit" and p_stat in ("crit_rate", "crit_dmg", "crit"):
        return True
    if p_stat == "elem_dmg" and o_stat == "elem_dmg":
        # Se ambos especificarem elemento, exige o mesmo elemento; se o guia disser apenas "Dano Elemental", aceita qualquer
        return (not o_elem) or (not p_elem) or (p_elem == o_elem)
    return p_stat == o_stat


def _unify_slot_key(slot_name: str, game_id: str) -> str:
    s = _strip_accents(str(slot_name or "")).lower().strip()
    g = (game_id or "").lower().strip()
    if g == "zzz":
        m = re.search(r"(\d)", s)
        if m:
            return f"disc_{m.group(1)}"
    if any(k in s for k in ("corpo", "body", "torso", "peito")):
        return "body"
    if any(k in s for k in ("bota", "pes", "feet")):
        return "feet"
    if any(k in s for k in ("esfera", "sphere")):
        return "planar_sphere"
    if any(k in s for k in ("corda", "rope")):
        return "link_rope"
    if any(k in s for k in ("areia", "ampulheta", "sands")):
        return "sands"
    if any(k in s for k in ("copo", "calice", "goblet")):
        return "goblet"
    if any(k in s for k in ("tiara", "coroa", "circlet")):
        return "circlet"
    return s


def evaluate_build_comparison(
    game_id: str,
    player_build: Dict[str, Any],
    meta_target: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Avalia canonicamente Arma (25 pts), Conjuntos/Planares (25 pts) e Main Stats por Slot (30 pts)
    usando o catálogo oficial dinâmico e normalização estrita de atributos.
    """
    g = (game_id or "").lower().strip()

    # ------------------------------------------------------------------
    # 1. ARMA / CONE DE LUZ / W-ENGINE (25 pts)
    # ------------------------------------------------------------------
    raw_player_weapon = str(player_build.get("weapon") or "Não informado")
    clean_player_weapon = str(player_build.get("weapon_clean") or "").strip()
    if not clean_player_weapon and raw_player_weapon != "Não informado":
        clean_player_weapon = re.sub(r"\s*\([^)]*\)", "", raw_player_weapon).strip()

    has_player_weapon = bool(
        clean_player_weapon
        and not clean_player_weapon.lower().startswith(("não informado", "nao informado", "nenhum"))
    )
    player_w_entry = resolve_equipment_entry(g, "weapons", clean_player_weapon) if has_player_weapon else None

    raw_rec_weapons = list(meta_target.get("weapons_raw") or meta_target.get("weapons") or [])
    if not raw_rec_weapons and meta_target.get("weapon") and meta_target.get("weapon") != "Não informado":
        raw_rec_weapons = [meta_target["weapon"]]

    resolved_weapons_pt: List[str] = []
    resolved_weapons_en: List[str] = []
    rec_weapon_entries: List[Optional[Dict[str, Any]]] = []
    for rw in raw_rec_weapons:
        ent = resolve_equipment_entry(g, "weapons", rw)
        rec_weapon_entries.append(ent)
        resolved_weapons_pt.append(ent["name_pt"] if ent else rw)
        resolved_weapons_en.append(ent["name_en"] if ent else rw)

    weapon_tier = 0
    weapon_score = 0
    matched_idx = -1
    if has_player_weapon and raw_rec_weapons:
        for idx, rw in enumerate(raw_rec_weapons):
            if _items_match(g, "weapons", clean_player_weapon, rw, player_w_entry, rec_weapon_entries[idx]):
                matched_idx = idx
                break
        if matched_idx == 0:
            weapon_tier = 1
            weapon_score = 25
        elif matched_idx > 0:
            weapon_tier = 2
            weapon_score = 20
        elif len(clean_player_weapon) > 3:
            weapon_tier = 3
            weapon_score = 12

    weapon_eval = {
        "tier": weapon_tier,
        "score": weapon_score,
        "matched_index": matched_idx,
        "bis_name_pt": resolved_weapons_pt[0] if resolved_weapons_pt else "Não informado",
        "bis_name_en": resolved_weapons_en[0] if resolved_weapons_en else "Not available",
        "weapons_pt": resolved_weapons_pt,
        "weapons_en": resolved_weapons_en,
        "options_count": len(raw_rec_weapons),
    }

    # ------------------------------------------------------------------
    # 2. CONJUNTOS / RELÍQUIAS / PLANARES / DISCOS (25 pts)
    # ------------------------------------------------------------------
    player_sets_parsed = [
        parse_player_set_entry(g, ps)
        for ps in (player_build.get("sets") or [])
        if ps and not str(ps).lower().strip().startswith(("nenhum", "não informado", "nao informado"))
    ]

    raw_relic_sets = [
        s for s in (meta_target.get("relic_sets_raw") or meta_target.get("all_sets_raw") or meta_target.get("all_sets") or [])
        if not is_junk_set_name(s)
    ]
    raw_planar_sets = [
        s for s in (meta_target.get("planar_sets_raw") or meta_target.get("planar_sets") or [])
        if not is_junk_set_name(s)
    ]

    # Se for HSR e planar_sets não veio separado, separa automaticamente usando flag is_planar do catálogo!
    if g == "hsr" and not raw_planar_sets and raw_relic_sets:
        cavern_only: List[str] = []
        planar_only: List[str] = []
        for rs in raw_relic_sets:
            ent = resolve_equipment_entry(g, "sets", rs)
            if ent and ent.get("is_planar"):
                planar_only.append(rs)
            else:
                cavern_only.append(rs)
        if cavern_only:
            raw_relic_sets = cavern_only
        raw_planar_sets = planar_only

    rec_relic_entries = [resolve_equipment_entry(g, "sets", s) for s in raw_relic_sets]
    rec_planar_entries = [resolve_equipment_entry(g, "sets", s) for s in raw_planar_sets]

    relics_pt = [
        ent["name_pt"] if ent else localize_equipment_name(g, "sets", s, "pt")
        for s, ent in zip(raw_relic_sets, rec_relic_entries)
    ]
    relics_en = [
        ent["name_en"] if ent else localize_equipment_name(g, "sets", s, "en")
        for s, ent in zip(raw_relic_sets, rec_relic_entries)
    ]
    planars_pt = [
        ent["name_pt"] if ent else localize_equipment_name(g, "sets", s, "pt")
        for s, ent in zip(raw_planar_sets, rec_planar_entries)
    ]
    planars_en = [
        ent["name_en"] if ent else localize_equipment_name(g, "sets", s, "en")
        for s, ent in zip(raw_planar_sets, rec_planar_entries)
    ]

    def _player_matches_set(p_set: Dict[str, Any], target_raw: str, target_ent: Optional[Dict[str, Any]]) -> bool:
        if "+" in target_raw:
            return any(
                _items_match(g, "sets", p_set["clean"], sub.strip(), {"id": p_set["id"]} if p_set["id"] else None, None)
                for sub in target_raw.split("+")
                if sub.strip()
            )
        p_ent_obj = {"id": p_set["id"]} if p_set["id"] else None
        return _items_match(g, "sets", p_set["clean"], target_raw, p_ent_obj, target_ent)

    set_tier = 0
    set_score = 0
    has_bis_relic = False
    has_rec_relic = False
    has_bis_planar = False
    has_rec_planar = False
    has_any_active_bonus = any(ps["pieces"] >= 2 for ps in player_sets_parsed)

    if player_sets_parsed and (raw_relic_sets or raw_planar_sets):
        if raw_relic_sets:
            bis_relic_raw = raw_relic_sets[0]
            bis_relic_ent = rec_relic_entries[0]
            is_bis_combo_2p = "+" in bis_relic_raw
            for ps in player_sets_parsed:
                if _player_matches_set(ps, bis_relic_raw, bis_relic_ent):
                    if ps["pieces"] >= 4 or (is_bis_combo_2p and ps["pieces"] >= 2):
                        has_bis_relic = True
                    if ps["pieces"] >= 2:
                        has_rec_relic = True
            if not has_rec_relic:
                for idx, rs in enumerate(raw_relic_sets):
                    if any(ps["pieces"] >= 2 and _player_matches_set(ps, rs, rec_relic_entries[idx]) for ps in player_sets_parsed):
                        has_rec_relic = True
                        break

        if raw_planar_sets:
            if any(
                ps["pieces"] >= 2 and _player_matches_set(ps, raw_planar_sets[0], rec_planar_entries[0])
                for ps in player_sets_parsed
            ):
                has_bis_planar = True
                has_rec_planar = True
            else:
                for idx, pl in enumerate(raw_planar_sets):
                    if any(ps["pieces"] >= 2 and _player_matches_set(ps, pl, rec_planar_entries[idx]) for ps in player_sets_parsed):
                        has_rec_planar = True
                        break

        if g == "hsr" and raw_planar_sets:
            if has_bis_relic and has_bis_planar:
                set_tier = 1
                set_score = 25
            elif has_bis_relic and has_rec_planar:
                set_tier = 1
                set_score = 24
            elif has_bis_relic:
                set_tier = 1
                set_score = 22
            elif has_rec_relic and has_bis_planar:
                set_tier = 2
                set_score = 22
            elif has_rec_relic or has_rec_planar:
                set_tier = 2
                set_score = 20
            elif has_any_active_bonus:
                set_tier = 3
                set_score = 12
        else:
            if has_bis_relic:
                set_tier = 1
                set_score = 25
            elif has_rec_relic:
                set_tier = 2
                set_score = 20
            elif has_any_active_bonus:
                set_tier = 3
                set_score = 12

    set_eval = {
        "tier": set_tier,
        "score": set_score,
        "has_bis_relic": has_bis_relic,
        "has_rec_relic": has_rec_relic,
        "has_bis_planar": has_bis_planar,
        "has_rec_planar": has_rec_planar,
        "bis_set_pt": relics_pt[0] if relics_pt else "Não informado",
        "bis_set_en": relics_en[0] if relics_en else "Not available",
        "bis_planar_pt": planars_pt[0] if planars_pt else "",
        "bis_planar_en": planars_en[0] if planars_en else "",
        "sets_pt": relics_pt,
        "sets_en": relics_en,
        "planar_sets_pt": planars_pt,
        "planar_sets_en": planars_en,
    }

    # ------------------------------------------------------------------
    # 3. ATRIBUTOS PRINCIPAIS POR SLOT (30 pts)
    # ------------------------------------------------------------------
    target_stats = meta_target.get("stats") or {}
    pieces_list = player_build.get("pieces") or []
    slot_evals: List[Dict[str, Any]] = []
    slots_score_total = 0.0
    slot_issues: List[str] = []

    if target_stats:
        pts_per_slot = 30.0 / len(target_stats)
        for slot_lbl, raw_target_val in target_stats.items():
            t_key = _unify_slot_key(slot_lbl, g)
            matched_piece = None
            for pc in pieces_list:
                p_slot = str(pc.get("slot") or "")
                p_key = _unify_slot_key(p_slot, g)
                if (p_key and t_key and p_key == t_key) or (
                    slot_lbl.lower().strip() in p_slot.lower().strip()
                ):
                    matched_piece = pc
                    break

            raw_t_str = str(raw_target_val or "").strip()
            target_en = re.sub(r"Qualquer\s*\(Flex\)", "Any (Flex)", raw_t_str, flags=re.IGNORECASE)

            if not matched_piece or not matched_piece.get("main"):
                slot_issues.append(slot_lbl)
                slot_evals.append(
                    {
                        "slot": slot_lbl,
                        "player_main": "",
                        "target_pt": raw_t_str,
                        "target_en": target_en,
                        "status": "empty",
                        "score": 0.0,
                    }
                )
                continue

            p_main = str(matched_piece.get("main") or "")
            p_norm_key = normalize_main_stat_key(p_main)
            options = [opt.strip() for opt in _RE_SPLIT_OPTIONS.split(raw_t_str) if opt.strip()]
            opt_keys = [normalize_main_stat_key(opt) for opt in options]

            is_wildcard = any(ok[0] == "anything" for ok in opt_keys)
            first_match = bool(opt_keys) and _main_stats_match(p_norm_key, opt_keys[0])
            any_match = first_match or is_wildcard or any(_main_stats_match(p_norm_key, ok) for ok in opt_keys[1:])

            if is_wildcard and (not opt_keys or opt_keys[0][0] == "anything" or len(opt_keys) == 1):
                status = "flex"
                s_pts = pts_per_slot
            elif first_match or is_wildcard:
                status = "ideal"
                s_pts = pts_per_slot
            elif any_match:
                status = "valid"
                s_pts = pts_per_slot * 0.75
            else:
                status = "mismatch"
                s_pts = 0.0
                slot_issues.append(f"{slot_lbl} ({raw_t_str})")

            slots_score_total += s_pts
            slot_evals.append(
                {
                    "slot": slot_lbl,
                    "player_main": p_main,
                    "target_pt": raw_t_str,
                    "target_en": target_en,
                    "status": status,
                    "score": round(s_pts, 2),
                }
            )

    return {
        "weapon": weapon_eval,
        "sets": set_eval,
        "slots": slot_evals,
        "slots_score": round(slots_score_total, 2),
        "slot_issues": slot_issues,
    }
