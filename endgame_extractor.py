import asyncio
import genshin
from typing import Optional, Dict

def format_team_node(node_name: str, characters: list, monsters: list = None, char_map: Dict[str, str] = None) -> str:
    """Formata os detalhes de uma metade/nó do endgame."""
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


async def extrair_endgame_hsr(client: genshin.Client, uid: int) -> str:
    text = "=== HONKAI: STAR RAIL - ENDGAME ===\n"
    has_data = False
    
    # Busca nomes de personagens para mapeamento
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
            has_data = True
            floor = moc.floors[0]
            # Verifica se tem node_3 (novo formato com 4 estrelas / 3 times)
            has_node_3 = hasattr(floor, 'node_3') and floor.node_3 is not None
            max_stars = 4 if has_node_3 else 3
            
            text += f"🏆 **Caos da Memória (MoC)** - {floor.name}\n"
            text += f"  • Estrelas: {getattr(floor, 'star_num', getattr(floor, 'stars', '?'))}/{max_stars} | Rodadas Utilizadas: {floor.round_num}\n"
            text += format_team_node("Lado 1", getattr(floor.node_1, "avatars", []), getattr(floor.node_1, "monsters", []), char_map) + "\n"
            text += format_team_node("Lado 2", getattr(floor.node_2, "avatars", []), getattr(floor.node_2, "monsters", []), char_map) + "\n"
            if has_node_3:
                text += format_team_node("Lado 3", getattr(floor.node_3, "avatars", []), getattr(floor.node_3, "monsters", []), char_map) + "\n"
    except Exception as e:
        pass

    # 2. Ficção Pura (Pure Fiction)
    try:
        pf = await client.get_starrail_pure_fiction(uid)
        if pf.floors:
            has_data = True
            floor = pf.floors[0]
            has_node_3 = hasattr(floor, 'node_3') and floor.node_3 is not None
            max_stars = 4 if has_node_3 else 3
            
            text += f"🎭 **Ficção Pura** - {floor.name}\n"
            text += f"  • Estrelas: {getattr(floor, 'star_num', getattr(floor, 'stars', '?'))}/{max_stars} | Pontuação: {floor.score}\n"
            text += format_team_node("Lado 1", getattr(floor.node_1, "avatars", []), getattr(floor.node_1, "monsters", []), char_map) + "\n"
            text += format_team_node("Lado 2", getattr(floor.node_2, "avatars", []), getattr(floor.node_2, "monsters", []), char_map) + "\n"
            if has_node_3:
                text += format_team_node("Lado 3", getattr(floor.node_3, "avatars", []), getattr(floor.node_3, "monsters", []), char_map) + "\n"
    except Exception as e:
        pass

    # 3. Sombra Apocalíptica (Apocalyptic Shadow)
    try:
        apc = await client.get_starrail_apc_shadow(uid)
        if apc.floors:
            has_data = True
            floor = apc.floors[0]
            has_node_3 = hasattr(floor, 'node_3') and floor.node_3 is not None
            max_stars = 4 if has_node_3 else 3
            
            text += f"🌑 **Sombra Apocalíptica** - {floor.name}\n"
            text += f"  • Estrelas: {getattr(floor, 'star_num', getattr(floor, 'stars', '?'))}/{max_stars} | Pontuação: {floor.score}\n"
            text += format_team_node("Lado 1", getattr(floor.node_1, "avatars", []), getattr(floor.node_1, "monsters", []), char_map) + "\n"
            text += format_team_node("Lado 2", getattr(floor.node_2, "avatars", []), getattr(floor.node_2, "monsters", []), char_map) + "\n"
            if has_node_3:
                text += format_team_node("Lado 3", getattr(floor.node_3, "avatars", []), getattr(floor.node_3, "monsters", []), char_map) + "\n"
    except Exception as e:
        pass
        
    return text if has_data else ""


async def extrair_endgame_genshin(client: genshin.Client, uid: int) -> str:
    text = "=== GENSHIN IMPACT - ENDGAME ===\n"
    has_data = False

    # 1. Abismo Espiral
    try:
        abyss = await client.get_genshin_spiral_abyss(uid)
        if abyss.floors:
            has_data = True
            floor = abyss.floors[-1]
            chamber = floor.chambers[-1] if floor.chambers else None
            
            text += f"🌌 **Abismo Espiral** - Piso {floor.floor} (Câmara {chamber.chamber if chamber else '?'})\n"
            text += f"  • Estrelas do Piso: {floor.stars}/{floor.max_stars}\n"
            if chamber and chamber.battles:
                for b in chamber.battles:
                    node_name = "Primeira Metade" if b.half == 1 else "Segunda Metade"
                    
                    # Puxa os inimigos da metade correspondente, se existirem na câmara
                    monsters = []
                    if b.half == 1 and hasattr(chamber, "first_half_enemies"):
                        monsters = chamber.first_half_enemies
                    elif b.half == 2 and hasattr(chamber, "second_half_enemies"):
                        monsters = chamber.second_half_enemies
                        
                    text += format_team_node(node_name, getattr(b, "characters", []), monsters) + "\n"
    except Exception as e:
        pass

    # 2. Teatro Imaginário
    try:
        it = await client.get_imaginarium_theater(uid)
        if hasattr(it, "datas") and it.datas:
            # Pega a temporada atual/mais recente
            current = it.datas[0]
            has_data = True
            text += f"🎭 **Teatro Imaginário**\n"
            text += f"  • Medalhas: {getattr(current, 'medal_num', '?')} | Atos Concluídos: {getattr(current, 'max_round_id', '?')}\n"
            # O Teatro tem muitos atos, pegamos apenas o lineup geral ou os favoritos se disponíveis
            favs = getattr(current, "favorite_characters", [])
            if favs:
                char_names = [f"{getattr(c, 'name', '?')} (Nv.{getattr(c, 'level', '?')})" for c in favs]
                text += f"    - **Personagens Principais/Destaques:** {', '.join(char_names)}\n"
    except Exception as e:
        pass

    return text if has_data else ""


async def extrair_endgame_zzz(client: genshin.Client, uid: int) -> str:
    text = "=== ZENLESS ZONE ZERO - ENDGAME ===\n"
    has_data = False

    # 1. Defesa Shiyu (Critical Node / etc)
    try:
        shiyu = await client.get_shiyu_defense(uid)
        # O shiyu normalmente guarda os nós no 'brief_info' ou similar se não houver um array direto
        # Caso tenha floors no atributo 'datas' ou similar
        nodes = getattr(shiyu, "datas", [])
        if not nodes and hasattr(shiyu, "brief_info"):
            nodes = [shiyu.brief_info] # Fallback
            
        if nodes:
            has_data = True
            node = nodes[-1] 
            level = getattr(node, "level", getattr(node, "layer", "?"))
            text += f"📺 **Defesa Shiyu** - Nó/Andar {level}\n"
            rating = getattr(node, "rating", "Concluído")
            text += f"  • Classificação: {rating}\n"
            
            # Puxa times se disponíveis (A API do ZZZ é mais esparsa em detalhes de time dependendo da rotação)
            avatars = getattr(node, "avatars", [])
            if avatars:
                char_names = [f"{getattr(c, 'name', '?')} (Nv.{getattr(c, 'level', '?')})" for c in avatars]
                text += f"    - **Agentes Utilizados:** {', '.join(char_names)}\n"
    except Exception as e:
        pass

    return text if has_data else ""


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
