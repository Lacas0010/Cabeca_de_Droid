"""Cálculo determinístico de breakpoints de combate (CRIT 1:2, SPD/AV, Recarga, Anomalia).

Lê metas específicas de cada personagem dinamicamente a partir de `static_data/character_benchmarks.json`,
dos guias consolidados (`meta_comparator.parse_meta_target`) e dos manifestos de `static_data/`.
"""

import json
import os
import unicodedata
from typing import Any, Dict, Optional, Tuple

from calculators.benchmark_radar import parse_stat_number
from core.paths import get_data_path, get_resource_path

_BENCHMARKS_CACHE: Optional[Dict[str, Any]] = None


def _norm_key(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("utf-8").lower()
    return "".join(ch for ch in s if ch.isalnum())


def _load_benchmarks_json() -> Dict[str, Any]:
    global _BENCHMARKS_CACHE
    if _BENCHMARKS_CACHE is None:
        rel = os.path.join("static_data", "character_benchmarks.json")
        loaded: Dict[str, Any] = {}
        for p in (get_data_path(rel), get_resource_path(rel)):
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        loaded = data
                        break
                except Exception:
                    continue
        _BENCHMARKS_CACHE = loaded
    return _BENCHMARKS_CACHE


def _get_dynamic_char_context(game_id: str, char_name: str) -> Tuple[Dict[str, str], Dict[str, Any], Dict[str, Any]]:
    """Retorna (benchmarks_dict, manifest_profile, guide_target) a partir de static_data/ e guias."""
    g = (game_id or "hsr").lower().strip()
    benchmarks: Dict[str, str] = {}
    profile: Dict[str, Any] = {}
    guide_target: Dict[str, Any] = {}

    slug = ""
    try:
        from meta_comparator import resolve_character_canonical_slug

        slug = resolve_character_canonical_slug(g, char_name) or ""
    except Exception:
        slug = ""

    # 1. Manifesto de static_data/{game}_manifest.json
    try:
        from static_data_manager import static_data_manager

        profile = static_data_manager.get_character_profile(g, char_name) or {}
        if not profile and slug:
            profile = static_data_manager.get_character_profile(g, slug) or {}
    except Exception:
        profile = {}

    # 2. Benchmarks de static_data/character_benchmarks.json
    bm_game = _load_benchmarks_json().get(g) or {}
    if isinstance(bm_game, dict):
        candidates = [
            slug,
            char_name.lower().strip().replace(" ", "_"),
            _norm_key(char_name),
            _norm_key(slug),
            _norm_key(profile.get("name", "")),
        ]
        norm_lookup = {_norm_key(k): v for k, v in bm_game.items() if isinstance(v, dict)}
        for cand in candidates:
            if not cand:
                continue
            if cand in bm_game and isinstance(bm_game[cand], dict):
                benchmarks = dict(bm_game[cand])
                break
            nk = _norm_key(cand)
            if nk in norm_lookup:
                benchmarks = dict(norm_lookup[nk])
                break

    # 3. Guia raspado local (quando disponível, complementa armas/sets/benchmarks)
    try:
        from meta_comparator import find_best_guide_file, parse_meta_target

        if find_best_guide_file(g, char_name):
            parsed = parse_meta_target(g, char_name)
            if isinstance(parsed, dict):
                guide_target = parsed
                for bk, bv in (parsed.get("benchmarks") or {}).items():
                    if bk not in benchmarks and bv:
                        benchmarks[bk] = str(bv)
    except Exception:
        guide_target = {}

    return benchmarks, profile, guide_target


def _extract_benchmark_target(benchmarks: Dict[str, str], key_fragments: Tuple[str, ...]) -> Tuple[Optional[float], str]:
    """Busca o valor numérico alvo de um atributo nos benchmarks carregados."""
    for bk, bv in (benchmarks or {}).items():
        bk_norm = _norm_key(bk)
        if any(frag in bk_norm for frag in key_fragments):
            val = parse_stat_number(bv)
            if val is not None and val > 0:
                return float(val), str(bv)
    return None, ""


def calculate_stat_breakpoints(game_id: str, char_name: str, stats: dict) -> dict:
    """
    Avalia se os status atuais de um personagem atingiram os limiares (breakpoints) de combate,
    incluindo Speed Tuning e Action Value por ciclos de MoC/PF/Endgame.
    """
    game_id = (game_id or "hsr").lower().strip()
    breakpoints = []
    benchmarks, profile, guide_target = _get_dynamic_char_context(game_id, char_name)

    def _parse_val(k_list, default=0.0):
        for k in k_list:
            if k in stats and stats[k] is not None:
                parsed = parse_stat_number(stats[k])
                if parsed is not None:
                    return float(parsed)
        return default

    speed = _parse_val(["speed", "spd", "velocidade"])
    ehr = _parse_val(["ehr", "effect_hit_rate", "taxa_acerto_efeito"])
    er = _parse_val(["er", "err", "energy_recharge", "recarga_energia", "recarga"])
    crit_rate = _parse_val(["crit_rate", "crit_pct", "taxa_critica", "taxa_crit"])
    crit_dmg = _parse_val(["crit_dmg", "crit_dmg_pct", "dano_critico", "dano_crit"])
    impact = _parse_val(["impact", "impacto"])
    ap = _parse_val(["anomaly_prof", "anomaly_proficiency", "proficiencia_anomalia", "ap"])

    speed_av = round(10000.0 / speed, 1) if speed > 0 else None
    cycles_summary = None

    if game_id == "hsr":
        path_lower = str(profile.get("path") or "").lower()
        target_spd, raw_spd_str = _extract_benchmark_target(benchmarks, ("vel", "spd", "speed"))
        guide_sets_str = " ".join(
            str(s).lower() for s in ((guide_target.get("sets") or []) + (guide_target.get("all_sets") or []))
        )

        if speed > 0:
            spd_tiers = [
                (120.0, "120.0 SPD", "Ativa Planares (Frota, Penacony, Vonwacq)"),
                (134.0, "134.0 SPD", "2 ações no Ciclo 0 (150 AV) do MoC"),
                (142.9, "143.0 SPD", "5 ações nos 3 primeiros ciclos"),
                (160.1, "160.1 SPD", "4 ações em 2 ciclos (suportes hyperspeed)"),
                (200.0, "200.0 SPD", "2 ações por ciclo (50 AV)"),
            ]

            reached_tier_desc = "Abaixo de 120 SPD (base)"
            next_goal_desc = "Breakpoint máximo atingido"
            is_reached = speed >= 134.0
            tier_prog = 0.0

            for idx, (val, title, desc) in enumerate(spd_tiers):
                if speed >= val:
                    reached_tier_desc = f"{title}: {desc}"
                elif next_goal_desc == "Breakpoint máximo atingido":
                    diff = val - speed
                    next_goal_desc = f"+{diff:.1f} SPD para {title} ({desc})"
                    prev_val = spd_tiers[idx - 1][0] if idx > 0 else 100.0
                    tier_prog = min(100.0, max(0.0, round(((speed - prev_val) / (val - prev_val)) * 100.0, 1)))

            # Dica de Speed Tuning derivada dinamicamente do caminho, benchmark de SPD e sets do guia
            has_cd_bm = _extract_benchmark_target(benchmarks, ("danocrit", "critdmg"))[0] is not None
            raw_spd_lower = raw_spd_str.lower()
            tuning_tip = "DPS padrão: 134.0 SPD fecha 2 ações no Ciclo 0. Buffers/debuffers devem agir antes do carry."
            if (target_spd is not None and target_spd >= 160.0) or "160" in raw_spd_lower:
                tuning_tip = "Hyperspeed (160.1+ SPD): libera Bota de ATQ% no DPS sem perder turnos."
            elif "slower" in raw_spd_lower or "-1" in raw_spd_lower or (
                "harmony" in path_lower and has_cd_bm and target_spd is not None and 130.0 <= target_spd <= 140.0
            ):
                tuning_tip = "Setup -1 SPD: deixe 1–2 SPD abaixo do carry para dobrar turnos logo após o DPS."
            elif ("vonwacq" in guide_sets_str) or (
                "harmony" in path_lower and target_spd is not None and 118.0 <= target_spd <= 126.0
            ):
                tuning_tip = "120–125 SPD + Vonwacq para puxar o primeiro turno e abrir o buff de equipe cedo."

            turnos_ciclo0 = 2 if speed >= 134.0 else 1
            if speed >= 200.0:
                turnos_ciclo0 = 3
            cycles_summary = f"{speed_av} AV/turno • Ciclo 0: {turnos_ciclo0} ação(ões) • 134 SPD: {'OK' if speed >= 134.0 else 'Falta'}"

            breakpoints.append(
                {
                    "stat": "Velocidade & Ciclos MoC (SPD)",
                    "current": f"{speed:.1f} SPD ({speed_av} AV)",
                    "status": reached_tier_desc,
                    "next_goal": next_goal_desc,
                    "is_reached": is_reached,
                    "tier_progress": tier_prog if not (speed >= 200.0) else 100.0,
                    "action_value": speed_av,
                    "category": "speed",
                    "speed_tuning_tip": tuning_tip,
                }
            )

        # Check EHR derivado de static_data/character_benchmarks.json e Caminho (Nihility)
        bm_ehr, _ = _extract_benchmark_target(benchmarks, ("acertodeefeito", "effecthit", "ehr"))
        if ehr > 0 or bm_ehr is not None or "nihility" in path_lower:
            target_ehr = bm_ehr if bm_ehr is not None else 67.0
            is_ehr_ok = ehr >= target_ehr
            status_ehr = (
                f"Cap fechado contra chefes Lv. 95 (meta: {target_ehr:.0f}%)"
                if is_ehr_ok
                else f"Abaixo do cap de debuff (meta: {target_ehr:.0f}%)"
            )
            breakpoints.append(
                {
                    "stat": "Efetividade de Acerto (EHR)",
                    "current": f"{ehr:.1f}%",
                    "status": status_ehr,
                    "next_goal": f"+{max(0.0, target_ehr - ehr):.1f}% EHR"
                    if not is_ehr_ok
                    else "Cap atingido",
                    "is_reached": is_ehr_ok,
                    "tier_progress": min(100.0, round((ehr / target_ehr) * 100.0, 1)) if target_ehr > 0 else 100.0,
                    "category": "debuff",
                    "speed_tuning_tip": "Sem o cap de EHR, debuffs podem falhar em chefes com 40% Effect RES.",
                }
            )

    elif game_id == "genshin":
        # Recarga de Energia (ER) lida dinamicamente de character_benchmarks.json / guia do personagem
        bm_er, _ = _extract_benchmark_target(benchmarks, ("recargadeenergia", "energyrecharge", "recarga", "er"))
        target_er = bm_er if bm_er is not None else 160.0

        is_er_ok = er >= target_er
        status_er = (
            f"Ult pronto por rotação de 20s (meta: {target_er:.0f}%)"
            if is_er_ok
            else f"ER curto para fechar a rotação (meta: {target_er:.0f}%)"
        )
        breakpoints.append(
            {
                "stat": "Recarga de Energia (ER)",
                "current": f"{er:.1f}%",
                "status": status_er,
                "next_goal": f"+{max(0.0, target_er - er):.1f}% ER"
                if not is_er_ok
                else "ER fechado",
                "is_reached": is_er_ok,
                "tier_progress": min(100.0, round((er / target_er) * 100.0, 1)) if target_er > 0 else 100.0,
                "category": "energy",
                "speed_tuning_tip": "Falta de ER estende a rotação e derruba mais DPS que perder rolls de CRIT.",
            }
        )

        # Checagem de Favonius baseada dinamicamente nas armas recomendadas do guia ou suporte de alta ER (>=180%)
        guide_weapons_str = " ".join(
            str(w).lower() for w in ((guide_target.get("weapons") or []) + (guide_target.get("all_weapons") or []))
        )
        recommends_favonius = "favonius" in guide_weapons_str
        is_high_er_support = target_er >= 180.0 and _extract_benchmark_target(benchmarks, ("danocrit", "critdmg"))[0] is None
        if 0 < crit_rate < 40.0 and (recommends_favonius or is_high_er_support):
            breakpoints.append(
                {
                    "stat": "Proc de Favonius",
                    "current": f"{crit_rate:.1f}% Taxa CRIT",
                    "status": "Taxa CRIT baixa para procar Favonius (alvo: 40–50%)",
                    "next_goal": f"+{40.0 - crit_rate:.1f}% Taxa CRIT para proc estável",
                    "is_reached": False,
                    "tier_progress": min(100.0, round((crit_rate / 40.0) * 100.0, 1)),
                    "category": "energy",
                    "speed_tuning_tip": "Favonius só proca em CRIT em campo.",
                }
            )

    elif game_id == "zzz":
        spec_lower = str(profile.get("specialty") or "").lower()
        bm_ap, _ = _extract_benchmark_target(benchmarks, ("proficienciadeanomalia", "proficienciaemanomalia", "anomalyprof"))
        if ap > 0 or bm_ap is not None or "anomaly" in spec_lower:
            target_ap = bm_ap if bm_ap is not None else 300.0
            is_ap_ok = ap >= target_ap
            breakpoints.append(
                {
                    "stat": "Proficiência em Anomalia (AP)",
                    "current": f"{ap:.0f} AP",
                    "status": f"Cap de Anomalia atingido (meta: {target_ap:.0f} AP)"
                    if is_ap_ok
                    else f"Abaixo do cap de Anomalia (meta: {target_ap:.0f} AP)",
                    "next_goal": f"+{max(0.0, target_ap - ap):.0f} AP"
                    if not is_ap_ok
                    else "Cap fechado",
                    "is_reached": is_ap_ok,
                    "tier_progress": min(100.0, round((ap / target_ap) * 100.0, 1)) if target_ap > 0 else 100.0,
                    "category": "anomaly",
                    "speed_tuning_tip": f"Feche {target_ap:.0f} AP para maximizar dano de Anomalia/Desordem.",
                }
            )

        bm_imp, _ = _extract_benchmark_target(benchmarks, ("impacto", "impact"))
        if impact > 0 or bm_imp is not None or "stun" in spec_lower:
            target_imp = min(bm_imp, 140.0) if bm_imp is not None else 130.0
            is_imp_ok = impact >= target_imp
            breakpoints.append(
                {
                    "stat": "Impacto (Stun)",
                    "current": f"{impact:.0f} Impacto",
                    "status": "Impacto no padrão de stunner"
                    if is_imp_ok
                    else "Impacto baixo — falta Disco 6 de Impacto%",
                    "next_goal": "Trocar Disco 6 para Impacto%" if not is_imp_ok else "Impacto OK",
                    "is_reached": is_imp_ok,
                    "tier_progress": min(100.0, round((impact / max(target_imp, 1.0)) * 100.0, 1)) if impact > 0 else 50.0,
                    "category": "impact",
                    "speed_tuning_tip": "Disco 6 de Impacto% acelera a janela de Stun e Chain Attack.",
                }
            )

    # Proporção Crítica 1:2 Universal
    if crit_rate > 0 and crit_dmg > 0:
        ratio = round(crit_dmg / max(1.0, crit_rate), 2)
        is_ratio_ok = 1.7 <= ratio <= 2.3
        status_crit = (
            f"Proporção 1:{ratio} (dentro da faixa 1:2)"
            if is_ratio_ok
            else f"Proporção 1:{ratio} (fora da faixa 1:2)"
        )
        goal_crit = (
            "CRIT equilibrado"
            if is_ratio_ok
            else ("Falta Taxa CRIT" if ratio > 2.3 else "Falta Dano CRIT")
        )
        breakpoints.append(
            {
                "stat": "Proporção CRIT (1:2)",
                "current": f"{crit_rate:.1f}% CR / {crit_dmg:.1f}% CD",
                "status": status_crit,
                "next_goal": goal_crit,
                "is_reached": is_ratio_ok,
                "tier_progress": 100.0 if is_ratio_ok else 65.0,
                "category": "crit",
                "speed_tuning_tip": "Priorize fechar 1:2 considerando buffs de CRIT em combate (sets/passivas).",
            }
        )

    return {
        "char_name": char_name,
        "game_id": game_id,
        "speed_action_value": speed_av,
        "cycles_summary": cycles_summary,
        "breakpoints": breakpoints,
    }

