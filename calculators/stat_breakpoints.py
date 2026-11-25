"""Cálculo determinístico de breakpoints de combate (CRIT 1:2, SPD/AV, Recarga, Anomalia)."""

from calculators.benchmark_radar import parse_stat_number


def calculate_stat_breakpoints(game_id: str, char_name: str, stats: dict) -> dict:
    """
    Avalia se os status atuais de um personagem atingiram os limiares (breakpoints) vitais de combate,
    incluindo Speed Tuning e Action Value por ciclos de MoC/PF/Endgame.
    """
    game_id = (game_id or "hsr").lower().strip()
    char_lower = (char_name or "").lower().strip()
    breakpoints = []

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
        if speed > 0:
            spd_tiers = [
                (120.0, "120.0 SPD", "Ativação de Orbes Planares (Frota dos Eternos, Penacony, Vonwacq)"),
                (134.0, "134.0 SPD", "2 Ações no Ciclo 0 (150 AV) do MoC / Pura Ficção"),
                (142.9, "143.0 SPD", "5 Ações nos Primeiros 3 Ciclos"),
                (160.1, "160.1 SPD", "4 Ações em 2 Ciclos (Tier Supremo: Sparkle, Ruan Mei, Robin)"),
                (200.0, "200.0 SPD", "2 Ações por Ciclo garantidas (50 AV)"),
            ]

            reached_tier_desc = "Abaixo de 120 (Sem turnos extras)"
            next_goal_desc = "Breakpoint Máximo atingido!"
            is_reached = speed >= 134.0
            tier_prog = 0.0

            for idx, (val, title, desc) in enumerate(spd_tiers):
                if speed >= val:
                    reached_tier_desc = f"{title}: {desc}"
                elif next_goal_desc == "Breakpoint Máximo atingido!":
                    diff = val - speed
                    next_goal_desc = f"Faltam {diff:.1f} de VEL para atingir {title} ({desc})"
                    prev_val = spd_tiers[idx - 1][0] if idx > 0 else 100.0
                    tier_prog = min(100.0, max(0.0, round(((speed - prev_val) / (val - prev_val)) * 100.0, 1)))

            # Dica de Speed Tuning personalizada
            tuning_tip = "Para DPS padrão, atingir 134.0 SPD garante 2 turnos no ciclo 0. Suportes de buffer/debuff devem idealmente agir antes do DPS."
            if "bronya" in char_lower or "sunday" in char_lower:
                tuning_tip = "Speed Tuning -1 SPD: Mantenha a velocidade de 1 a 2 pontos logo ABAIXO do seu DPS para agir imediatamente após ele e conceder turno duplo instantâneo."
            elif "sparkle" in char_lower or "hanabi" in char_lower:
                tuning_tip = "Hyper-Speed Tuning (160.1+ SPD para Sparkle/Hanabi): Permite que seu DPS use Botas de ATQ% com zero velocidade e ainda assim aja como se tivesse 160+ de VEL."
            elif "robin" in char_lower:
                tuning_tip = "Robin Tuning: Mantenha por volta de 120-125 SPD com o conjunto Vonwacq para avançar a ação no início da batalha e abrir o Concerto rapidamente."

            turnos_ciclo0 = 2 if speed >= 134.0 else 1
            if speed >= 200.0:
                turnos_ciclo0 = 3
            cycles_summary = f"{speed_av} AV/turno • Ciclo 0 (150 AV): {turnos_ciclo0} Ação(ões) • Meta 134 SPD: {'Atingida' if speed >= 134.0 else 'Incompleta'}"

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

        # Check EHR para debuffers
        debuffers_67 = ["silver", "pela", "welt", "guinaifen"]
        debuffers_120 = ["black swan", "cisne negro", "jiaoqiu"]
        if ehr > 0 or any(d in char_lower for d in debuffers_67 + debuffers_120):
            target_ehr = 120.0 if any(d in char_lower for d in debuffers_120) else 67.0
            is_ehr_ok = ehr >= target_ehr
            status_ehr = (
                f"100% de Aplicação garantida contra chefes Lvl 95 (Meta: {target_ehr}%)"
                if is_ehr_ok
                else f"Risco de falha na aplicação de debuffs (Meta: {target_ehr}%)"
            )
            breakpoints.append(
                {
                    "stat": "Efetividade de Acerto (EHR)",
                    "current": f"{ehr:.1f}%",
                    "status": status_ehr,
                    "next_goal": f"Faltam {max(0.0, target_ehr - ehr):.1f}% de EHR"
                    if not is_ehr_ok
                    else "Meta de EHR atingida!",
                    "is_reached": is_ehr_ok,
                    "tier_progress": min(100.0, round((ehr / target_ehr) * 100.0, 1)),
                    "category": "debuff",
                    "speed_tuning_tip": "Debuffs aplicados com sucesso reduzem as defesas dos inimigos antes das ações do DPS.",
                }
            )

    elif game_id == "genshin":
        # Check Recarga de Energia (ER)
        target_er = 160.0
        if "xiangling" in char_lower:
            target_er = 200.0
        elif "faruzan" in char_lower:
            target_er = 250.0
        elif "raiden" in char_lower:
            target_er = 220.0
        elif "xingqiu" in char_lower or "yelan" in char_lower:
            target_er = 180.0
        elif "furina" in char_lower or "bennett" in char_lower:
            target_er = 180.0
        elif "neuvillette" in char_lower:
            target_er = 125.0

        is_er_ok = er >= target_er
        status_er = (
            f"Supremo carregado a cada rotação de 20s (Meta: {target_er}%)"
            if is_er_ok
            else f"Rotação truncada por falta de energia (Meta: {target_er}%)"
        )
        breakpoints.append(
            {
                "stat": "Recarga de Energia (ER)",
                "current": f"{er:.1f}%",
                "status": status_er,
                "next_goal": f"Faltam {max(0.0, target_er - er):.1f}% de ER para rotação fluida"
                if not is_er_ok
                else "Meta de Recarga atingida!",
                "is_reached": is_er_ok,
                "tier_progress": min(100.0, round((er / target_er) * 100.0, 1)) if target_er > 0 else 100.0,
                "category": "energy",
                "speed_tuning_tip": "Alinhe partículas com o Supremo para evitar perda de DPS por rotações estagnadas.",
            }
        )

        # Checagem de Favonius Weapon Procs
        if (
            crit_rate > 0
            and crit_rate < 40.0
            and any(s in char_lower for s in ["bennett", "kazuha", "faruzan", "diona", "gorou", "thoma"])
        ):
            breakpoints.append(
                {
                    "stat": "Geração de Partículas (Favonius Check)",
                    "current": f"{crit_rate:.1f}% Taxa CRIT",
                    "status": "Taxa crítica baixa para ativação consistente da Arma de Favonius (Alvo: 40% - 50%)",
                    "next_goal": f"Aumente a Taxa CRIT em {40.0 - crit_rate:.1f}% para garantir partículas neutras para a equipe.",
                    "is_reached": False,
                    "tier_progress": min(100.0, round((crit_rate / 40.0) * 100.0, 1)),
                    "category": "energy",
                    "speed_tuning_tip": "Armas de Favonius só geram partículas em acertos críticos dentro de campo.",
                }
            )

    elif game_id == "zzz":
        if "jane" in char_lower or ap > 0:
            target_ap = 420.0 if "jane" in char_lower else 300.0
            is_ap_ok = ap >= target_ap
            breakpoints.append(
                {
                    "stat": "Proficiência em Anomalia (AP)",
                    "current": f"{ap:.0f} AP",
                    "status": f"100% Taxa CRIT de Assalto e dano de anomalia amplificado (Meta: {target_ap} AP)"
                    if is_ap_ok
                    else f"Abaixo do limiar ideal de Anomalia (Meta: {target_ap} AP)",
                    "next_goal": f"Faltam {max(0.0, target_ap - ap):.0f} AP"
                    if not is_ap_ok
                    else "Meta de Anomalia atingida!",
                    "is_reached": is_ap_ok,
                    "tier_progress": min(100.0, round((ap / target_ap) * 100.0, 1)),
                    "category": "anomaly",
                    "speed_tuning_tip": "Jane Doe converte AP em Taxa Crítica para o gatilho de Assalto até o cap de 420.",
                }
            )

        if impact > 0 or any(s in char_lower for s in ["anby", "lycaon", "qingyi", "koleda"]):
            is_imp_ok = impact >= 130.0
            breakpoints.append(
                {
                    "stat": "Impacto / Atordoamento (Stun Rate)",
                    "current": f"{impact:.0f} Impacto",
                    "status": "Excelente multiplicador de atordoamento para quebra rápida de postura"
                    if is_imp_ok
                    else "Impacto pode ser aumentado no Disco 6 para atordoar chefes mais rápido",
                    "next_goal": "Equipar Disco 6 com Impacto %" if not is_imp_ok else "Limiar de Stunner atingido!",
                    "is_reached": is_imp_ok,
                    "tier_progress": min(100.0, round((impact / 140.0) * 100.0, 1)) if impact > 0 else 50.0,
                    "category": "impact",
                    "speed_tuning_tip": "Quanto maior o Impacto do Atordoador, mais cedo o time entra na janela de Chain Attacks.",
                }
            )

    # Proporção Crítica 1:2 Universal
    if crit_rate > 0 and crit_dmg > 0:
        ratio = round(crit_dmg / max(1.0, crit_rate), 2)
        is_ratio_ok = 1.7 <= ratio <= 2.3
        status_crit = (
            f"Proporção Áurea 1:{ratio} (Muito próxima do ideal 1:2)"
            if is_ratio_ok
            else f"Proporção atual 1:{ratio} (Desvio do equilíbrio 1:2)"
        )
        goal_crit = (
            "Equilíbrio de Crítico excelente!"
            if is_ratio_ok
            else ("Invista mais em Taxa CRIT" if ratio > 2.3 else "Invista mais em Dano CRIT")
        )
        breakpoints.append(
            {
                "stat": "Proporção Crítica (1:2)",
                "current": f"{crit_rate:.1f}% CR / {crit_dmg:.1f}% CD",
                "status": status_crit,
                "next_goal": goal_crit,
                "is_reached": is_ratio_ok,
                "tier_progress": 100.0 if is_ratio_ok else 65.0,
                "category": "crit",
                "speed_tuning_tip": "Manter a relação 1:2 maximiza matematicamente o Dano Médio esperado (Expectation Value).",
            }
        )

    return {
        "char_name": char_name,
        "game_id": game_id,
        "speed_action_value": speed_av,
        "cycles_summary": cycles_summary,
        "breakpoints": breakpoints,
    }

