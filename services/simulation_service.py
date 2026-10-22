import re
from typing import Dict, List, Tuple, Optional, Any, Union
import database
from build_calculator import score_relic, normalize_slot_name, calculate_stat_breakpoints, get_meta_data
from schemas.simulation import RelicPieceModel, SimulateSwapRequest, SimulateSwapResponse, SimulatedStatDiff

RE_NUM = re.compile(r"([0-9]+(?:\.[0-9]+)?)")


def parse_stat_line(line: str) -> Tuple[Optional[str], float]:
    """Extrai a chave normalizada e o valor numérico de uma linha de status."""
    if not line:
        return None, 0.0
    s = line.lower().strip()
    m = RE_NUM.search(s)
    if not m:
        return None, 0.0
    val = float(m.group(1))

    if any(k in s for k in ["taxa crit", "crit rate", "taxa crítica", "crit_rate"]):
        return "crit_rate", val
    if any(k in s for k in ["dano crit", "crit dmg", "dano crítico", "crit_dmg"]):
        return "crit_dmg", val
    if any(k in s for k in ["vel", "spd", "speed", "velocidade"]):
        return "speed", val
    if any(k in s for k in ["recarga", "energy recharge", "er", "err"]):
        return "er", val
    if any(k in s for k in ["acerto de efeito", "ehr", "effect hit rate"]):
        return "ehr", val
    if any(k in s for k in ["proficiência", "anomaly prof", "ap"]):
        return "ap", val
    if any(k in s for k in ["atk%", "ataque%", "atk %"]):
        return "atk_pct", val
    if any(k in s for k in ["hp%", "vida%", "hp %"]):
        return "hp_pct", val
    if any(k in s for k in ["def%", "defesa%", "def %"]):
        return "def_pct", val
    if "atk" in s or "ataque" in s:
        return "atk_flat", val
    if "hp" in s or "vida" in s:
        return "hp_flat", val
    if "def" in s or "defesa" in s:
        return "def_flat", val

    return None, 0.0


def extract_stats_from_relic(main_stat: str, sub_stats: Union[str, List[Any]]) -> Dict[str, float]:
    """Mapeia os atributos numéricos contidos no Main Stat e Substatus de uma peça."""
    stats: Dict[str, float] = {}

    # 1. Main Stat
    if main_stat:
        k, v = parse_stat_line(main_stat)
        if k:
            stats[k] = stats.get(k, 0.0) + v

    # 2. Substats
    if isinstance(sub_stats, list):
        for item in sub_stats:
            line_str = ""
            if isinstance(item, dict):
                line_str = f"{item.get('name', '')} {item.get('val', '')}"
            else:
                line_str = str(item)
            k, v = parse_stat_line(line_str)
            if k:
                stats[k] = stats.get(k, 0.0) + v
    elif isinstance(sub_stats, str):
        for part in sub_stats.split(","):
            part_clean = part.strip()
            if part_clean:
                k, v = parse_stat_line(part_clean)
                if k:
                    stats[k] = stats.get(k, 0.0) + v

    return stats


def format_substats_to_str(sub_stats: Union[str, List[Any]]) -> str:
    """Padroniza a lista de substatus para string separada por vírgula."""
    if isinstance(sub_stats, list):
        parts = []
        for s in sub_stats:
            if isinstance(s, dict):
                parts.append(f"{s.get('name', '')}: {s.get('val', '')}")
            else:
                parts.append(str(s))
        return ", ".join(parts)
    return str(sub_stats or "")


def map_score_to_grade(score: float) -> str:
    """Mapeia uma pontuação percentual (0..100) para nota de SSS a D."""
    if score >= 90.0:
        return "SS"
    if score >= 80.0:
        return "S+"
    if score >= 70.0:
        return "S"
    if score >= 60.0:
        return "A"
    if score >= 50.0:
        return "B"
    if score >= 40.0:
        return "C"
    return "D"


def simulate_relic_swap(req: SimulateSwapRequest) -> SimulateSwapResponse:
    """
    Simula a substituição de uma relíquia equipada por uma peça nova/candidata e calcula:
    - Delta de pontuação da peça e da build inteira.
    - Delta de atributos numéricos (CR, CD, VEL, ER, AP, etc.).
    - Alterações de Breakpoints vitais e recomendações.
    """
    game_clean = (req.game_id or "hsr").lower().strip()
    char_name = req.char_name.strip()
    target_slot_norm = normalize_slot_name(req.target_slot, game_clean)

    # 1. Recupera as relíquias atuais se não enviadas na requisição
    current_relics = req.current_relics
    if current_relics is None:
        roster = database.get_roster_data(game_clean)
        char_obj = next((c for c in roster if c.get("name", "").lower() == char_name.lower()), None)
        if char_obj and char_obj.get("relics"):
            current_relics = [
                RelicPieceModel(
                    slot=r.get("slot", ""),
                    name=r.get("name", "Relíquia"),
                    main_stat=r.get("main", r.get("main_stat", "")),
                    sub_stats=r.get("sub", r.get("sub_stats", "")),
                    icon=r.get("icon", ""),
                )
                for r in char_obj["relics"]
            ]
        else:
            current_relics = []

    # 2. Localiza a peça antiga no slot alvo
    old_piece: Optional[RelicPieceModel] = None
    other_pieces: List[RelicPieceModel] = []

    for r in current_relics:
        if normalize_slot_name(r.slot, game_clean) == target_slot_norm and old_piece is None:
            old_piece = r
        else:
            other_pieces.append(r)

    # Se a peça antiga não existia, cria uma peça neutra vazia
    if not old_piece:
        old_piece = RelicPieceModel(slot=req.target_slot, name="Vazio", main_stat="", sub_stats="")

    # 3. Avalia a Peça Antiga
    old_sub_str = format_substats_to_str(old_piece.sub_stats)
    old_piece_grade, old_piece_score = score_relic(
        game_clean, char_name, target_slot_norm, old_piece.main_stat, old_sub_str
    )

    # 4. Avalia a Nova Peça Candidata
    new_sub_str = format_substats_to_str(req.replacement_relic.sub_stats)
    new_piece_grade, new_piece_score = score_relic(
        game_clean, char_name, target_slot_norm, req.replacement_relic.main_stat, new_sub_str
    )

    # 5. Avalia todas as outras peças para compor o score total da build antes e depois
    all_old_scores = [old_piece_score]
    all_new_scores = [new_piece_score]

    for p in other_pieces:
        p_slot_norm = normalize_slot_name(p.slot, game_clean)
        p_sub_str = format_substats_to_str(p.sub_stats)
        _, p_score = score_relic(game_clean, char_name, p_slot_norm, p.main_stat, p_sub_str)
        all_old_scores.append(p_score)
        all_new_scores.append(p_score)

    old_build_score = round(sum(all_old_scores) / max(len(all_old_scores), 1), 1)
    new_build_score = round(sum(all_new_scores) / max(len(all_new_scores), 1), 1)
    score_diff = round(new_build_score - old_build_score, 1)

    old_build_grade = map_score_to_grade(old_build_score)
    new_build_grade = map_score_to_grade(new_build_score)
    grade_changed = old_build_grade != new_build_grade
    is_upgrade = score_diff > 0

    # 6. Cálculo das variações de atributos numéricos (Stat Diffs)
    old_piece_stats = extract_stats_from_relic(old_piece.main_stat, old_piece.sub_stats)
    new_piece_stats = extract_stats_from_relic(req.replacement_relic.main_stat, req.replacement_relic.sub_stats)

    all_stat_keys = set(old_piece_stats.keys()).union(set(new_piece_stats.keys()))
    stat_display_names = {
        "speed": "VEL",
        "crit_rate": "Taxa CRIT",
        "crit_dmg": "Dano CRIT",
        "er": "Recarga de Energia",
        "ehr": "Acerto de Efeito",
        "ap": "Proficiência (AP)",
        "atk_pct": "ATK%",
        "hp_pct": "HP%",
        "def_pct": "DEF%",
        "atk_flat": "ATK",
        "hp_flat": "HP",
        "def_flat": "DEF",
    }

    stat_diffs: List[SimulatedStatDiff] = []
    simulated_final_stats = dict(req.current_stats or {})

    for k in sorted(all_stat_keys):
        o_val = old_piece_stats.get(k, 0.0)
        n_val = new_piece_stats.get(k, 0.0)
        delta = round(n_val - o_val, 1)

        # Atualiza nos status finais simulados
        curr_val = 0.0
        if k in simulated_final_stats:
            try:
                curr_val = float(simulated_final_stats[k])
            except (ValueError, TypeError):
                curr_val = 0.0

        simulated_final_stats[k] = round(curr_val + delta, 1)

        sign = "+" if delta > 0 else ""
        unit = "%" if any(u in k for u in ["pct", "crit", "er", "ehr"]) else ""
        formatted = f"{sign}{delta}{unit}"

        stat_diffs.append(
            SimulatedStatDiff(
                stat_name=stat_display_names.get(k, k.upper()),
                old_val=o_val,
                new_val=n_val,
                diff=delta,
                formatted_diff=formatted,
            )
        )

    # 7. Avalia Breakpoints com os novos atributos simulados
    breakpoint_feedback = []
    if simulated_final_stats:
        bp_res = calculate_stat_breakpoints(game_clean, char_name, simulated_final_stats)
        if "cycles_summary" in bp_res and bp_res["cycles_summary"]:
            breakpoint_feedback.append(f"⚡ {bp_res['cycles_summary']}")

        for bp in bp_res.get("breakpoints", []):
            reached = bp.get("is_reached") or bp.get("achieved")
            stat_label = bp.get("stat", "")
            desc = bp.get("status") or bp.get("feedback") or ""
            tip = f" — {bp['speed_tuning_tip']}" if bp.get("speed_tuning_tip") else ""
            if reached:
                breakpoint_feedback.append(f"✓ {stat_label}: {desc}{tip}")
            else:
                next_goal = f" ({bp.get('next_goal')})" if bp.get("next_goal") else ""
                breakpoint_feedback.append(f"✗ {stat_label}: {desc}{next_goal}")

    # 8. Veredito Executivo do Simulador
    if score_diff > 2.0:
        verdict = (
            f"Recomendado! A troca eleva o score da build em +{score_diff}% ({old_build_grade} ➔ {new_build_grade})."
        )
    elif score_diff > 0:
        verdict = f"Upgrade sutil (+{score_diff}%). Melhora pontual sem alteração drástica de tier."
    elif score_diff == 0:
        verdict = "Efeito neutro. As duas peças oferecem equilíbrio de atributos similar para o personagem."
    elif score_diff > -3.0:
        verdict = f"Leve redução de score ({score_diff}%). Verifique se o ganho de atributos secundários compensa."
    else:
        verdict = f"Não recomendado! A peça candidata reduz o score da build em {score_diff}% ({old_build_grade} ➔ {new_build_grade})."

    return SimulateSwapResponse(
        character_name=char_name,
        game_id=game_clean,
        target_slot=target_slot_norm,
        old_piece_score=old_piece_score,
        old_piece_grade=old_piece_grade,
        new_piece_score=new_piece_score,
        new_piece_grade=new_piece_grade,
        old_build_score=old_build_score,
        old_build_grade=old_build_grade,
        new_build_score=new_build_score,
        new_build_grade=new_build_grade,
        score_diff=score_diff,
        grade_changed=grade_changed,
        is_upgrade=is_upgrade,
        stat_diffs=stat_diffs,
        breakpoint_feedback=breakpoint_feedback,
        verdict_summary=verdict,
    )
