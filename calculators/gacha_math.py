"""Simulador estocástico Monte Carlo e projeção de acumulação para banners Gacha."""

import random
from datetime import datetime, timedelta
from typing import Optional


def simulate_gacha_probabilities(
    game_id: str,
    current_pity: int,
    is_guaranteed: bool,
    pulls_available: int,
    target_copies: int = 1,
    current_copies: int = 0,
    current_rank: Optional[int] = None,
    target_rank: Optional[int] = None,
    banner_type: str = "character",
    num_simulations: int = 10000,
) -> dict:
    """
    Executa uma Simulação Monte Carlo para calcular a chance real (%) de obter N cópias do personagem ou arma alvo
    com base no Pity atual, Garantido (50/50 ou 75/25), Desejos/Tiros disponíveis e o nível de Constelação/Eidolon/Refinamento já possuído.
    """
    game_id = (game_id or "genshin").lower().strip()
    is_weapon = str(banner_type).lower().strip() in ["weapon", "light_cone", "w_engine", "arma", "cone"]
    max_pity_cap = 79 if is_weapon else 89
    current_pity = max(0, min(current_pity, max_pity_cap))
    pulls_available = max(0, pulls_available)

    # Determina o prefixo e terminologia de acordo com o jogo e tipo de banner
    if is_weapon:
        if game_id == "genshin":
            prefix = "R"
            term = "Refinamento"
        elif game_id == "hsr":
            prefix = "S"
            term = "Sobreposição"
        else:  # zzz
            prefix = "★"
            term = "Refinamento de Motor-W"
        max_rank_limit = 4  # R1 (0) a R5 (4)
    else:
        if game_id == "genshin":
            prefix = "C"
            term = "Constelação"
        elif game_id == "hsr":
            prefix = "E"
            term = "Eidolon"
        else:  # zzz
            prefix = "M"
            term = "Mindscape Cinema"
        max_rank_limit = 6  # C0/E0/M0 (0) a C6/E6/M6 (6)

    # Converter current_rank e target_rank com suporte a fallback de current_copies / target_copies
    if current_rank is not None:
        curr_r = max(-1, min(current_rank, max_rank_limit))
    elif current_copies > 0:
        curr_r = max(-1, min(current_copies - 1, max_rank_limit))
    else:
        curr_r = -1

    if target_rank is not None:
        tgt_r = max(0, min(target_rank, max_rank_limit))
    elif target_copies > 0:
        tgt_r = max(0, min(curr_r + target_copies, max_rank_limit))
    else:
        tgt_r = max(0, curr_r)

    # Total de cópias já possuídas vs total necessário para a meta
    owned_pulls = 0 if curr_r < 0 else (curr_r + 1)
    target_pulls = tgt_r + 1
    needed_new_copies = max(0, target_pulls - owned_pulls)

    rank_display_offset = 1 if is_weapon else 0
    curr_rank_label = "Não Possui" if curr_r < 0 else f"{prefix}{curr_r + rank_display_offset}"
    target_rank_label = f"{prefix}{tgt_r + rank_display_offset}"

    # Se a meta já foi alcançada ou superada
    if needed_new_copies == 0:
        dist_meta = {f"Já possui {curr_rank_label} (Meta {target_rank_label} já alcançada)": 100.0}
        return {
            "success_rate": 100.0,
            "target_copies": 0,
            "needed_new_copies": 0,
            "current_rank": curr_r,
            "target_rank": tgt_r,
            "current_rank_str": curr_rank_label,
            "target_rank_str": target_rank_label,
            "term": term,
            "banner_type": "weapon" if is_weapon else "character",
            "pulls_available": pulls_available,
            "current_pity": current_pity,
            "is_guaranteed": is_guaranteed,
            "avg_pulls_spent": 0,
            "distribution": dist_meta,
            "num_simulations": num_simulations,
            "game_id": game_id,
        }

    # Parâmetros da mecânica de Gacha por jogo e tipo de banner
    if is_weapon:
        if game_id == "genshin":
            soft_pity_start = 63
            base_rate = 0.007  # 0.7%
            soft_pity_increment = 0.07
            promo_chance = 0.75  # 75% rate up
            fate_point_cap = 1  # Limite oficial de 1 ponto de destino na v5.0+
        elif game_id == "hsr":
            soft_pity_start = 65
            base_rate = 0.008  # 0.8%
            soft_pity_increment = 0.065
            promo_chance = 0.75  # 75/25
            fate_point_cap = 0
        else:  # zzz
            soft_pity_start = 65
            base_rate = 0.010  # 1.0%
            soft_pity_increment = 0.065
            promo_chance = 0.75  # 75/25
            fate_point_cap = 0
    else:
        soft_pity_start = 74 if game_id in ["genshin", "hsr"] else 75
        base_rate = 0.006  # 0.6%
        soft_pity_increment = 0.06
        promo_chance = 0.50  # 50/50
        fate_point_cap = 0

    if num_simulations <= 0:
        return {
            "success_rate": 0.0,
            "target_copies": needed_new_copies,
            "needed_new_copies": needed_new_copies,
            "current_rank": curr_r,
            "target_rank": tgt_r,
            "current_rank_str": curr_rank_label,
            "target_rank_str": target_rank_label,
            "term": term,
            "banner_type": "weapon" if is_weapon else "character",
            "pulls_available": pulls_available,
            "current_pity": current_pity,
            "is_guaranteed": is_guaranteed,
            "avg_pulls_spent": None,
            "distribution": {},
            "num_simulations": 0,
            "game_id": game_id,
        }

    hard_pity = 80 if is_weapon else 90
    successful_runs = 0
    total_pulls_spent_list = []
    copies_obtained_distribution = {i: 0 for i in range(needed_new_copies + 1)}

    for _ in range(num_simulations):
        pity = current_pity
        guaranteed = is_guaranteed
        fate_points = 0
        copies = 0
        pulls_left = pulls_available
        pulls_spent = 0

        while pulls_left > 0 and copies < needed_new_copies:
            pulls_left -= 1
            pulls_spent += 1
            pity += 1

            # Cálculo de probabilidade do tiro atual com soft pity e hard pity absoluto
            if pity >= hard_pity:
                chance = 1.0
            elif pity < soft_pity_start:
                chance = base_rate
            else:
                chance = min(1.0, base_rate + (pity - soft_pity_start + 1) * soft_pity_increment)

            if random.random() < chance:
                # Tirou um 5★ / Rank S
                pity = 0
                if is_weapon:
                    # Mecânica de Armas / Cones / Motores
                    if game_id == "genshin":
                        # Genshin Caminho Divino (Fate Points máx 1)
                        if fate_points >= fate_point_cap:
                            copies += 1
                            fate_points = 0
                            guaranteed = False
                        elif guaranteed:
                            # 50% de vir a arma alvo específica entre as 2 promocionais
                            if random.random() < 0.5:
                                copies += 1
                                fate_points = 0
                                guaranteed = False
                            else:
                                fate_points += 1
                                guaranteed = False
                        else:
                            # 75% promocional
                            if random.random() < 0.75:
                                if random.random() < 0.5:
                                    copies += 1
                                    fate_points = 0
                                    guaranteed = False
                                else:
                                    fate_points += 1
                                    guaranteed = False
                            else:
                                # Perdeu para mochileiro
                                guaranteed = True
                                fate_points += 1
                    else:
                        # HSR e ZZZ (75/25 garantido puro)
                        if guaranteed or random.random() < 0.75:
                            copies += 1
                            guaranteed = False
                        else:
                            guaranteed = True
                else:
                    # Mecânica de Personagens (50/50)
                    if guaranteed or random.random() < 0.5:
                        copies += 1
                        guaranteed = False
                    else:
                        guaranteed = True

        copies_obtained_distribution[copies] = copies_obtained_distribution.get(copies, 0) + 1
        if copies >= needed_new_copies:
            successful_runs += 1
            total_pulls_spent_list.append(pulls_spent)

    success_rate = (successful_runs / num_simulations) * 100.0
    avg_pulls_needed = (
        round(sum(total_pulls_spent_list) / len(total_pulls_spent_list), 1) if total_pulls_spent_list else None
    )

    # Converter distribuição em porcentagens com nomenclaturas reais dos jogos
    dist_pct = {}
    for k in range(needed_new_copies + 1):
        count = copies_obtained_distribution.get(k, 0)
        pct = round((count / num_simulations) * 100.0, 1)

        if k == 0:
            if curr_r < 0:
                lbl = "0 cópias (Não obtém o item alvo)"
            else:
                lbl = f"0 novas cópias (Mantém {prefix}{curr_r + rank_display_offset})"
        else:
            final_r = (curr_r if curr_r >= 0 else -1) + k
            final_str = f"{prefix}{final_r + rank_display_offset}"
            if final_r >= tgt_r:
                lbl = f"+{k} cópia(s) (Alcança {final_str} - Meta Batida! 🎉)"
            else:
                lbl = f"+{k} cópia(s) (Alcança {final_str})"
        dist_pct[lbl] = pct

    return {
        "success_rate": round(success_rate, 1),
        "target_copies": needed_new_copies,
        "needed_new_copies": needed_new_copies,
        "current_rank": curr_r,
        "target_rank": tgt_r,
        "current_rank_str": curr_rank_label,
        "target_rank_str": target_rank_label,
        "term": term,
        "banner_type": "weapon" if is_weapon else "character",
        "pulls_available": pulls_available,
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
        "avg_pulls_spent": avg_pulls_needed,
        "distribution": dist_pct,
        "num_simulations": num_simulations,
        "game_id": game_id,
    }


def calculate_gacha_forecast(
    game_id: str,
    current_pulls: int,
    current_pity: int,
    is_guaranteed: bool,
    target_rank: int = 0,
    current_rank: int = -1,
    target_days: int = 21,
    has_daily_pass: bool = False,
    has_battle_pass: bool = False,
    include_shop_resets: bool = True,
    include_events_estimate: bool = True,
    include_endgame_resets: bool = True,
    character_name: str = "",
    banner_type: str = "character",
    num_simulations: int = 10000,
) -> dict:
    """
    Calcula a projeção completa de acúmulo de tiros/gemas futuras (diárias, passe, eventos, resets)
    e executa simulação Monte Carlo conectada para prever a probabilidade de bater a meta de banner de personagem ou arma.
    """
    game_id = (game_id or "genshin").lower().strip()
    is_weapon = str(banner_type).lower().strip() in ["weapon", "light_cone", "w_engine", "arma", "cone"]
    target_days = max(1, min(int(target_days), 180))
    current_pulls = max(0, int(current_pulls))
    max_pity_cap = 79 if is_weapon else 89
    max_rank_cap = 4 if is_weapon else 6
    current_pity = max(0, min(int(current_pity), max_pity_cap))
    target_rank = max(0, min(int(target_rank), max_rank_cap))
    current_rank = max(-1, min(int(current_rank), max_rank_cap))

    # Nomenclaturas oficiais por jogo e tipo de banner
    if is_weapon:
        if game_id == "genshin":
            term = "Refinamento"
            prefix = "R"
            currency = "Gemas Essenciais"
            pass_name = "Bênção da Lua Nova"
        elif game_id == "hsr":
            term = "Sobreposição"
            prefix = "S"
            currency = "Jades Estelares"
            pass_name = "Passe de Suprimentos do Expresso"
        else:  # zzz
            term = "Refinamento de Motor-W"
            prefix = "★"
            currency = "Policromos"
            pass_name = "Associação Inter-Nó"
        t_info = {
            "term": term,
            "prefix": prefix,
            "currency": currency,
            "pass_name": pass_name,
        }
    else:
        game_terms = {
            "genshin": {
                "term": "Constelação",
                "prefix": "C",
                "currency": "Gemas Essenciais",
                "pass_name": "Bênção da Lua Nova",
            },
            "hsr": {
                "term": "Eidolon",
                "prefix": "E",
                "currency": "Jades Estelares",
                "pass_name": "Passe de Suprimentos do Expresso",
            },
            "zzz": {
                "term": "Mindscape Cinema",
                "prefix": "M",
                "currency": "Policromos",
                "pass_name": "Associação Inter-Nó",
            },
        }
        t_info = game_terms.get(game_id, game_terms["genshin"])
        term = t_info["term"]
        prefix = t_info["prefix"]
        currency = t_info["currency"]
        pass_name = t_info["pass_name"]

    # 1. Projeção de Renda Diária F2P (60 gemas/dia em todos os 3 jogos)
    daily_gems = target_days * 60
    daily_pulls = daily_gems / 160.0

    # 2. Passe Diário (+90 gemas/dia)
    pass_gems = (target_days * 90) if has_daily_pass else 0
    pass_pulls = pass_gems / 160.0

    # 3. Resets Mensais da Loja (5 tiros no dia 1º de cada mês)
    shop_resets_count = 0
    if include_shop_resets:
        now = datetime.now()
        for d in range(1, target_days + 1):
            future_day = now + timedelta(days=d)
            if future_day.day == 1:
                shop_resets_count += 1
    shop_pulls = shop_resets_count * 5

    # 4. Projeção de Eventos da Versão (~52.4 gemas/dia de média de eventos)
    events_gems = int(target_days * 52.4) if include_events_estimate else 0
    events_pulls = events_gems / 160.0

    # 5. Endgame Quinzenal/Mensal (Abismo/Teatro/MoC/PF/AS/Shiyu - ~800 gemas por ciclo de 15 dias)
    endgame_cycles = (target_days // 15) if include_endgame_resets else 0
    endgame_gems = endgame_cycles * 800
    endgame_pulls = endgame_gems / 160.0

    # 6. Passe de Batalha (4 tiros especiais + 680 gemas por patch de 42 dias -> ~8.25 tiros)
    bp_pulls = round((target_days / 42.0) * 8.25, 1) if has_battle_pass else 0.0

    # Total de Tiros Futuros Acumulados
    future_pulls_total = round(daily_pulls + pass_pulls + shop_pulls + events_pulls + endgame_pulls + bp_pulls, 1)
    total_projected_pulls = int(current_pulls + future_pulls_total)

    # 7. Simulação Monte Carlo com o Total Projetado
    sim_result = simulate_gacha_probabilities(
        game_id=game_id,
        current_pity=current_pity,
        is_guaranteed=is_guaranteed,
        pulls_available=total_projected_pulls,
        current_rank=current_rank,
        target_rank=target_rank,
        banner_type=banner_type,
        num_simulations=num_simulations,
    )

    # Simulação de Comparação F2P (Apenas Saldo Atual + Diárias Puras)
    f2p_pure_pulls = int(current_pulls + daily_pulls + shop_pulls)
    f2p_sim_result = simulate_gacha_probabilities(
        game_id=game_id,
        current_pity=current_pity,
        is_guaranteed=is_guaranteed,
        pulls_available=f2p_pure_pulls,
        current_rank=current_rank,
        target_rank=target_rank,
        banner_type=banner_type,
        num_simulations=3000,
    )

    # 8. Cálculo Matemático de Pior Cenário (Worst-case para 100% de Garantia)
    needed_new_copies = sim_result.get("needed_new_copies", 1)
    hard_pity_val = 80 if is_weapon else 90
    max_guarantee_multiplier = 160 if is_weapon else 180

    if needed_new_copies <= 0:
        worst_case_pulls = 0
    elif needed_new_copies == 1:
        worst_case_pulls = (
            (hard_pity_val - current_pity) if is_guaranteed else (max_guarantee_multiplier - current_pity)
        )
    else:
        first_copy_worst = (
            (hard_pity_val - current_pity) if is_guaranteed else (max_guarantee_multiplier - current_pity)
        )
        remaining_copies_worst = (needed_new_copies - 1) * max_guarantee_multiplier
        worst_case_pulls = first_copy_worst + remaining_copies_worst

    pulls_needed_for_guarantee = max(0, worst_case_pulls - total_projected_pulls)
    gems_needed_for_guarantee = pulls_needed_for_guarantee * 160

    # 9. Parecer Estratégico Textual & Classificação
    success_rate = sim_result.get("success_rate", 0.0)
    target_rank_display = target_rank + (1 if is_weapon else 0)
    if needed_new_copies <= 0:
        verdict_status = "ACQUIRED"
        verdict_badge = "Meta Já Alcançada"
        verdict_color = "#34d399"
        verdict_text = f"Você já possui o nível desejado ({prefix}{target_rank_display}) no seu Roster!"
    elif success_rate >= 95.0:
        verdict_status = "SAFE"
        verdict_badge = "Garantia Praticamente Assegurada"
        verdict_color = "#34d399"
        verdict_text = f"Excelente planejamento! Sua probabilidade de sucesso é de {success_rate}%. Com ~{total_projected_pulls} tiros projetados, o risco de não bater a meta é quase nulo."
    elif success_rate >= 75.0:
        verdict_status = "FAVORABLE"
        verdict_badge = "Cenário Muito Favorável"
        verdict_color = "#10b981"
        verdict_text = f"Probabilidade Alta ({success_rate}%). Você acumulará cerca de {int(future_pulls_total)} novos tiros em {target_days} dias. Mantenha as diárias e eventos em dia."
    elif success_rate >= 50.0:
        verdict_status = "MODERATE"
        verdict_badge = "Cenário Competitivo (50/50)"
        verdict_color = "#fbbf24"
        verdict_text = f"Probabilidade Moderada ({success_rate}%). Você terá ~{total_projected_pulls} tiros até o fim do banner. Faltam {pulls_needed_for_guarantee} tiros para 100% de garantia matemática."
    elif success_rate >= 25.0:
        verdict_status = "RISKY"
        verdict_badge = "Cenário de Alto Risco"
        verdict_color = "#f97316"
        verdict_text = f"Probabilidade Baixa ({success_rate}%). O saldo projetado de {total_projected_pulls} tiros pode não ser suficiente caso perca o 50/50. Faltam {pulls_needed_for_guarantee} tiros para garantir."
    else:
        verdict_status = "CRITICAL"
        verdict_badge = "Cenário Crítico"
        verdict_color = "#ef4444"
        verdict_text = f"Probabilidade Crítica ({success_rate}%). Recomenda-se economizar mais recursos ou focar no C0/E0/M0 antes de arriscar cópias adicionais."

    income_breakdown = {
        "current_pulls": current_pulls,
        "current_gems_equiv": current_pulls * 160,
        "daily_f2p": {
            "days": target_days,
            "gems": daily_gems,
            "pulls": round(daily_pulls, 1),
            "label": f"Missões Diárias ({target_days}d × 60)",
        },
        "daily_pass": {
            "active": has_daily_pass,
            "gems": pass_gems,
            "pulls": round(pass_pulls, 1),
            "label": f"{pass_name} ({target_days}d × 90)" if has_daily_pass else f"{pass_name} (Inativo)",
        },
        "battle_pass": {
            "active": has_battle_pass,
            "pulls": round(bp_pulls, 1),
            "label": "Passe de Batalha (Prorrateado)" if has_battle_pass else "Passe de Batalha (Inativo)",
        },
        "shop_resets": {
            "count": shop_resets_count,
            "pulls": shop_pulls,
            "label": f"Reset de Loja ({shop_resets_count} mês(es) × 5)",
        },
        "events": {
            "active": include_events_estimate,
            "gems": events_gems,
            "pulls": round(events_pulls, 1),
            "label": f"Eventos de Versão (~{events_gems} gemas)",
        },
        "endgame": {
            "cycles": endgame_cycles,
            "gems": endgame_gems,
            "pulls": round(endgame_pulls, 1),
            "label": f"Endgame ({endgame_cycles} ciclos × 800 gemas)",
        },
        "total_future_pulls": future_pulls_total,
        "total_projected_pulls": total_projected_pulls,
        "total_projected_gems_equiv": total_projected_pulls * 160,
    }

    return {
        "game_id": game_id,
        "banner_type": banner_type,
        "character_name": character_name or "Personagem 5★ Alvo",
        "target_days": target_days,
        "current_pulls": current_pulls,
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
        "current_rank": current_rank,
        "target_rank": target_rank,
        "current_rank_str": sim_result["current_rank_str"],
        "target_rank_str": sim_result["target_rank_str"],
        "term": t_info["term"],
        "needed_new_copies": needed_new_copies,
        "total_projected_pulls": total_projected_pulls,
        "income_breakdown": income_breakdown,
        "success_rate": success_rate,
        "f2p_pure_success_rate": f2p_sim_result.get("success_rate", 0.0),
        "f2p_pure_pulls": f2p_pure_pulls,
        "avg_pulls_spent": sim_result.get("avg_pulls_spent"),
        "worst_case_pulls": worst_case_pulls,
        "pulls_needed_for_guarantee": pulls_needed_for_guarantee,
        "gems_needed_for_guarantee": gems_needed_for_guarantee,
        "distribution": sim_result.get("distribution", {}),
        "verdict": {"status": verdict_status, "badge": verdict_badge, "color": verdict_color, "text": verdict_text},
    }

