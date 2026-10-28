
ENDGAME_MODE_EN_MAP = {
    "Caos da Memória (MoC)": "Memory of Chaos (MoC)",
    "Caos da Memória": "Memory of Chaos",
    "Ficção Pura": "Pure Fiction",
    "Sombra Apocalíptica": "Apocalyptic Shadow",
    "Abismo Espiral": "Spiral Abyss",
    "Teatro Imaginário": "Imaginarium Theater",
    "Defesa Shiyu (Shiyu Defense)": "Shiyu Defense",
    "Defesa Shiyu": "Shiyu Defense",
    "Investida Fatal": "Deadly Assault",
    "Cavidade Zero": "Hollow Zero",
}
import os
import re
import json
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

import database
from build_calculator import normalize_char_name
from core.config import get_resource_path
from schemas.team_matcher import (
    TeamMemberSubstitute,
    TeamMemberMatch,
    MatchedTeamItem,
    EndgameTeamMatchResponse,
)

_ARCHETYPES_CACHE: Optional[Dict[str, Any]] = None
_MANIFESTS_CACHE: Dict[str, Dict[str, Any]] = {}


def _get_manifest(game_id: str) -> Dict[str, Any]:
    """Carrega o manifesto de entidades de static_data com cache em memória."""
    global _MANIFESTS_CACHE
    g_clean = game_id.lower().strip()
    if g_clean not in _MANIFESTS_CACHE:
        manifest_path = get_resource_path(os.path.join("static_data", f"{g_clean}_manifest.json"))
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    _MANIFESTS_CACHE[g_clean] = json.load(f)
            except Exception as e:
                print(f"[WARN] Erro ao carregar manifesto de {g_clean}: {e}")
                _MANIFESTS_CACHE[g_clean] = {}
        else:
            _MANIFESTS_CACHE[g_clean] = {}
    return _MANIFESTS_CACHE[g_clean]


def load_team_archetypes(game_id: str, force_reload: bool = False) -> List[Dict[str, Any]]:
    """Carrega o catálogo de composições de endgame de static_data/team_archetypes.json."""
    global _ARCHETYPES_CACHE
    g_clean = game_id.lower().strip()
    archetypes_file = get_resource_path(os.path.join("static_data", "team_archetypes.json"))

    if _ARCHETYPES_CACHE is None or force_reload:
        if os.path.exists(archetypes_file):
            try:
                with open(archetypes_file, "r", encoding="utf-8") as f:
                    _ARCHETYPES_CACHE = json.load(f)
            except Exception as e:
                print(f"[WARN] Erro ao carregar team_archetypes.json: {e}")
                _ARCHETYPES_CACHE = {}
        else:
            _ARCHETYPES_CACHE = {}

    return _ARCHETYPES_CACHE.get(g_clean, [])


def categorize_role(role_name: str, path: str = "", specialty: str = "") -> str:
    """Classifica qualquer denominação de papel ou classe em uma das 6 categorias táticas fundamentais."""
    combined = f"{role_name} {path} {specialty}".lower()

    # 1. Sustento / Defesa / Cura / Escudo
    if any(
        k in combined
        for k in [
            "sustento",
            "sustain",
            "cura",
            "healer",
            "escudo",
            "shielder",
            "preservation",
            "preservação",
            "preservacao",
            "abundance",
            "abundância",
            "abundancia",
            "defesa",
            "defense",
        ]
    ):
        return "SUSTAIN"

    # 2. Atordoamento / Quebra (ZZZ e Stunners)
    if any(k in combined for k in ["atordoamento", "stun", "quebra", "daze", "impact"]):
        return "STUNNER"

    # 3. Debuffer / Inexistência / DoT / Shred (checado antes de buffer para evitar colisão)
    if any(
        k in combined
        for k in ["debuffer", "inexistência", "inexistencia", "nihility", "dot", "shred", "res pen", "vulnerabilidade"]
    ):
        return "DEBUFFER"

    # 4. Buffer / Amplificação / Harmonia
    if any(
        k in combined
        for k in ["buffer", "harmonia", "harmony", "amplificação", "amplificacao", "amplifier", "support", "suporte"]
    ):
        return "BUFFER"

    # 5. Sub-DPS / Aplicação Elemental
    if any(k in combined for k in ["sub-dps", "off-field", "aplicação", "aplicacao", "anomalia", "anomaly"]):
        return "SUB_DPS"

    # 6. DPS Principal / Ataque
    return "DPS"


def infer_char_role(game_id: str, char_name: str, char_data: Optional[Dict[str, Any]] = None) -> str:
    """Infere a função de combate do personagem consultando o manifesto estático."""
    g_clean = game_id.lower().strip()
    manifest = _get_manifest(g_clean)
    characters_manifest = manifest.get("characters", {})
    norm_name = normalize_char_name(char_name)

    # Busca nos manifestos
    char_info = None
    for k, v in characters_manifest.items():
        if normalize_char_name(v.get("name", k)) == norm_name or k.lower() == norm_name:
            char_info = v
            break

    path_val = (char_info.get("path") if char_info else "") or ""
    specialty_val = (char_info.get("specialty") if char_info else "") or ""
    role_hint = ""

    if char_data:
        role_hint = char_data.get("role", "") or char_data.get("path", "")

    return categorize_role(role_hint, path=path_val, specialty=specialty_val)


def find_functional_substitutes(
    game_id: str, target_role: str, target_element: str, roster: List[Dict[str, Any]], excluded_names: Set[str], lang: str = "pt"
) -> List[TeamMemberSubstitute]:
    """Varre os personagens que o jogador REALMENTE POSSUI no roster para sugerir substitutos funcionais."""
    g_clean = game_id.lower().strip()
    target_category = categorize_role(target_role)
    candidates = []

    for c in roster:
        c_name = c.get("name", "").strip()
        if not c_name:
            continue

        c_norm = normalize_char_name(c_name)
        if c_norm in excluded_names:
            continue

        c_element = c.get("element", "")
        c_level = c.get("level", 1)
        c_rarity = c.get("rarity", 4)
        c_rank = c.get("rank_str", "C0")
        c_icon = c.get("icon", "")

        c_category = infer_char_role(g_clean, c_name, c)

        # Avalia compatibilidade funcional
        score = 0
        is_compatible = False

        if c_category == target_category:
            is_compatible = True
            score += 60
        elif target_category in ["BUFFER", "DEBUFFER"] and c_category in ["BUFFER", "DEBUFFER"]:
            is_compatible = True
            score += 35
        elif target_category in ["DPS", "SUB_DPS"] and c_category in ["DPS", "SUB_DPS"]:
            is_compatible = True
            score += 40

        if not is_compatible:
            continue

        # Bônus por elemento compartilhado
        if target_element and c_element and target_element.lower() == c_element.lower():
            score += 15

        # Ponderação por preparo real da conta (nível e raridade)
        score += min(c_level, 90) * 0.3
        if str(c_rarity).startswith("5"):
            score += 5

        # Elabora justificativa funcional
        if lang == "en":
            reason = f"Same tactical role ({target_category.capitalize()})"
            if target_element and c_element and target_element.lower() == c_element.lower():
                reason += f" and same element ({c_element})"
            if c_level >= 70:
                reason += f" • Lv. {c_level} battle-ready"
        else:
            reason = f"Mesmo papel tático ({target_category.capitalize()})"
            if target_element and c_element and target_element.lower() == c_element.lower():
                reason += f" e mesmo elemento ({c_element})"
            if c_level >= 70:
                reason += f" • Nv. {c_level} já preparado"

        candidates.append(
            (
                score,
                TeamMemberSubstitute(
                    name=c_name,
                    role=c_category,
                    element=c_element,
                    level=c_level,
                    rarity=5 if str(c_rarity).startswith("5") else 4,
                    rank_str=c_rank,
                    icon=c_icon,
                    synergy_reason=reason,
                ),
            )
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [sub for _, sub in candidates[:3]]


def calculate_readiness_score(matched_members: List[TeamMemberMatch], max_level: int = 80) -> float:
    """Calcula score de prontidão ponderado da equipe baseado nos personagens possuídos."""
    owned = [m for m in matched_members if m.is_owned]
    if not owned:
        return 0.0

    total_score = 0.0
    for m in owned:
        lvl = m.level or 1
        pct = min(lvl / max_level, 1.0) * 100.0
        total_score += pct

    # Média entre os membros possuídos, penalizada proporcionalmente caso faltem membros
    avg_owned_score = total_score / len(matched_members)
    return round(avg_owned_score, 1)


def match_endgame_teams(
    game_id: str, uid: Optional[str] = None, mode: Optional[str] = None, min_match: float = 0.0, lang: str = "pt"
) -> EndgameTeamMatchResponse:
    """
    Cruza as equipes de referência de endgame com o roster real do jogador.
    Calcula percentual de compatibilidade, membros possuídos e substitutos disponíveis no roster.
    """
    g_clean = (game_id or "hsr").lower().strip()
    if g_clean not in ["hsr", "genshin", "zzz"]:
        raise ValueError("Jogo inválido. Escolha 'hsr', 'genshin' ou 'zzz'.")

    target_uid = uid or database.get_active_uid(g_clean)
    roster_data = database.get_roster_data(g_clean, uid=target_uid)

    # Mapa normalizado de personagens possuídos
    owned_map: Dict[str, Dict[str, Any]] = {}
    for c in roster_data:
        c_name = c.get("name", "").strip()
        if c_name:
            norm = normalize_char_name(c_name)
            owned_map[norm] = c
            owned_map[c_name.lower()] = c

    archetypes = load_team_archetypes(g_clean)
    available_modes = sorted(list(set(t.get("mode", "") for t in archetypes if t.get("mode"))))

    matched_teams: List[MatchedTeamItem] = []
    ready_count = 0
    max_lvl = 90 if g_clean == "genshin" else (80 if g_clean == "hsr" else 60)

    for t_arch in archetypes:
        t_mode = t_arch.get("mode", "")
        if mode and mode.lower() not in t_mode.lower():
            continue

        raw_members = t_arch.get("members", [])
        total_members_count = len(raw_members)
        if total_members_count == 0:
            continue

        matched_members: List[TeamMemberMatch] = []
        owned_count = 0
        excluded_names: Set[str] = set()

        # 1. Primeiro passo: identifica os membros possuídos da composição
        for m in raw_members:
            m_name = m.get("name", "").strip()
            m_norm = normalize_char_name(m_name)
            m_lower = m_name.lower()

            user_char = owned_map.get(m_norm) or owned_map.get(m_lower)
            if user_char:
                owned_count += 1
                excluded_names.add(m_norm)
                matched_members.append(
                    TeamMemberMatch(
                        name=m_name,
                        role=m.get("role", "DPS"),
                        element=user_char.get("element") or m.get("element", ""),
                        is_owned=True,
                        level=user_char.get("level", 1),
                        rarity=5 if str(user_char.get("rarity", "")).startswith("5") else 4,
                        rank_str=user_char.get("rank_str", "C0"),
                        icon=user_char.get("icon", ""),
                        substitutes=[],
                    )
                )
            else:
                matched_members.append(
                    TeamMemberMatch(
                        name=m_name,
                        role=m.get("role", "DPS"),
                        element=m.get("element", ""),
                        is_owned=False,
                        level=None,
                        rarity=None,
                        rank_str=None,
                        icon=None,
                        substitutes=[],
                    )
                )

        # 2. Segundo passo: busca substitutos no roster para os faltantes
        for m_item in matched_members:
            if not m_item.is_owned:
                subs = find_functional_substitutes(
                    game_id=g_clean,
                    target_role=m_item.role,
                    target_element=m_item.element or "",
                    roster=roster_data,
                    excluded_names=excluded_names,
                    lang=lang,
                )
                m_item.substitutes = subs
                # Evita reutilizar o mesmo substituto sugerido em outro slot faltante da mesma equipe
                if subs:
                    excluded_names.add(normalize_char_name(subs[0].name))

        match_pct = round((owned_count / total_members_count) * 100.0, 1)
        if match_pct < min_match:
            continue

        readiness = calculate_readiness_score(matched_members, max_level=max_lvl)

        # Considera pronto se tem 100% de posse ou se faltar apenas 1 membro e houver substituto viável
        is_ready = (owned_count == total_members_count) or (
            owned_count >= (total_members_count - 1)
            and all(len(m.substitutes) > 0 for m in matched_members if not m.is_owned)
        )
        if owned_count == total_members_count:
            ready_count += 1

        matched_teams.append(
            MatchedTeamItem(
                team_id=t_arch.get("team_id", f"{g_clean}_{len(matched_teams)}"),
                team_name=t_arch.get("team_name", "Composição Metagame"),
                game_id=g_clean,
                mode=ENDGAME_MODE_EN_MAP.get(t_mode, t_mode) if lang == "en" else t_mode,
                tier_or_rank=t_arch.get("tier_or_rank", ""),
                avg_performance=t_arch.get("avg_performance", ""),
                usage_rate=t_arch.get("usage_rate", ""),
                match_percentage=match_pct,
                owned_count=owned_count,
                total_count=total_members_count,
                is_ready=is_ready,
                readiness_score=readiness,
                members=matched_members,
                synergy_notes=t_arch.get("synergy_notes", ""),
                recommended_buffs_bosses=t_arch.get("recommended_buffs_bosses", ""),
            )
        )

    # Ordena: 100% primeiro, depois por match_percentage decrescente e readiness_score
    matched_teams.sort(key=lambda t: (t.match_percentage, t.readiness_score), reverse=True)

    return EndgameTeamMatchResponse(
        status="success",
        game_id=g_clean,
        uid=target_uid,
        mode_filter=mode,
        total_teams=len(matched_teams),
        ready_teams_count=ready_count,
        teams=matched_teams,
        available_modes=[ENDGAME_MODE_EN_MAP.get(m, m) for m in available_modes] if lang == "en" else available_modes,
    )
