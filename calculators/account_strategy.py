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

    # ==========================================
    # 1. GENSHIN IMPACT
    # ==========================================
    if g == "genshin":
        # Arquétipos
        sustain_t0 = ["zhongli", "kokomi", "baizhu", "xianyun", "bennett", "kuki shinobu", "sigewinne"]
        sustain_others = [
            "diona",
            "layla",
            "kirara",
            "jean",
            "charlotte",
            "yaoyao",
            "barbara",
            "noelle",
            "sayu",
            "chevreuse",
            "mika",
            "thoma",
            "qiqi",
        ]
        owned_sustain_t0 = count_in_group(sustain_t0)
        owned_sustain_all = count_in_group(sustain_t0 + sustain_others)

        buffers_t0 = ["furina", "kazuha", "nahida", "xilonen", "shenhe", "sucrose", "faruzan", "emilie"]
        buffers_others = ["lynette", "gorou", "yun jin", "kujou sara", "candace", "traveler"]
        owned_buffers_t0 = count_in_group(buffers_t0)
        owned_buffers_all = count_in_group(buffers_t0 + buffers_others)

        offfield_hydro = ["xingqiu", "yelan", "furina", "kokomi", "sigewinne"]
        owned_offfield_hydro = count_in_group(offfield_hydro)

        main_dps_list = [
            "neuvillette",
            "arlecchino",
            "alhaitham",
            "raiden shogun",
            "hu tao",
            "navia",
            "mualani",
            "kinich",
            "clorinde",
            "lyney",
            "wriothesley",
            "xiao",
            "wanderer",
            "kamisato ayaka",
            "ganyu",
            "arataki itto",
            "tartaglia",
            "cyno",
            "tighnari",
            "diluc",
            "keqing",
            "gaming",
            "yanfei",
            "sethos",
        ]
        owned_main_dps = count_in_group(main_dps_list)

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
                "description": "Essencial para sobrevivência nos 2 lados do Abismo 12.",
            }
        )

        st_buff, col_buff = get_status_data(len(owned_buffers_all), len(owned_buffers_t0), 2)
        archetypes_summary.append(
            {
                "key": "buffers",
                "title": "Buffers & Redução de RES (VV / Suportes)",
                "icon": "fa-wand-magic-sparkles",
                "status": st_buff,
                "status_color": col_buff,
                "owned_count": len(owned_buffers_all),
                "target_count": 2,
                "owned_characters": owned_buffers_all,
                "description": "Multiplicadores de dano e reações elementais da equipe.",
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
                "description": "Coluna vertebral para Vaporize, Hyperbloom, Taser e Freeze.",
            }
        )

        st_dps, col_dps = get_status_data(len(owned_main_dps), len(owned_main_dps), 2)
        archetypes_summary.append(
            {
                "key": "main_dps",
                "title": "DPS Principal (Hypercarries / Reaction)",
                "icon": "fa-khanda",
                "status": st_dps,
                "status_color": col_dps,
                "owned_count": len(owned_main_dps),
                "target_count": 2,
                "owned_characters": owned_main_dps,
                "description": "Pilares de dano para as duas metades das câmaras de combate.",
            }
        )

        # Cobertura Elemental (dinâmica via roster + static_data/)
        elemental_coverage.extend(_compute_elemental_coverage("genshin", owned_chars_map))

        # Lacunas Críticas
        if len(owned_sustain_t0) == 0:
            overall_score -= 22
            critical_gaps.append(
                {
                    "id": "genshin_no_t0_sustain",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "🛡️ Sobrevivência em Risco",
                    "title": "Falta de Sustentador Premium Tier 0",
                    "description": "Você não possui nenhum curandeiro/escudo de elite (Zhongli, Kokomi, Baizhu, Xianyun ou Bennett).",
                    "endgame_impact": "Alta dificuldade para manter a rotação viva e evitar interrupções no Abismo 12.",
                    "suggested_archetype": "Shielder Indestrutível ou Healer Global com utilidade de Buff",
                    "recommended_characters": ["Zhongli", "Kokomi", "Baizhu", "Xianyun"],
                }
            )

        if len(owned_offfield_hydro) < 2:
            overall_score -= 18
            critical_gaps.append(
                {
                    "id": "genshin_lack_hydro",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "💧 Carência de Aplicação Hydro",
                    "title": "Falta de Aplicador Hydro Off-Field para 2 Times",
                    "description": "Possui menos de 2 aplicadores Hydro (Xingqiu, Yelan, Furina).",
                    "endgame_impact": "Limita severamente a formação de times simultâneos de Vaporize, Hyperbloom ou Freeze.",
                    "suggested_archetype": "Sub-DPS / Buffer Hydro Off-Field",
                    "recommended_characters": ["Yelan", "Furina", "Xingqiu"],
                }
            )

        has_vv, _ = has_any(["kazuha", "sucrose"])
        if not has_vv:
            overall_score -= 15
            critical_gaps.append(
                {
                    "id": "genshin_no_vv_shred",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "🌪️ Sem Redução Elemental VV",
                    "title": "Ausência de Buffer Anemo Sombra Verde (VV)",
                    "description": "Você não tem Kazuha ou Sacarose para aplicar o debuff de 40% de RES Shred.",
                    "endgame_impact": "Perda direta de ~25% a 30% do DPS final em composições de reação elemental.",
                    "suggested_archetype": "Buffer / Agrupador Anemo",
                    "recommended_characters": ["Kaedehara Kazuha", "Sucrose"],
                }
            )

        if len(owned_main_dps) < 2:
            overall_score -= 20
            critical_gaps.append(
                {
                    "id": "genshin_lack_main_dps",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "⚔️ Carência de Dano Principal",
                    "title": "Menos de 2 Hypercarries/Drivers Construídos",
                    "description": "Faltam carregadores de dano principais para cobrir as duas câmaras do Abismo 12.",
                    "endgame_impact": "Incapacidade de atingir as metas de DPS para fechar com 36 estrelas.",
                    "suggested_archetype": "DPS Principal Top-Tier",
                    "recommended_characters": ["Neuvillette", "Arlecchino", "Alhaitham", "Navia"],
                }
            )

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_sustain_t0) == 0:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Sustentador / Shielder Tier 0",
                    "badge": "Prioridade Máxima",
                    "tag": "Sobrevivência & Conforto",
                    "characters": ["Zhongli", "Xilonen", "Kokomi"],
                    "reason": "Garante estabilidade absoluta de rotação no Abismo 12 sem interrupções de golpes inimigos.",
                    "impact_score": "+35% Conforto & Consistência de Clear",
                }
            )
            rank_idx += 1

        if not has_any(["furina", "kazuha"])[0]:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Universal Damage Buffer",
                    "badge": "Alta Prioridade",
                    "tag": "Salto de DPS Global",
                    "characters": ["Furina", "Kaedehara Kazuha"],
                    "reason": "Aumenta drasticamente o dano de quase todas as equipes do jogo através de buffs globais e RES shred.",
                    "impact_score": "+30% a 40% Dano Global da Equipe",
                }
            )
            rank_idx += 1

        if len(owned_main_dps) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Hypercarry On-Field",
                    "badge": "Alta Prioridade",
                    "tag": "DPS de Fechamento",
                    "characters": ["Neuvillette", "Arlecchino"],
                    "reason": "Unidades independentes e com multiplicadores colossais para carregar um lado inteiro do Abismo.",
                    "impact_score": "Garante 1 lado completo do Abismo 12",
                }
            )
            rank_idx += 1

    # ==========================================
    # 2. HONKAI: STAR RAIL
    # ==========================================
    elif g == "hsr":
        # Arquétipos
        harmony_t0 = ["ruan mei", "robin", "sparkle", "sunday", "bronya", "tingyun"]
        owned_harmony_t0 = count_in_group(harmony_t0)

        sustain_5star = ["aventurine", "huohuo", "fu xuan", "lingsha", "luocha"]
        sustain_all = sustain_5star + ["gallagher", "lynx", "natasha", "bailu", "gepard", "march 7th"]
        owned_sustain_5star = count_in_group(sustain_5star)
        owned_sustain_all = count_in_group(sustain_all)

        break_archetype = [
            "firefly",
            "boothill",
            "rappa",
            "trailblazer",
            "xueyi",
            "fugue",
            "ruan mei",
            "gallagher",
            "lingsha",
        ]
        owned_break = count_in_group(break_archetype)

        fua_archetype = [
            "feixiao",
            "aventurine",
            "robin",
            "topaz",
            "dr. ratio",
            "yunli",
            "clara",
            "moze",
            "march 7th",
            "jade",
        ]
        owned_fua = count_in_group(fua_archetype)

        pf_erudition = ["herta", "himeko", "jade", "argenti", "acheron"]
        owned_pf = count_in_group(pf_erudition)

        crit_hypercarries = [
            "acheron",
            "feixiao",
            "dan heng il",
            "jingliu",
            "dr. ratio",
            "yunli",
            "argenti",
            "blade",
            "jing yuan",
            "clara",
            "seele",
        ]
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
                "description": "Peças fundamentais para turnos extras, penetração de resistência e buffs de crítico.",
            }
        )

        st_sust, col_sust = get_hsr_status(len(owned_sustain_all), len(owned_sustain_5star), 2)
        archetypes_summary.append(
            {
                "key": "sustain",
                "title": "Sustentadores de Elite (Preservação / Abundância)",
                "icon": "fa-shield-halved",
                "status": st_sust,
                "status_color": col_sust,
                "owned_count": len(owned_sustain_all),
                "target_count": 2,
                "owned_characters": owned_sustain_5star if owned_sustain_5star else owned_sustain_all,
                "description": "Imunidade a controle (CC), escudos inquebráveis e cura reativa para MoC 12 e AS 4.",
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
                "description": "Dominância contra fraquezas e velocidade de limpeza em Sombra Apocalíptica.",
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
                "title": "Especialistas em AoE / Pura Ficção",
                "icon": "fa-meteor",
                "status": st_pf,
                "status_color": col_pf,
                "owned_count": len(owned_pf),
                "target_count": 2,
                "owned_characters": owned_pf,
                "description": "Erudição e dano em área contínuo para bater 60.000+ pontos na Pura Ficção.",
            }
        )

        # Cobertura Elemental (dinâmica via roster + static_data/)
        elemental_coverage.extend(_compute_elemental_coverage("hsr", owned_chars_map))

        # Lacunas Críticas
        if len(owned_harmony_t0) < 2:
            overall_score -= 22
            critical_gaps.append(
                {
                    "id": "hsr_lack_tier0_harmony",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "🎵 Déficit de Harmonia Tier 0",
                    "title": "Menos de 2 Suportes Harmonia Premium",
                    "description": "Você possui menos de 2 buffers de alta geração de turnos (Ruan Mei, Robin, Sparkle, Sunday).",
                    "endgame_impact": "Queda drástica de ciclos no MoC e dificuldade de alcançar os 40.000 pts na Pura Ficção.",
                    "suggested_archetype": "Harmonia Limitada (Avanço de Ação / Penetração de RES / DMG%)",
                    "recommended_characters": ["Robin", "Ruan Mei", "Sunday", "Sparkle"],
                }
            )

        if len(owned_sustain_5star) < 2:
            overall_score -= 20
            critical_gaps.append(
                {
                    "id": "hsr_lack_5star_sustain",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "🛡️ Sustentação de Alto Nível",
                    "title": "Falta de 2 Sustentadores Limitados 5★",
                    "description": "Você não possui 2 sustentadores premium (Aventurine, Huohuo, Fu Xuan, Lingsha).",
                    "endgame_impact": "Vulnerabilidade a debuffs de controle (Crowd Control) e one-shots nos andares 11 e 12.",
                    "suggested_archetype": "Preservação / Abundância Limitada",
                    "recommended_characters": ["Aventurine", "Huohuo", "Lingsha", "Fu Xuan"],
                }
            )

        owned_pf_lower = {x.lower() for x in owned_pf}
        has_herta_himeko = any(k in owned_pf_lower for k in ("herta", "himeko", "jade"))
        if not has_herta_himeko:
            overall_score -= 15
            critical_gaps.append(
                {
                    "id": "hsr_no_pure_fiction_core",
                    "severity": "ALTA",
                    "severity_color": "#f97316",
                    "badge": "📖 Fraqueza em Pura Ficção",
                    "title": "Falta de Núcleo Especialista em AoE",
                    "description": "Herta ou Himeko não estão construídas na conta.",
                    "endgame_impact": "Dificuldade constante para obter a pontuação máxima (60.000 / 80.000) na Pura Ficção.",
                    "suggested_archetype": "Erudição / AoE Follow-Up",
                    "recommended_characters": ["Herta (Construir)", "Himeko", "Jade"],
                }
            )

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_harmony_t0) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Suporte Harmonia Universal (Robin / Sunday / Ruan Mei)",
                    "badge": "Prioridade Máxima",
                    "tag": "Multiplicador de Conta",
                    "characters": ["Robin", "Sunday", "Ruan Mei"],
                    "reason": "O maior upgrade de poder possível em Honkai: Star Rail. Transforma qualquer DPS em uma máquina de ciclos zero.",
                    "impact_score": "-2 a 4 Ciclos no Caos da Memória (MoC)",
                }
            )
            rank_idx += 1

        if len(owned_sustain_5star) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Sustentador 5★ de Elite (Aventurine / Huohuo)",
                    "badge": "Alta Prioridade",
                    "tag": "Segurança & Utilidade",
                    "characters": ["Aventurine", "Huohuo", "Lingsha"],
                    "reason": "Aventurine traz sinergia colossal com FuA/Acheron e escudos infinitos. Huohuo recarrega energia globalmente.",
                    "impact_score": "100% de Taxa de Sobrevivência no MoC 12",
                }
            )
            rank_idx += 1

        if len(owned_crit_dps) == 0 and len(owned_break) < 2:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "DPS de Elite (Acheron / Firefly / Feixiao)",
                    "badge": "Alta Prioridade",
                    "tag": "Finalizador de Endgame",
                    "characters": ["Acheron", "Firefly", "Feixiao"],
                    "reason": "Mecanismos de quebra que ignoram fraquezas ou rajadas de dano absurdas com escalonamento moderno.",
                    "impact_score": "Garante 36★ no MoC e 12★ na Sombra Apocalíptica",
                }
            )
            rank_idx += 1

    # ==========================================
    # 3. ZENLESS ZONE ZERO
    # ==========================================
    elif g == "zzz":
        # Arquétipos
        stunners_s = ["qingyi", "lycaon", "caesar", "koleda"]
        stunners_all = stunners_s + ["anby"]
        owned_stunners_s = count_in_group(stunners_s)
        owned_stunners_all = count_in_group(stunners_all)

        supports_s = ["caesar", "astra yao", "rina"]
        supports_all = supports_s + ["soukaku", "lucy", "nicole", "seth"]
        owned_supports_s = count_in_group(supports_s)
        owned_supports_all = count_in_group(supports_all)

        attack_dps = ["ellen", "zhu yuan", "soldier 11", "nekomata", "harumasa", "miyabi", "corin", "anton", "billy"]
        owned_attack_dps = count_in_group(attack_dps)

        anomaly_dps = ["jane doe", "burnice", "yanagi", "grace", "piper"]
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
                "description": "Multiplica o dano em 150%+ durante a janela de Atordoamento (Stun Window).",
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
                "title": "Suportes & Defesa (Buff de ATK / DEF Shred)",
                "icon": "fa-shield-halved",
                "status": st_supp,
                "status_color": col_supp,
                "owned_count": len(owned_supports_all),
                "target_count": 2,
                "owned_characters": owned_supports_all,
                "description": "Gera pontos de assistência, buffs de ATK puro e debuffs defensivos no inimigo.",
            }
        )

        st_atk = (
            "Excelente" if len(owned_attack_dps) >= 2 else ("Suficiente" if len(owned_attack_dps) >= 1 else "Atenção")
        )
        col_atk = "#10b981" if st_atk == "Excelente" else ("#3b82f6" if st_atk == "Suficiente" else "#f59e0b")
        archetypes_summary.append(
            {
                "key": "attack_dps",
                "title": "Agentes de Ataque (Burst / Dano Direto)",
                "icon": "fa-crosshairs",
                "status": st_atk,
                "status_color": col_atk,
                "owned_count": len(owned_attack_dps),
                "target_count": 2,
                "owned_characters": owned_attack_dps,
                "description": "Descarregam dano massivo durante as janelas de Chain Attack e Stun.",
            }
        )

        st_anom = (
            "Excelente" if len(owned_anomaly_dps) >= 2 else ("Suficiente" if len(owned_anomaly_dps) >= 1 else "Atenção")
        )
        col_anom = "#10b981" if st_anom == "Excelente" else ("#3b82f6" if st_anom == "Suficiente" else "#f59e0b")
        archetypes_summary.append(
            {
                "key": "anomaly_dps",
                "title": "Agentes de Anomalia (DoT / Desordem)",
                "icon": "fa-flask-vial",
                "status": st_anom,
                "status_color": col_anom,
                "owned_count": len(owned_anomaly_dps),
                "target_count": 2,
                "owned_characters": owned_anomaly_dps,
                "description": "Acumulam anomalia e causam Desordem contínua sem depender do atordoamento.",
            }
        )

        # Cobertura de Atributos ZZZ (dinâmica via roster + static_data/)
        elemental_coverage.extend(_compute_elemental_coverage("zzz", owned_chars_map))

        # Lacunas Críticas
        if len(owned_stunners_s) == 0:
            overall_score -= 22
            critical_gaps.append(
                {
                    "id": "zzz_no_s_stunner",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "⚡ Lentidão no Atordoamento",
                    "title": "Falta de Atordoador S-Rank (Qingyi / Lycaon / Caesar)",
                    "description": "Você depende exclusivamente da Anby como atordoadora nos 2 lados do Shiyu Defense.",
                    "endgame_impact": "Demora excessiva para atingir o estado de Stun nos Chefes da Shiyu Crítica (Nível 5-7).",
                    "suggested_archetype": "Atordoador S-Rank de Alto Impacto",
                    "recommended_characters": ["Qingyi", "Caesar", "Von Lycaon"],
                }
            )

        if len(owned_attack_dps) + len(owned_anomaly_dps) < 2:
            overall_score -= 25
            critical_gaps.append(
                {
                    "id": "zzz_lack_dps",
                    "severity": "CRÍTICA",
                    "severity_color": "#ef4444",
                    "badge": "⚔️ Carência de Finalizadores",
                    "title": "Falta de DPSs Principais para 2 Equipes",
                    "description": "Menos de 2 agentes de Ataque ou Anomalia de alto investimento.",
                    "endgame_impact": "Inviabiliza a obtenção de Rank S na Shiyu Defense dos dois lados.",
                    "suggested_archetype": "DPS S-Rank de Ataque ou Anomalia",
                    "recommended_characters": ["Ellen Joe", "Jane Doe", "Zhu Yuan", "Miyabi", "Burnice"],
                }
            )

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_stunners_s) == 0:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Atordoador S-Rank (Qingyi / Caesar)",
                    "badge": "Prioridade Máxima",
                    "tag": "Velocidade de Stun",
                    "characters": ["Qingyi", "Caesar"],
                    "reason": "Qingyi eleva o multiplicador de atordoamento para 200%+ e atordoa chefes na metade do tempo da Anby.",
                    "impact_score": "-40s no Tempo de Clear do Shiyu 7",
                }
            )
            rank_idx += 1

        if len(owned_anomaly_dps) == 0:
            pull_recommendations.append(
                {
                    "priority_rank": rank_idx,
                    "archetype": "Especialista em Anomalia / Desordem",
                    "badge": "Alta Prioridade",
                    "tag": "Novo Arquétipo Meta",
                    "characters": ["Jane Doe", "Burnice", "Yanagi"],
                    "reason": "Permite ignorar mecânicas de atordoamento e derreter inimigos com Desordem de alto escalonamento.",
                    "impact_score": "+30% Flexibilidade contra Chefes com Alta Resistência a Stun",
                }
            )
            rank_idx += 1

    # Normalização final da pontuação
    overall_score = max(20, min(100, overall_score))
    if overall_score >= 85:
        score_grade = "S"
        score_label = "Excelente Cobertura & Alta Prontidão"
        score_color = "#10b981"
    elif overall_score >= 70:
        score_grade = "A"
        score_label = "Conta Equilibrada com Boas Sinergias"
        score_color = "#3b82f6"
    elif overall_score >= 50:
        score_grade = "B"
        score_label = "Lacunas Moderadas em Arquétipos Chave"
        score_color = "#f59e0b"
    else:
        score_grade = "C"
        score_label = "Atenção: Carência Crítica de Suportes/Sustentação"
        score_color = "#ef4444"

    # Avaliação de Prontidão de Endgame
    endgame_teams_ready = 2 if len(critical_gaps) <= 1 and built_chars >= 6 else (1 if built_chars >= 3 else 0)
    endgame_readiness = {
        "status": f"{endgame_teams_ready}/2 Equipes Prontas para Endgame",
        "teams_ready": endgame_teams_ready,
        "summary": (
            "Sua conta possui fundações completas para fechar o conteúdo mais difícil do jogo com nota máxima."
            if endgame_teams_ready == 2
            else "Você tem 1 time competitivo consolidado, mas a segunda equipe precisa de reforços nos arquétipos sinalizados."
            if endgame_teams_ready == 1
            else "Concentre seus recursos e energia em elevar o nível e fechar as builds da sua equipe principal primeiro."
        ),
        "details": [gap["title"] for gap in critical_gaps],
    }

    # Resumo formatado em Markdown consolidado
    rag_lines = [
        f"### DIAGNÓSTICO DE LACUNAS DA CONTA ({game_names.get(g, g.upper())}):",
        f"- **Pontuação de Saúde da Conta:** {overall_score}/100 (Classificação: {score_grade} - {score_label})",
        f"- **Personagens Construídos (Prontos p/ Batalha):** {built_chars} de {total_chars}",
        f"- **Equipes Prontas p/ Endgame:** {endgame_teams_ready}/2 times",
    ]
    if critical_gaps:
        rag_lines.append("- **Lacunas Estratégicas Críticas Detectadas:**")
        for cg in critical_gaps:
            rag_lines.append(
                f"  * [{cg['severity']}] {cg['title']}: {cg['description']} -> *Recomendado buscar:* {', '.join(cg['recommended_characters'])}"
            )
    else:
        rag_lines.append("- **Lacunas:** Nenhuma carência grave detectada! Conta muito bem balanceada.")

    if pull_recommendations:
        rag_lines.append("- **Prioridades de Puxada no Gacha / Banners Futuros:**")
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

    def _find_craft_cfg(cand_name: str, game_key: str, meta_craft_map: dict, default_cfg: dict) -> dict:
        """Resolve o alvo de crafting normalizando espaços/pontuação e consultando slug canônico."""
        c_norm = _norm_str(cand_name)
        canon_norm = ""
        try:
            from meta_comparator import resolve_character_canonical_slug

            canon_norm = _norm_str(resolve_character_canonical_slug(game_key, cand_name))
        except Exception:
            pass

        for mk, cfg_val in meta_craft_map.items():
            mk_norm = _norm_str(mk)
            if (
                mk_norm in c_norm
                or c_norm in mk_norm
                or (canon_norm and (mk_norm in canon_norm or canon_norm in mk_norm))
            ):
                return cfg_val
        return default_cfg

    recommendations = []
    rank_counter = 1

    # ==========================================
    # REGRAS DE CRAFTING POR JOGO
    # ==========================================
    if g == "genshin":
        # Meta targets no Genshin
        meta_craft_genshin = {
            "neuvillette": {
                "set": "Caçador das Sombras",
                "slot": "Cálice de Eonothem (Slot 4)",
                "main": "Bônus de Dano Hydro (ou HP%)",
                "substats": ["Dano Crítico", "Taxa Crítica", "HP%", "Recarga de Energia"],
                "gain": "+25% Dano no Ataque Carregado Notável",
            },
            "furina": {
                "set": "Trompete do Éter / Companhia Dourada",
                "slot": "Ampulheta / Cálice (Slot 3 ou 4)",
                "main": "Recarga de Energia ou HP%",
                "substats": ["Taxa Crítica", "Dano Crítico", "HP%", "Recarga de Energia"],
                "gain": "Garante 100% de Uptime no Supremo Fanfarra",
            },
            "arlecchino": {
                "set": "Fragmento da Harmonia Caprichosa",
                "slot": "Cálice de Bônus Pyro (Slot 4)",
                "main": "Bônus de Dano Pyro",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Proficiência Elemental"],
                "gain": "+30% Eficiência em Golpes de Vaporize",
            },
            "kaedehara kazuha": {
                "set": "Sombra Verde (VV)",
                "slot": "Cálice / Tiara (Slot 4 ou 5)",
                "main": "Proficiência Elemental (EM)",
                "substats": ["Recarga de Energia", "Proficiência Elemental", "ATK%"],
                "gain": "Atinge a meta de 1.000 EM para buffer máximo de 40% DMG",
            },
            "nahida": {
                "set": "Memórias da Floresta (Deepwood)",
                "slot": "Tiara / Cálice (Slot 4 ou 5)",
                "main": "Proficiência Elemental (ou Taxa Crítica)",
                "substats": ["Proficiência Elemental", "Taxa Crítica", "Dano Crítico", "Recarga de Energia"],
                "gain": "Maximiza dano de Tri-Karma e bônus da cúpula",
            },
            "yelan": {
                "set": "Selo da Insulação (Emblem)",
                "slot": "Cálice de Dano Hydro ou Tiara Crítica",
                "main": "Bônus de Dano Hydro (ou Taxa/Dano Crítico)",
                "substats": ["Taxa Crítica", "Dano Crítico", "Recarga de Energia", "HP%"],
                "gain": "+20% Dano Coordenado do Supremo",
            },
        }
        default_genshin_cfg = {
            "set": "Set Bis Recomendado",
            "slot": "Cálice Elemental (Slot 4) ou Tiara Crítica (Slot 5)",
            "main": "Bônus Elemental ou Taxa/Dano Crítico",
            "substats": ["Taxa Crítica", "Dano Crítico", "ATK%/HP%", "Recarga"],
            "gain": "+15% a +25% Dano Total do Personagem",
        }

        for cand in top_candidates:
            cfg = _find_craft_cfg(cand["name"], "genshin", meta_craft_genshin, default_genshin_cfg)

            lowest_piece = "Nenhuma relíquia equipada"
            if cand["relics"]:
                lowest_piece = f"Peça atual subótima (Build: {cand['grade']})"

            recommendations.append(
                {
                    "priority_rank": rank_counter,
                    "character_name": cand["name"],
                    "character_icon": cand["icon"],
                    "target_set_name": cfg["set"],
                    "slot_name": cfg["slot"],
                    "slot_icon": "fa-wand-magic-sparkles",
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

    elif g == "hsr":
        # Meta targets no HSR
        meta_craft_hsr = {
            "robin": {
                "set": "Lushaka das Águas Afundadas / Vonwacq",
                "slot": "Corda de Ligação (Slot 6)",
                "main": "Taxa de Recuperação de Energia (ERR)",
                "substats": ["Velocidade (SPD)", "ATK%", "HP%", "RES a Efeito"],
                "gain": "Recarrega o Concerto do Supremo em 1 rotação",
            },
            "sunday": {
                "set": "Lushaka das Águas Afundadas",
                "slot": "Corda de ERR (Slot 6) ou Pés de SPD (Slot 4)",
                "main": "Taxa de Recuperação de Energia (ERR) ou Velocidade",
                "substats": ["Dano Crítico", "Velocidade", "RES a Efeito", "HP%"],
                "gain": "Sincroniza avanço de ação imediato no turno do Hypercarry",
            },
            "ruan mei": {
                "set": "Talia: Reino dos Bandidos / Vonwacq",
                "slot": "Corda de ERR (Slot 6) ou Pés de SPD (Slot 4)",
                "main": "Taxa de Recuperação de Energia ou Velocidade",
                "substats": ["Efeito de Quebra (Break Effect)", "Velocidade", "HP%"],
                "gain": "Alcança 160% de Efeito de Quebra para buff de 68% DMG global",
            },
            "acheron": {
                "set": "Pioneiro Mergulhador no Mar Morto / Izumo Gensei",
                "slot": "Esfera de ATK% / Raio (Slot 5) ou Corpo de Dano Crítico",
                "main": "Dano Crítico (Corpo) ou ATK% (Esfera)",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Velocidade"],
                "gain": "+35% Dano Bruto no Supremo dos Nove Cortes",
            },
            "firefly": {
                "set": "Cavalaria de Ferro dos Flagelos / Kalpagni",
                "slot": "Pés de SPD (Slot 4) ou Esfera de ATK% (Slot 5)",
                "main": "Velocidade (150+ SPD) e ATK%",
                "substats": ["Efeito de Quebra (Break Effect)", "Velocidade", "ATK%"],
                "gain": "Garante 4 ações completas no estado Combustão Completa",
            },
            "feixiao": {
                "set": "Corajoso ao Vento / Duran: Dinastia dos Lobos",
                "slot": "Corpo de Taxa Crítica (Slot 3) ou Esfera de Dano Físico",
                "main": "Taxa Crítica (Corpo) ou Dano Físico (Esfera)",
                "substats": ["Dano Crítico", "Taxa Crítica", "Velocidade", "ATK%"],
                "gain": "Consistência de 95%+ Crítico nos Ataques Extras e Supremo",
            },
            "aventurine": {
                "set": "Palácio dos Cavaleiros da Pureza / Salsotto",
                "slot": "Corpo de DEF% ou Dano Crítico (Slot 3)",
                "main": "DEF% (para 4.000 DEF) ou Dano Crítico",
                "substats": ["DEF%", "Velocidade", "Dano Crítico", "Taxa Crítica"],
                "gain": "Escudo perpétuo de 100% e ativação do buff de 48% Crítico",
            },
        }
        default_hsr_cfg = {
            "set": "Set de Ornamentos Planares Meta",
            "slot": "Corda de Recuperação de Energia (Slot 6) ou Pés de SPD (Slot 4)",
            "main": "Taxa de Recuperação de Energia (ERR) ou Velocidade (SPD)",
            "substats": ["Velocidade", "Taxa Crítica", "Dano Crítico", "HP%/ATK%"],
            "gain": "+20% Eficiência de Ciclos no Caos da Memória (MoC)",
        }

        for cand in top_candidates:
            cfg = _find_craft_cfg(cand["name"], "hsr", meta_craft_hsr, default_hsr_cfg)

            lowest_piece = "Peça atual subótima"
            if cand["relics"]:
                lowest_piece = f"Build Atual: Nota {cand['grade']} ({cand['score']}%)"

            recommendations.append(
                {
                    "priority_rank": rank_counter,
                    "character_name": cand["name"],
                    "character_icon": cand["icon"],
                    "target_set_name": cfg["set"],
                    "slot_name": cfg["slot"],
                    "slot_icon": "fa-cube",
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

    elif g == "zzz":
        # Meta targets no ZZZ
        meta_craft_zzz = {
            "qingyi": {
                "set": "Jazz Eletrizante / Choque Trovejante",
                "slot": "Disco 6 (Impacto %)",
                "main": "Impacto %",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Proficiência de Anomalia"],
                "gain": "Atordoa chefes de Shiyu em menos de 15 segundos",
            },
            "ellen": {
                "set": "Pica-Pau Polar / Metal Polar",
                "slot": "Disco 4 (Taxa/Dano Crítico) ou Disco 5 (Bônus Gelo)",
                "main": "Dano Crítico ou Bônus de Dano de Gelo",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "PEN"],
                "gain": "+30% Dano Crítico nas Tesouradas de Gelo",
            },
            "jane doe": {
                "set": "Presa Furiosa / Jazz da Liberdade",
                "slot": "Disco 4 (Proficiência de Anomalia) ou Disco 5 (Dano Físico)",
                "main": "Proficiência de Anomalia ou Bônus Físico",
                "substats": ["Proficiência de Anomalia", "Taxa de Anomalia", "ATK%"],
                "gain": "Desencadeia Assalto Crítico contínuo de 500k+ dano",
            },
            "caesar": {
                "set": "Protetor da Proto-Faixa / Jazz",
                "slot": "Disco 6 (Impacto %) ou Disco 4 (DEF%)",
                "main": "Impacto % (ou DEF%)",
                "substats": ["DEF%", "HP%", "Impacto", "ATK%"],
                "gain": "Concede +1.000 de ATK instantâneo para todo o time com escudo",
            },
        }
        default_zzz_cfg = {
            "set": "Discos de Música Recomendados",
            "slot": "Disco 6 (Impacto ou Regeneração de Energia)",
            "main": "Impacto % ou Regeneração de Energia",
            "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "PEN"],
            "gain": "+20% Velocidade de Stun ou Dano de Burst",
        }

        for cand in top_candidates:
            cfg = _find_craft_cfg(cand["name"], "zzz", meta_craft_zzz, default_zzz_cfg)

            lowest_piece = f"Build Atual: Nota {cand['grade']}"

            recommendations.append(
                {
                    "priority_rank": rank_counter,
                    "character_name": cand["name"],
                    "character_icon": cand["icon"],
                    "target_set_name": cfg["set"],
                    "slot_name": cfg["slot"],
                    "slot_icon": "fa-compact-disc",
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
        f"💡 **Dica de Ouro:** Guarde sua {item_names.get(g, 'Resina')} para peças de **Recuperação de Energia (ERR)** "
        "ou **Cálices de Bônus Elemental / Discos de Impacto**, pois elas possuem a menor probabilidade matemática de drop natural (~3% a 5%)."
    )

    return {
        "game_id": g,
        "game_name": game_names.get(g, g.upper()),
        "crafting_item_name": item_names.get(g, "Item de Síntese"),
        "crafting_item_icon": item_icons.get(g, "fa-wand-magic-sparkles"),
        "recommendations": recommendations,
        "summary_tip": summary_tip,
    }

