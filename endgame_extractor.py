import asyncio
import re
import genshin
from typing import Optional, Dict, List, Any, Tuple

def format_team_node(node_name: str, characters: list, monsters: list = None, char_map: Dict[str, str] = None) -> str:
    """Formata os detalhes de uma metade/nó do endgame para texto Markdown."""
    if not characters:
        return ""
    
    lines = [f"    - **{node_name}:**"]
    # Formata personagens
    char_names = []
    for c in characters:
        name = getattr(c, "name", None)
        if not name and hasattr(c, "id"):
            cid = str(c.id)
            name = char_map.get(cid, f"Desconhecido (ID: {cid})") if char_map else f"Avatar {cid}"
        elif not name:
            name = "Desconhecido"
            
        level = getattr(c, "level", "?")
        char_names.append(f"{name} (Nv.{level})")
    lines.append(f"      • Equipe: {', '.join(char_names)}")
    
    # Formata monstros (se disponível)
    if monsters:
        monster_names = []
        for m in monsters:
            m_name = getattr(m, "name", "Inimigo")
            m_level = getattr(m, "level", "?")
            monster_names.append(f"{m_name} (Nv.{m_level})")
        lines.append(f"      • Inimigos: {', '.join(monster_names)}")
        
    return "\n".join(lines)


def _build_char_node_data(c: Any, char_map: Dict[str, str] = None, roster_map: Dict[str, dict] = None) -> dict:
    """Cria o dicionário estruturado com metadados para um personagem de endgame."""
    c_name = getattr(c, "name", None)
    c_id = str(getattr(c, "id", ""))
    if not c_name and c_id:
        if c_id.startswith("800") or c_id.startswith("801") or c_id in ["8001", "8002", "8003", "8004", "8005", "8006", "8007", "8008", "8009", "8010"]:
            c_name = "Desbravador(a)"
        elif c_id in ["10000005", "10000007"]:
            c_name = "Viajante"
        else:
            c_name = char_map.get(c_id, f"Desconhecido (ID: {c_id})") if char_map else f"Avatar {c_id}"
    elif c_name and ("8009" in c_name or "800" in c_name and "desconhecido" in c_name.lower()):
        c_name = "Desbravador(a)"
    elif not c_name:
        c_name = "Desconhecido"
        
    c_lvl = getattr(c, "level", 80)
    c_icon = getattr(c, "icon", "")
    c_elem = getattr(c, "element", "")
    c_rarity = getattr(c, "rarity", 5)
    c_rank = getattr(c, "rank", getattr(c, "mindscape", getattr(c, "constellation", None)))
    rank_str = f"E{c_rank}" if c_rank is not None else ""

    # Enriquece com o roster se disponível
    if roster_map and c_name.lower() in roster_map:
        rm = roster_map[c_name.lower()]
        if not c_icon and rm.get("icon"):
            c_icon = rm["icon"]
        if not c_elem and rm.get("element"):
            c_elem = rm["element"]
        if rm.get("rarity"):
            c_rarity = rm["rarity"]
        if not rank_str and rm.get("rank_str"):
            rank_str = rm["rank_str"]

    return {
        "id": c_id,
        "name": c_name,
        "level": c_lvl,
        "icon": c_icon,
        "element": str(c_elem).lower() if c_elem else "",
        "rarity": c_rarity,
        "rank_str": rank_str
    }


# ==============================================================================
# EXTRAÇÃO HONKAI: STAR RAIL
# ==============================================================================
async def extrair_endgame_hsr_data(client: genshin.Client, uid: int) -> Tuple[str, List[dict]]:
    """Extrai os dados de Endgame de HSR retornando texto formatado e lista estruturada."""
    text = "=== HONKAI: STAR RAIL - ENDGAME ===\n"
    modes = []
    
    char_map = {}
    try:
        chars = await client.get_starrail_characters(uid)
        for c in chars.avatar_list:
            char_map[str(c.id)] = c.name
    except Exception:
        pass
    
    # 1. Caos da Memória (MoC)
    try:
        moc = await client.get_starrail_challenge(uid)
        if moc.floors:
            floor = moc.floors[0]
            has_node_3 = hasattr(floor, 'node_3') and floor.node_3 is not None
            max_stars = 4 if has_node_3 else 3
            star_num = getattr(floor, 'star_num', getattr(floor, 'stars', max_stars))
            
            text += f" **Caos da Memória (MoC)** - {floor.name}\n"
            text += f"  • Estrelas: {star_num}/{max_stars} | Rodadas Utilizadas: {floor.round_num}\n"
            text += format_team_node("Lado 1", getattr(floor.node_1, "avatars", []), getattr(floor.node_1, "monsters", []), char_map) + "\n"
            text += format_team_node("Lado 2", getattr(floor.node_2, "avatars", []), getattr(floor.node_2, "monsters", []), char_map) + "\n"
            if has_node_3:
                text += format_team_node("Lado 3", getattr(floor.node_3, "avatars", []), getattr(floor.node_3, "monsters", []), char_map) + "\n"

            teams = []
            for n_idx, n_obj in enumerate([floor.node_1, floor.node_2, getattr(floor, "node_3", None)], 1):
                if not n_obj: continue
                n_chars = [_build_char_node_data(a, char_map) for a in getattr(n_obj, "avatars", [])]
                n_monsters = [{"name": getattr(m, "name", "Inimigo"), "level": getattr(m, "level", "?")} for m in getattr(n_obj, "monsters", [])]
                teams.append({
                    "name": f"Lado {n_idx}",
                    "characters": n_chars,
                    "monsters": n_monsters
                })

            modes.append({
                "id": "moc",
                "name": "Caos da Memória (MoC)",
                "badge": "MoC",
                "stage": floor.name,
                "stars": star_num,
                "max_stars": max_stars,
                "metric_label": "Rodadas Utilizadas",
                "metric_value": str(floor.round_num),
                "teams": teams
            })
    except Exception as e:
        print(f"[Aviso] Erro ao extrair MoC HSR: {e}")

    # 2. Ficção Pura (Pure Fiction)
    try:
        pf = await client.get_starrail_pure_fiction(uid)
        if pf.floors:
            floor = pf.floors[0]
            has_node_3 = hasattr(floor, 'node_3') and floor.node_3 is not None
            max_stars = 4 if has_node_3 else 3
            star_num = getattr(floor, 'star_num', getattr(floor, 'stars', max_stars))
            
            text += f" **Ficção Pura** - {floor.name}\n"
            text += f"  • Estrelas: {star_num}/{max_stars} | Pontuação: {floor.score}\n"
            text += format_team_node("Lado 1", getattr(floor.node_1, "avatars", []), getattr(floor.node_1, "monsters", []), char_map) + "\n"
            text += format_team_node("Lado 2", getattr(floor.node_2, "avatars", []), getattr(floor.node_2, "monsters", []), char_map) + "\n"
            if has_node_3:
                text += format_team_node("Lado 3", getattr(floor.node_3, "avatars", []), getattr(floor.node_3, "monsters", []), char_map) + "\n"

            teams = []
            for n_idx, n_obj in enumerate([floor.node_1, floor.node_2, getattr(floor, "node_3", None)], 1):
                if not n_obj: continue
                n_chars = [_build_char_node_data(a, char_map) for a in getattr(n_obj, "avatars", [])]
                n_monsters = [{"name": getattr(m, "name", "Inimigo"), "level": getattr(m, "level", "?")} for m in getattr(n_obj, "monsters", [])]
                teams.append({
                    "name": f"Lado {n_idx}",
                    "characters": n_chars,
                    "monsters": n_monsters
                })

            modes.append({
                "id": "pure_fiction",
                "name": "Ficção Pura",
                "badge": "PF",
                "stage": floor.name,
                "stars": star_num,
                "max_stars": max_stars,
                "metric_label": "Pontuação",
                "metric_value": f"{floor.score:,}".replace(",", "."),
                "teams": teams
            })
    except Exception as e:
        print(f"[Aviso] Erro ao extrair Ficção Pura HSR: {e}")

    # 3. Sombra Apocalíptica (Apocalyptic Shadow)
    try:
        apc = await client.get_starrail_apc_shadow(uid)
        if apc.floors:
            floor = apc.floors[0]
            has_node_3 = hasattr(floor, 'node_3') and floor.node_3 is not None
            max_stars = 4 if has_node_3 else 3
            star_num = getattr(floor, 'star_num', getattr(floor, 'stars', max_stars))
            
            text += f" **Sombra Apocalíptica** - {floor.name}\n"
            text += f"  • Estrelas: {star_num}/{max_stars} | Pontuação: {floor.score}\n"
            text += format_team_node("Lado 1", getattr(floor.node_1, "avatars", []), getattr(floor.node_1, "monsters", []), char_map) + "\n"
            text += format_team_node("Lado 2", getattr(floor.node_2, "avatars", []), getattr(floor.node_2, "monsters", []), char_map) + "\n"
            if has_node_3:
                text += format_team_node("Lado 3", getattr(floor.node_3, "avatars", []), getattr(floor.node_3, "monsters", []), char_map) + "\n"

            teams = []
            for n_idx, n_obj in enumerate([floor.node_1, floor.node_2, getattr(floor, "node_3", None)], 1):
                if not n_obj: continue
                n_chars = [_build_char_node_data(a, char_map) for a in getattr(n_obj, "avatars", [])]
                n_monsters = [{"name": getattr(m, "name", "Inimigo"), "level": getattr(m, "level", "?")} for m in getattr(n_obj, "monsters", [])]
                teams.append({
                    "name": f"Lado {n_idx}",
                    "characters": n_chars,
                    "monsters": n_monsters
                })

            modes.append({
                "id": "apocalyptic_shadow",
                "name": "Sombra Apocalíptica",
                "badge": "AS",
                "stage": floor.name,
                "stars": star_num,
                "max_stars": max_stars,
                "metric_label": "Pontuação",
                "metric_value": f"{floor.score:,}".replace(",", "."),
                "teams": teams
            })
    except Exception as e:
        print(f"[Aviso] Erro ao extrair Sombra Apocalíptica HSR: {e}")
        
    return (text if modes else "", modes)

async def extrair_endgame_hsr(client: genshin.Client, uid: int) -> str:
    text, _ = await extrair_endgame_hsr_data(client, uid)
    return text


# ==============================================================================
# EXTRAÇÃO GENSHIN IMPACT
# ==============================================================================
async def extrair_endgame_genshin_data(client: genshin.Client, uid: int) -> Tuple[str, List[dict]]:
    """Extrai os dados de Endgame de Genshin retornando texto formatado e lista estruturada."""
    text = "=== GENSHIN IMPACT - ENDGAME ===\n"
    modes = []

    # 1. Abismo Espiral
    try:
        abyss = await client.get_genshin_spiral_abyss(uid)
        if not abyss.floors:
            try:
                abyss = await client.get_genshin_spiral_abyss(uid, previous=True)
            except Exception:
                pass
        if abyss.floors:
            floor = abyss.floors[-1]
            chamber = floor.chambers[-1] if floor.chambers else None
            stage_name = f"Piso {floor.floor}" + (f" (Câmara {chamber.chamber})" if chamber else "")
            
            text += f" **Abismo Espiral** - {stage_name}\n"
            text += f"  • Estrelas do Piso: {floor.stars}/{floor.max_stars}\n"
            
            teams = []
            if chamber and chamber.battles:
                for b in chamber.battles:
                    node_name = "Primeira Metade" if b.half == 1 else "Segunda Metade"
                    
                    monsters = []
                    if b.half == 1 and hasattr(chamber, "first_half_enemies"):
                        monsters = chamber.first_half_enemies
                    elif b.half == 2 and hasattr(chamber, "second_half_enemies"):
                        monsters = chamber.second_half_enemies
                        
                    text += format_team_node(node_name, getattr(b, "characters", []), monsters) + "\n"
                    
                    n_chars = [_build_char_node_data(c) for c in getattr(b, "characters", [])]
                    n_monsters = [{"name": getattr(m, "name", "Inimigo"), "level": getattr(m, "level", 100)} for m in monsters]
                    teams.append({
                        "name": node_name,
                        "characters": n_chars,
                        "monsters": n_monsters
                    })
                    
            modes.append({
                "id": "spiral_abyss",
                "name": "Abismo Espiral",
                "badge": "Abyss",
                "stage": stage_name,
                "stars": floor.stars,
                "max_stars": floor.max_stars,
                "metric_label": "Estrelas do Piso",
                "metric_value": f"{floor.stars}/{floor.max_stars} ⭐",
                "teams": teams
            })
    except Exception as e:
        print(f"[Aviso] Erro ao extrair Abismo Genshin: {e}")

    # 2. Teatro Imaginário
    try:
        it = await client.get_imaginarium_theater(uid)
        target_data = None
        is_current = True
        
        if hasattr(it, "datas") and it.datas:
            if it.datas[0].has_data:
                target_data = it.datas[0]
                is_current = True
            else:
                for d in it.datas:
                    if d.has_data:
                        target_data = d
                        is_current = False
                        break
                if not target_data and it.datas:
                    target_data = it.datas[0]
        
        if target_data and (target_data.has_data or getattr(target_data, "acts", [])):
            stat = getattr(target_data, "stats", None)
            medals = getattr(stat, "medal_num", 0) if stat else 0
            best_act = getattr(stat, "best_record", 0) if stat else 0
            if not best_act and hasattr(target_data, "acts") and target_data.acts:
                best_act = len(target_data.acts)
                
            diff_obj = getattr(stat, "difficulty", None) if stat else None
            diff_val = getattr(diff_obj, "value", diff_obj)
            
            DIFF_NAMES = {
                1: "Fácil",
                2: "Normal",
                3: "Difícil",
                4: "Visionário",
                5: "Desafio Arcano"
            }
            diff_name = DIFF_NAMES.get(diff_val, f"Dificuldade {diff_val}" if diff_val else "Normal")
            
            DIFF_MAX_ACTS = {
                1: 3,
                2: 6,
                3: 8,
                4: 10,
                5: 10
            }
            max_acts = DIFF_MAX_ACTS.get(diff_val, 10 if best_act > 8 else (8 if best_act > 6 else 6))
            
            season_id = getattr(target_data.schedule, "id", None) if hasattr(target_data, "schedule") and target_data.schedule else None
            season_type = getattr(target_data.schedule, "schedule_type", 1) if hasattr(target_data, "schedule") and target_data.schedule else 1
            season_str = "Temporada Atual" if is_current and season_type == 1 else "Temporada Anterior"
            stage_name = f"{diff_name}" + (f" (Temporada #{season_id})" if season_id else "")
            
            text += f" **Teatro Imaginário** - {stage_name} ({season_str})\n"
            text += f"  • Medalhas: {medals}/{max_acts} | Atos Concluídos: {best_act}/{max_acts}\n"
            
            teams = []
            if hasattr(target_data, "acts") and target_data.acts:
                for act in target_data.acts:
                    act_chars = getattr(act, "characters", [])
                    if not act_chars:
                        continue
                    n_chars = [_build_char_node_data(c) for c in act_chars]
                    medal_mark = " (Medalha ⭐)" if getattr(act, "medal_obtained", False) else ""
                    node_title = f"Ato {act.round_id}{medal_mark}"
                    
                    text += format_team_node(node_title, act_chars, None) + "\n"
                    teams.append({
                        "name": node_title,
                        "characters": n_chars,
                        "monsters": []
                    })
                    
            modes.append({
                "id": "imaginarium_theater",
                "name": "Teatro Imaginário",
                "badge": "Teatro",
                "stage": stage_name,
                "stars": medals,
                "max_stars": max_acts,
                "metric_label": "Atos Concluídos",
                "metric_value": f"{best_act}/{max_acts} Atos ({medals}★)",
                "teams": teams
            })
    except Exception as e:
        print(f"[Aviso] Erro ao extrair Teatro Imaginário Genshin: {e}")

    return (text if modes else "", modes)

async def extrair_endgame_genshin(client: genshin.Client, uid: int) -> str:
    text, _ = await extrair_endgame_genshin_data(client, uid)
    return text


# ==============================================================================
# EXTRAÇÃO ZENLESS ZONE ZERO
# ==============================================================================
async def extrair_endgame_zzz_data(client: genshin.Client, uid: int) -> Tuple[str, List[dict]]:
    """Extrai os dados de Endgame de ZZZ retornando texto formatado e lista estruturada."""
    text = "=== ZENLESS ZONE ZERO - ENDGAME ===\n"
    modes = []

    # 1. Defesa Shiyu (Critical Node / etc)
    try:
        shiyu = await client.get_shiyu_defense(uid)
        floors = getattr(shiyu, "floors", [])
        if not floors and hasattr(shiyu, "datas"):
            floors = getattr(shiyu, "datas", [])
            
        if floors:
            floor = floors[-1] 
            level_name = getattr(floor, "name", getattr(floor, "layer", f"Nó {getattr(floor, 'index', len(floors))}"))
            rating = getattr(floor, "rating", "Concluído")
            
            text += f" **Defesa Shiyu** - {level_name}\n"
            text += f"  • Classificação: {rating}\n"
            
            teams = []
            for n_idx, node_attr in enumerate(["node_1", "node_2"], 1):
                node = getattr(floor, node_attr, None)
                if not node: continue
                
                node_chars = getattr(node, "characters", [])
                if node_chars:
                    char_names = [f"{getattr(c, 'name', '?')} (Nv.{getattr(c, 'level', '?')})" for c in node_chars]
                    text += f"    - **Lado {n_idx}:**\n"
                    text += f"      • Equipe: {', '.join(char_names)}\n"
                    
                n_chars = [_build_char_node_data(c) for c in node_chars]
                bangboo = getattr(node, "bangboo", None)
                if bangboo:
                    b_name = getattr(bangboo, "name", "Bangboo")
                    b_lvl = getattr(bangboo, "level", 60)
                    n_chars.append({
                        "id": str(getattr(bangboo, "id", "")),
                        "name": f"{b_name} (Bangboo)",
                        "level": b_lvl,
                        "icon": getattr(bangboo, "icon", ""),
                        "element": "bangboo",
                        "rarity": getattr(bangboo, "rarity", 4),
                        "rank_str": ""
                    })

                n_monsters = [{"name": getattr(m, "name", "Inimigo"), "level": getattr(m, "level", 60)} for m in getattr(node, "enemies", [])]
                
                teams.append({
                    "name": f"Lado {n_idx}",
                    "characters": n_chars,
                    "monsters": n_monsters
                })

            modes.append({
                "id": "shiyu_defense",
                "name": "Defesa Shiyu (Shiyu Defense)",
                "badge": "Shiyu",
                "stage": level_name,
                "stars": None,
                "max_stars": None,
                "metric_label": "Classificação",
                "metric_value": rating if rating and rating != "None" else "Concluído",
                "teams": teams
            })
    except Exception as e:
        print(f"[Aviso] Erro ao extrair Defesa Shiyu ZZZ: {e}")

    return (text if modes else "", modes)

async def extrair_endgame_zzz(client: genshin.Client, uid: int) -> str:
    text, _ = await extrair_endgame_zzz_data(client, uid)
    return text


# ==============================================================================
# PARSER ROBUSTO DE MARKDOWN (RETROCOMPATIBILIDADE PARA DADOS JÁ SALVOS)
# ==============================================================================
def parse_endgame_from_markdown(game_id: str, md_text: str, roster_list: List[dict] = None) -> List[dict]:
    """
    Analisa os blocos de texto salvos em roster_<game>.md e converte em
    uma lista estruturada de modos de endgame enriquecida com os dados do Roster.
    """
    if not md_text:
        return []
        
    game_id_clean = (game_id or "hsr").lower().strip()
    roster_map = {}
    if roster_list:
        for c in roster_list:
            name = c.get("name", "")
            if name:
                roster_map[name.lower()] = c

    modes = []

    # 1. HONKAI: STAR RAIL
    if game_id_clean == "hsr":
        block_m = re.search(r'===\s*HONKAI:\s*STAR RAIL\s*-\s*ENDGAME\s*===(.*?)(?=\n## |\Z)', md_text, re.DOTALL | re.I)
        if not block_m:
            return []
        block = block_m.group(1)
        
        # Divide por modos (iniciados com **Caos / **Ficção / **Sombra)
        mode_sections = re.split(r'\n\s*\*\*', block)
        for sec in mode_sections:
            if not sec.strip(): continue
            full_sec = '**' + sec if not sec.startswith('**') else sec
            
            m_header = re.search(r'\*\*(.*?)\*\*\s*-\s*(.*?)\n', full_sec)
            if not m_header:
                m_header = re.search(r'\*\*(.*?)\*\*\n', full_sec)
                if not m_header: continue
                m_name = m_header.group(1).strip()
                stage = ""
            else:
                m_name = m_header.group(1).strip()
                stage = m_header.group(2).strip()

            mode_id = "moc" if "caos" in m_name.lower() or "moc" in m_name.lower() else (
                "pure_fiction" if "ficção" in m_name.lower() or "fiction" in m_name.lower() else "apocalyptic_shadow"
            )
            badge = "MoC" if mode_id == "moc" else ("PF" if mode_id == "pure_fiction" else "AS")
            
            stars_m = re.search(r'Estrelas:\s*(\d+)/(\d+)', full_sec)
            stars = int(stars_m.group(1)) if stars_m else None
            max_stars = int(stars_m.group(2)) if stars_m else None
            
            rounds_m = re.search(r'Rodadas Utilizadas:\s*(\d+)', full_sec)
            score_m = re.search(r'Pontuação:\s*(\d+)', full_sec)
            
            metric_label = "Rodadas Utilizadas" if rounds_m else ("Pontuação" if score_m else "")
            metric_val = rounds_m.group(1) if rounds_m else (
                f"{int(score_m.group(1)):,}".replace(",", ".") if score_m else ""
            )
            
            teams = []
            side_blocks = re.findall(r'-\s*\*\*(Lado \d+|Primeira Metade|Segunda Metade):\*\*(.*?)(?=\n\s*-\s*\*\*|\Z)', full_sec, re.DOTALL)
            for side_name, side_content in side_blocks:
                team_chars = []
                team_m = re.search(r'Equipe:\s*(.*?)(?=\n|$)', side_content)
                if team_m:
                    for ci in team_m.group(1).split(','):
                        ci = ci.strip()
                        if not ci: continue
                        cm = re.search(r'^(.*?)\s*\(Nv\.(\d+)\)$', ci)
                        if cm:
                            cname, clvl = cm.group(1).strip(), int(cm.group(2))
                        else:
                            cname, clvl = ci, 80
                        
                        c_meta = roster_map.get(cname.lower(), {})
                        team_chars.append({
                            "id": c_meta.get("id", ""),
                            "name": cname,
                            "level": clvl,
                            "element": c_meta.get("element", "fire"),
                            "rarity": c_meta.get("rarity", 5),
                            "icon": c_meta.get("icon", ""),
                            "rank_str": c_meta.get("rank_str", "E0")
                        })
                        
                teams.append({
                    "name": side_name.strip(),
                    "characters": team_chars,
                    "monsters": []
                })
                
            modes.append({
                "id": mode_id,
                "name": m_name,
                "badge": badge,
                "stage": stage,
                "stars": stars,
                "max_stars": max_stars,
                "metric_label": metric_label,
                "metric_value": metric_val,
                "teams": teams
            })

    # 2. GENSHIN IMPACT
    elif game_id_clean == "genshin":
        block_m = re.search(r'===\s*GENSHIN IMPACT\s*-\s*ENDGAME\s*===(.*?)(?=\n## |\Z)', md_text, re.DOTALL | re.I)
        if not block_m:
            return []
        block = block_m.group(1)

        # 2a. Abismo Espiral
        abyss_m = re.search(r'\*\*Abismo Espiral\*\*\s*-\s*(.*?)\n\s*•\s*Estrelas do Piso:\s*(\d+)/(\d+)(.*?)(?=\n\s*\*\*|\Z)', block, re.DOTALL | re.I)
        if abyss_m:
            stage = abyss_m.group(1).strip()
            stars = int(abyss_m.group(2))
            max_stars = int(abyss_m.group(3))
            abyss_content = abyss_m.group(4)
            
            teams = []
            sides = re.findall(r'-\s*\*\*(Primeira Metade|Segunda Metade|Lado \d+):\*\*(.*?)(?=\n\s*-\s*\*\*|\Z)', abyss_content, re.DOTALL)
            for side_name, side_content in sides:
                team_chars = []
                eq_m = re.search(r'Equipe:\s*(.*?)(?=\n|$)', side_content)
                if eq_m:
                    for ci in eq_m.group(1).split(','):
                        ci = ci.strip()
                        if not ci: continue
                        cm = re.search(r'^(.*?)\s*\(Nv\.(\d+)\)$', ci)
                        if cm:
                            cname, clvl = cm.group(1).strip(), int(cm.group(2))
                        else:
                            cname, clvl = ci, 90
                        c_meta = roster_map.get(cname.lower(), {})
                        team_chars.append({
                            "id": c_meta.get("id", ""),
                            "name": cname,
                            "level": clvl,
                            "element": c_meta.get("element", "Anemo"),
                            "rarity": c_meta.get("rarity", 5),
                            "icon": c_meta.get("icon", ""),
                            "rank_str": c_meta.get("rank_str", "C0")
                        })
                monsters = []
                inim_m = re.search(r'Inimigos:\s*(.*?)(?=\n|$)', side_content)
                if inim_m:
                    for mi in inim_m.group(1).split(','):
                        mi = mi.strip()
                        if not mi: continue
                        mm = re.search(r'^(.*?)\s*\(Nv\.(\d+)\)$', mi)
                        if mm:
                            monsters.append({"name": mm.group(1).strip(), "level": int(mm.group(2))})
                        else:
                            monsters.append({"name": mi, "level": 100})
                            
                teams.append({
                    "name": side_name.strip(),
                    "characters": team_chars,
                    "monsters": monsters
                })
                
            modes.append({
                "id": "spiral_abyss",
                "name": "Abismo Espiral",
                "badge": "Abyss",
                "stage": stage,
                "stars": stars,
                "max_stars": max_stars,
                "metric_label": "Estrelas do Piso",
                "metric_value": f"{stars}/{max_stars} ⭐",
                "teams": teams
            })

        # 2b. Teatro Imaginário
        it_m = re.search(r'\*\*Teatro Imaginário\*\*\s*-\s*(.*?)\n\s*•\s*Medalhas:\s*(\d+)/(\d+)\s*\|\s*Atos Concluídos:\s*(\d+)/(\d+)(.*?)(?=\n\s*\*\*|\Z)', block, re.DOTALL | re.I)
        if it_m:
            stage = it_m.group(1).strip()
            medals = int(it_m.group(2))
            max_medals = int(it_m.group(3))
            acts = int(it_m.group(4))
            max_acts = int(it_m.group(5))
            it_content = it_m.group(6)
            
            teams = []
            act_nodes = re.findall(r'-\s*\*\*(Ato \d+.*?):\*\*(.*?)(?=\n\s*-\s*\*\*|\Z)', it_content, re.DOTALL)
            for act_name, act_content in act_nodes:
                team_chars = []
                eq_m = re.search(r'Equipe:\s*(.*?)(?=\n|$)', act_content)
                if eq_m:
                    for ci in eq_m.group(1).split(','):
                        ci = ci.strip()
                        if not ci: continue
                        cm = re.search(r'^(.*?)\s*\(Nv\.(\d+)\)$', ci)
                        if cm: cname, clvl = cm.group(1).strip(), int(cm.group(2))
                        else: cname, clvl = ci, 90
                        c_meta = roster_map.get(cname.lower(), {})
                        team_chars.append({
                            "id": c_meta.get("id", ""),
                            "name": cname,
                            "level": clvl,
                            "element": c_meta.get("element", "Anemo"),
                            "rarity": c_meta.get("rarity", 5),
                            "icon": c_meta.get("icon", ""),
                            "rank_str": c_meta.get("rank_str", "C0")
                        })
                teams.append({
                    "name": act_name.strip(),
                    "characters": team_chars,
                    "monsters": []
                })
                
            modes.append({
                "id": "imaginarium_theater",
                "name": "Teatro Imaginário",
                "badge": "Teatro",
                "stage": stage,
                "stars": medals,
                "max_stars": max_acts,
                "metric_label": "Atos Concluídos",
                "metric_value": f"{acts}/{max_acts} Atos ({medals}★)",
                "teams": teams
            })
        else:
            # Fallback para formato antigo ou simplificado
            old_it_m = re.search(r'\*\*Teatro Imaginário\*\*(.*?)(?=\n\s*\*\*|\Z)', block, re.DOTALL | re.I)
            if old_it_m:
                it_c = old_it_m.group(1)
                medals_m = re.search(r'Medalhas:\s*([^\s\|]+)', it_c)
                acts_m = re.search(r'Atos Concluídos:\s*([^\s\n\|]+)', it_c)
                medals_str = medals_m.group(1) if medals_m else "?"
                acts_str = acts_m.group(1) if acts_m else "?"
                medals_val = int(medals_str) if medals_str.isdigit() else None
                
                teams = []
                dest_m = re.search(r'Personagens Principais/Destaques:\s*(.*?)(?=\n|$)', it_c)
                if dest_m:
                    dest_chars = []
                    for ci in dest_m.group(1).split(','):
                        ci = ci.strip()
                        if not ci: continue
                        cm = re.search(r'^(.*?)\s*\(Nv\.(\d+)\)$', ci)
                        if cm: cname, clvl = cm.group(1).strip(), int(cm.group(2))
                        else: cname, clvl = ci, 90
                        c_meta = roster_map.get(cname.lower(), {})
                        dest_chars.append({
                            "id": c_meta.get("id", ""),
                            "name": cname,
                            "level": clvl,
                            "element": c_meta.get("element", "Anemo"),
                            "rarity": c_meta.get("rarity", 5),
                            "icon": c_meta.get("icon", ""),
                            "rank_str": c_meta.get("rank_str", "C0")
                        })
                    teams.append({
                        "name": "Elenco Principal / Destaques",
                        "characters": dest_chars,
                        "monsters": []
                    })
                    
                modes.append({
                    "id": "imaginarium_theater",
                    "name": "Teatro Imaginário",
                    "badge": "Teatro",
                    "stage": "Temporada Atual",
                    "stars": medals_val,
                    "max_stars": None,
                    "metric_label": "Progresso",
                    "metric_value": f"{acts_str} Atos ({medals_str} Medalhas)" if acts_str != "?" and acts_str != "None" else "Concluído",
                    "teams": teams
                })

    # 3. ZENLESS ZONE ZERO
    elif game_id_clean == "zzz":
        block_m = re.search(r'===\s*ZENLESS ZONE ZERO\s*-\s*ENDGAME\s*===(.*?)(?=\n## |\Z)', md_text, re.DOTALL | re.I)
        if not block_m:
            return []
        block = block_m.group(1)
        
        shiyu_m = re.search(r'\*\*Defesa Shiyu\*\*\s*-\s*(.*?)\n\s*•\s*Classificação:\s*(.*?)(?=\n|\Z)(.*?)(?=\n\s*\*\*|\Z)', block, re.DOTALL | re.I)
        if shiyu_m:
            stage = shiyu_m.group(1).strip()
            rating = shiyu_m.group(2).strip()
            rest_c = shiyu_m.group(3) if len(shiyu_m.groups()) >= 3 else ""
            
            teams = []
            agents_m = re.search(r'Agentes Utilizados:\s*(.*?)(?=\n|$)', rest_c)
            if agents_m:
                team_chars = []
                for ci in agents_m.group(1).split(','):
                    ci = ci.strip()
                    if not ci: continue
                    cm = re.search(r'^(.*?)\s*\(Nv\.(\d+)\)$', ci)
                    if cm: cname, clvl = cm.group(1).strip(), int(cm.group(2))
                    else: cname, clvl = ci, 60
                    c_meta = roster_map.get(cname.lower(), {})
                    team_chars.append({
                        "id": c_meta.get("id", ""),
                        "name": cname,
                        "level": clvl,
                        "element": c_meta.get("element", "physical"),
                        "rarity": c_meta.get("rarity", 5),
                        "icon": c_meta.get("icon", ""),
                        "rank_str": c_meta.get("rank_str", "M0")
                    })
                teams.append({
                    "name": "Agentes da Rotação",
                    "characters": team_chars,
                    "monsters": []
                })

            # Se não tem agentes no bloco antigo e o rating for None, ainda registramos com estado limpo
            modes.append({
                "id": "shiyu_defense",
                "name": "Defesa Shiyu (Shiyu Defense)",
                "badge": "Shiyu",
                "stage": stage if stage != "?" else "Nó Crítico",
                "stars": None,
                "max_stars": None,
                "metric_label": "Classificação",
                "metric_value": rating if rating and rating != "None" else "Aguardando sincronização",
                "teams": teams
            })

    return modes


# ==============================================================================
# CONTEXTO RAG PARA LLM
# ==============================================================================
async def gerar_contexto_endgame_rag(client: genshin.Client, uid_hsr: Optional[int] = None, uid_genshin: Optional[int] = None, uid_zzz: Optional[int] = None) -> str:
    """
    Função principal que orquestra a extração do endgame real de todos os jogos, 
    focando estritamente nos últimos andares/estágios para alimentar a LLM.
    """
    blocos = []
    
    if uid_hsr:
        hsr_data = await extrair_endgame_hsr(client, uid_hsr)
        if hsr_data: blocos.append(hsr_data)
        
    if uid_genshin:
        gen_data = await extrair_endgame_genshin(client, uid_genshin)
        if gen_data: blocos.append(gen_data)
        
    if uid_zzz:
        zzz_data = await extrair_endgame_zzz(client, uid_zzz)
        if zzz_data: blocos.append(zzz_data)
        
    return "\n".join(blocos)
