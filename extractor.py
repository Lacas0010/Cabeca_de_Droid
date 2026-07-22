import os
import re
import json
import requests
import asyncio
import genshin
import endgame_extractor

# Dicionários de mapeamento para traduzir Elementos e Caminhos para Português em HSR
ELEMENT_MAP = {
    "Ice": "Gelo",
    "Fire": "Fogo",
    "Wind": "Vento",
    "Lightning": "Raio",
    "Physical": "Físico",
    "Quantum": "Quântico",
    "Imaginary": "Imaginário",
    "Gelo": "Gelo",
    "Fogo": "Fogo",
    "Vento": "Vento",
    "Raio": "Raio",
    "Físico": "Físico",
    "Quântico": "Quântico",
    "Imaginário": "Imaginário"
}

PATH_MAP = {
    "DESTRUCTION": "Destruição",
    "THE_HUNT": "Caça",
    "ERUDITION": "Erudição",
    "HARMONY": "Harmonia",
    "NIHILITY": "Inexistência",
    "PRESERVATION": "Preservação",
    "ABUNDANCE": "Abundância",
    "REMEMBRANCE": "Recordação",
    "ELATION": "Euforia",
    "Destruction": "Destruição",
    "Hunt": "Caça",
    "The Hunt": "Caça",
    "Erudition": "Erudição",
    "Harmony": "Harmonia",
    "Nihility": "Inexistência",
    "Preservation": "Preservação",
    "Abundance": "Abundância",
    "Remembrance": "Recordação",
    "Elation": "Euforia"
}

class BaseExtractor:
    def __init__(self, cookies: dict):
        """
        Classe base para os extratores de jogos da HoYoVerse usando a biblioteca genshin.py.
        Configura o cliente com cookies e o idioma em português (pt-pt) para evitar erros da API.
        """
        self.client = genshin.Client(cookies=cookies, lang="pt-pt")

    async def get_account(self, game_biz_prefix: str) -> genshin.models.GenshinAccount:
        """
        Busca a primeira conta vinculada que corresponda ao prefixo do game_biz.
        Exemplos de prefixos:
            - "hkrpg" para Honkai: Star Rail
            - "hk4e" para Genshin Impact
            - "nap" para Zenless Zone Zero (ZZZ)
        """
        try:
            accounts = await self.client.get_game_accounts()
        except Exception as e:
            raise Exception(f"Erro ao obter contas vinculadas no HoYoLAB: {e}")
            
        for acc in accounts:
            if acc.game_biz.startswith(game_biz_prefix):
                return acc
        return None


class HSRExtractor(BaseExtractor):
    def __init__(self, cookies: dict):
        super().__init__(cookies)
        self.client.game = genshin.Game.STARRAIL

    async def extrair_e_salvar(self, filename: str = "hsr/roster_hsr.md") -> str:
        """
        Busca os dados de Honkai: Star Rail e gera um arquivo Markdown formatado.
        Mantém compatibilidade total com a lógica do extrator antigo.
        """
        hsr_account = await self.get_account("hkrpg")
        if not hsr_account:
            raise Exception("Nenhuma conta ativa de Honkai: Star Rail encontrada vinculada a este perfil HoYoLAB.")
            
        uid = hsr_account.uid
        
        # 2. Obtém os dados de Battle Chronicle e a lista detalhada de personagens
        try:
            user_data = await self.client.get_starrail_user(uid)
            characters_data = await self.client.get_starrail_characters(uid)
        except Exception as e:
            raise Exception(
                f"Não foi possível obter dados para o UID {uid}.\n"
                f"Certifique-se de que o perfil no HoYoLAB ('Registro de Batalha') está público nas configurações de privacidade."
            )
        
        # 2.5. Coleta e traduz os nomes dos conjuntos de relíquias via API do HoYoWiki
        wiki_ids = set()
        for char in characters_data.avatar_list:
            relics_list = []
            if hasattr(char, "relics") and char.relics:
                relics_list.extend(char.relics)
            if hasattr(char, "ornaments") and char.ornaments:
                relics_list.extend(char.ornaments)
            for r in relics_list:
                if hasattr(r, "wiki") and r.wiki:
                    match = re.search(r'/entry/(\d+)', r.wiki)
                    if match:
                        wiki_ids.add(match.group(1))

        wiki_map = {}
        if wiki_ids:
            ids_str = ",".join(wiki_ids)
            url = f"https://sg-act-public-api-static.hoyolab.com/hoyowiki/hsr/wapi/entry_pages?str_entry_page_ids={ids_str}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'x-rpc-language': 'pt-pt',
                'x-rpc-wiki_app': 'hsr'
            }
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    res_data = res.json()
                    if res_data.get("retcode") == 0 and "data" in res_data:
                        for item in res_data["data"].get("entry_pages", []):
                            wiki_map[str(item["id"])] = item["name"]
            except Exception as err:
                print(f"Erro ao traduzir conjuntos de relíquias via HoYoWiki: {err}")

        # 3. Formata e gera o conteúdo em Markdown
        stats = user_data.stats
        info = user_data.info
        
        lines = []
        lines.append("# Relatório de Personagens - Honkai: Star Rail")
        lines.append(f"**Usuário:** {info.nickname} (UID: {uid})")
        lines.append(f"**Nível de Desbravamento:** {info.level}")
        lines.append(f"**Dias Ativos:** {stats.active_days}")
        lines.append(f"**Personagens Obtidos:** {stats.avatar_num}")
        lines.append(f"**Conquistas Desbloqueadas:** {stats.achievement_num}")
        lines.append(f"**Baús Abertos:** {stats.chest_num}")
        lines.append(f"**Salão Esquecido:** {stats.abyss_process}")
        
        try:
            endgame_text = await endgame_extractor.extrair_endgame_hsr(self.client, uid)
            if endgame_text:
                lines.append("")
                lines.append(endgame_text)
        except Exception as e:
            print(f"Aviso: Não foi possível puxar dados de Endgame HSR: {e}")

        lines.append("")
        lines.append("## Detalhes do Roster de Personagens")
        lines.append("")
        lines.append("| Personagem | Nível | Raridade | Eidolon | Caminho | Elemento |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        # Ordena por raridade (decrescente) e nível (decrescente)
        for char in sorted(characters_data.avatar_list, key=lambda c: (c.rarity, c.level), reverse=True):
            stars = "⭐" * char.rarity
            eidolon = f"E{char.rank}"
            
            # Tradução e tratamento do Caminho
            p_name = char.path.name if hasattr(char.path, "name") else str(char.path)
            path = PATH_MAP.get(p_name, p_name)
            
            # Tradução e tratamento do Elemento
            e_name = char.element.name if hasattr(char.element, "name") else str(char.element)
            element = ELEMENT_MAP.get(e_name, e_name)
            
            lines.append(f"| {char.name} | {char.level} | {stars} | {eidolon} | {path} | {element} |")
            
        # Seção de Builds para Personagens Nível 80
        lines.append("")
        lines.append("## Detalhes de Builds (Personagens Nv. 80)")
        lines.append("")
        
        for char in sorted(characters_data.avatar_list, key=lambda c: (c.rarity, c.level), reverse=True):
            if char.level == 80:
                # 1. Cone de Luz
                if char.equip:
                    equip_text = f"{char.equip.name} (Sobreposição {char.equip.rank})"
                else:
                    equip_text = "Nenhum cone de luz equipado"
                
                # 2. Relíquias e Ornamentos
                relics_list = []
                try:
                    detail = await self.client.get_starrail_character_details(char.id)
                    if hasattr(detail, "relics") and detail.relics:
                        relics_list.extend(detail.relics)
                    if hasattr(detail, "ornaments") and detail.ornaments:
                        relics_list.extend(detail.ornaments)
                except Exception:
                    if hasattr(char, "relics") and char.relics:
                        relics_list.extend(char.relics)
                    if hasattr(char, "ornaments") and char.ornaments:
                        relics_list.extend(char.ornaments)
                
                set_counts = {}
                for r in relics_list:
                    # Tenta extrair o nome do conjunto amigável via mapeamento do HoYoWiki
                    set_name = r.name  # Fallback
                    if hasattr(r, "wiki") and r.wiki:
                        match = re.search(r'/entry/(\d+)', r.wiki)
                        if match:
                            w_id = match.group(1)
                            set_name = wiki_map.get(w_id, f"Conjunto {w_id}")
                    set_counts[set_name] = set_counts.get(set_name, 0) + 1
                
                set_strings = []
                for s_name, count in sorted(set_counts.items(), key=lambda x: x[1], reverse=True):
                    set_strings.append(f"{s_name} ({count} peças)")
                relics_text = " + ".join(set_strings) if set_strings else "Nenhuma relíquia equipada"
                
                # 3. Status Finais
                properties_list = []
                if hasattr(char, "properties") and char.properties:
                    for prop in char.properties:
                        name = prop.info.name if (prop.info and prop.info.name) else "Atributo"
                        val = getattr(prop, "display_value", getattr(prop, "final", ""))
                        if name and val:
                            properties_list.append(f"{name}: {val}")
                properties_text = ", ".join(properties_list) if properties_list else "Status não disponíveis"
                
                # Escreve o bloco do personagem em linguagem natural para LLMs
                eidolon = f"E{char.rank}"
                lines.append(f"**Personagem:** {char.name} | **Nível:** {char.level} | **Eidolon:** {eidolon}")
                lines.append(f"- **Cone de Luz:** {equip_text}")
                lines.append(f"- **Relíquias:** {relics_text}")
                lines.append(f"- **Status Finais:** {properties_text}")
                
                if relics_list:
                    lines.append("\n  **Detalhamento de Peças (Substatus):**")
                    for relic in relics_list:
                        main_prop = getattr(relic, "main_property", getattr(relic, "main_stat", None))
                        if main_prop:
                            m_name = getattr(getattr(main_prop, "info", main_prop), "name", getattr(main_prop, "property_name", getattr(main_prop, "type", "Atributo")))
                            m_val = getattr(main_prop, "value", getattr(main_prop, "display_value", getattr(main_prop, "stat_value", "")))
                            main_stat = f"{m_name} ({m_val})"
                        else:
                            main_stat = "Desconhecido"
                            
                        substats_str = "Sem substatus"
                        sub_props = getattr(relic, "properties", getattr(relic, "sub_properties", getattr(relic, "sub_stats", getattr(relic, "sub_property_list", []))))
                        if sub_props:
                            subs = []
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                subs.append(f"{s_name}: {s_val}")
                            substats_str = ", ".join(subs)
                        
                        hsr_slot_map = {1: "Cabeça", 2: "Mãos", 3: "Corpo", 4: "Pés", 5: "Esfera Plana", 6: "Corda de Ligação"}
                        pos = getattr(relic, 'pos', '?')
                        pos_name = hsr_slot_map.get(pos, f"Slot {pos}")
                        lines.append(f"  • [{pos_name}] {relic.name}")
                        lines.append(f"    - Principal: {main_stat}")
                        lines.append(f"    - Substatus: {substats_str}")
                        
                lines.append("")
                lines.append("---")
                lines.append("")

        # Salva dados estruturados em JSON para a Galeria Visual da UI
        roster_json_path = "hsr/roster_data_hsr.json"
        try:
            char_json_list = []
            hsr_slot_map = {1: "Cabeça", 2: "Mãos", 3: "Corpo", 4: "Pés", 5: "Esfera Plana", 6: "Corda de Ligação"}
            for char in sorted(characters_data.avatar_list, key=lambda c: (c.rarity, c.level), reverse=True):
                e_name = char.element.name if hasattr(char.element, "name") else str(char.element)
                element = ELEMENT_MAP.get(e_name, e_name)
                
                w_info = {}
                if hasattr(char, "equip") and char.equip:
                    w_info = {
                        "name": char.equip.name,
                        "level": getattr(char.equip, "level", 80),
                        "rank": getattr(char.equip, "rank", 1),
                        "icon": getattr(char.equip, "icon", "")
                    }
                    
                relics_json = []
                r_list = []
                if hasattr(char, "relics") and char.relics: r_list.extend(char.relics)
                if hasattr(char, "ornaments") and char.ornaments: r_list.extend(char.ornaments)
                for r in r_list:
                    pos = getattr(r, 'pos', '?')
                    pos_name = hsr_slot_map.get(pos, f"Slot {pos}")
                    main_prop = getattr(r, "main_property", getattr(r, "main_stat", None))
                    main_stat = "Desconhecido"
                    if main_prop:
                        m_name = getattr(getattr(main_prop, "info", main_prop), "name", getattr(main_prop, "property_name", getattr(main_prop, "type", "Atributo")))
                        m_val = getattr(main_prop, "value", getattr(main_prop, "display_value", getattr(main_prop, "stat_value", "")))
                        main_stat = f"{m_name} ({m_val})"
                        
                    sub_props = getattr(r, "properties", getattr(r, "sub_properties", getattr(r, "sub_stats", getattr(r, "sub_property_list", []))))
                    subs = []
                    if sub_props:
                        for sub in sub_props:
                            s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                            s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                            subs.append(f"{s_name}: {s_val}")
                    relics_json.append({
                        "name": r.name,
                        "icon": getattr(r, "icon", ""),
                        "slot": pos_name,
                        "main": main_stat,
                        "sub": ", ".join(subs) if subs else "Sem substatus"
                    })
                    
                char_json_list.append({
                    "name": char.name,
                    "level": char.level,
                    "rarity": char.rarity,
                    "rank_str": f"E{char.rank}",
                    "element": element,
                    "icon": getattr(char, "icon", getattr(char, "image", "")),
                    "weapon": w_info,
                    "relics": relics_json
                })
            os.makedirs(os.path.dirname(roster_json_path) or ".", exist_ok=True)
            with open(roster_json_path, "w", encoding="utf-8") as jf:
                json.dump(char_json_list, jf, ensure_ascii=False, indent=2)
        except Exception as json_err:
            print(f"Aviso ao salvar roster_data_hsr.json: {json_err}")

        markdown_content = "\n".join(lines)
        
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filename


class GenshinExtractor(BaseExtractor):
    def __init__(self, cookies: dict):
        super().__init__(cookies)
        self.client.game = genshin.Game.GENSHIN

    async def extrair_e_salvar(self, filename: str = "genshin/roster_genshin.md") -> str:
        """
        Busca os dados de Genshin Impact e gera um arquivo Markdown formatado.
        """
        genshin_acc = await self.get_account("hk4e")
        if not genshin_acc:
            raise Exception("Nenhuma conta ativa de Genshin Impact encontrada vinculada a este perfil HoYoLAB.")
            
        uid = genshin_acc.uid
        
        try:
            detail = await self.client.get_genshin_detailed_characters(uid)
            chars = detail.characters
        except Exception as e:
            raise Exception(
                f"Não foi possível obter dados detalhados para o UID {uid}.\n"
                f"Certifique-se de que o Registro de Batalha de Genshin está público nas configurações de privacidade."
            )
            
        lines = []
        lines.append("# Relatório de Personagens - Genshin Impact")
        lines.append(f"**UID:** {uid}")
        lines.append(f"**Rank de Aventura:** {genshin_acc.level}")
        lines.append(f"**Personagens Obtidos:** {len(chars)}")
        
        try:
            endgame_text = await endgame_extractor.extrair_endgame_genshin(self.client, uid)
            if endgame_text:
                lines.append("")
                lines.append(endgame_text)
        except Exception as e:
            print(f"Aviso: Não foi possível puxar dados de Endgame Genshin: {e}")
            
        lines.append("")
        lines.append("## Detalhes do Roster de Personagens")
        lines.append("")
        lines.append("| Personagem | Nível | Raridade | Constelação | Arma | Artefatos |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for char in sorted(chars, key=lambda c: (c.rarity, c.level), reverse=True):
            stars = "⭐" * char.rarity
            weapon = f"{char.weapon.name} (Nv. {char.weapon.level}, R{char.weapon.refinement})" if char.weapon else "Nenhuma"
            
            # Conta conjuntos de artefatos
            art_sets = {}
            for art in char.artifacts:
                if hasattr(art, "set") and art.set:
                    art_sets[art.set.name] = art_sets.get(art.set.name, 0) + 1
                    
            art_strings = []
            for s_name, count in sorted(art_sets.items(), key=lambda x: x[1], reverse=True):
                art_strings.append(f"{s_name} ({count} peças)")
            art_str = " + ".join(art_strings) if art_strings else "Sem artefatos"
            
            lines.append(f"| {char.name} | Nv. {char.level} | {stars} | C{char.constellation} | {weapon} | {art_str} |")
            
        # Seção de Builds para Personagens Nível 90
        lines.append("")
        lines.append("## Detalhes de Builds (Personagens Nv. 90)")
        lines.append("")
        
        for char in sorted(chars, key=lambda c: (c.rarity, c.level), reverse=True):
            if char.level == 90:
                # 1. Arma
                if char.weapon:
                    refinement = getattr(char.weapon, "refinement", 1)
                    weapon_text = f"{char.weapon.name} (Nv. {char.weapon.level}, R{refinement})"
                else:
                    weapon_text = "Nenhuma arma equipada"
                
                # 2. Artefatos
                art_sets = {}
                for art in char.artifacts:
                    if hasattr(art, "set") and art.set:
                        art_sets[art.set.name] = art_sets.get(art.set.name, 0) + 1
                
                set_strings = []
                for s_name, count in sorted(art_sets.items(), key=lambda x: x[1], reverse=True):
                    set_strings.append(f"{s_name} ({count} peças)")
                artifacts_text = " + ".join(set_strings) if set_strings else "Nenhum artefato equipado"
                
                # 3. Status Finais
                properties_list = []
                if hasattr(char, "selected_properties") and char.selected_properties:
                    for prop in char.selected_properties:
                        name = prop.info.name if (hasattr(prop, "info") and prop.info and prop.info.name) else "Atributo"
                        val = getattr(prop, "final", "")
                        if name and val:
                            properties_list.append(f"{name}: {val}")
                properties_text = ", ".join(properties_list) if properties_list else "Status não disponíveis"
                
                # Escreve o bloco do personagem
                constellation = f"C{char.constellation}"
                lines.append(f"**Personagem:** {char.name} | **Nível:** {char.level} | **Constelação:** {constellation}")
                lines.append(f"- **Arma:** {weapon_text}")
                lines.append(f"- **Artefatos:** {artifacts_text}")
                lines.append(f"- **Status Finais:** {properties_text}")
                
                if hasattr(char, "artifacts") and char.artifacts:
                    lines.append("\n  **Detalhamento de Peças (Substatus):**")
                    for art in char.artifacts:
                        main_prop = getattr(art, "main_stat", getattr(art, "main_property", None))
                        if main_prop:
                            m_name = getattr(getattr(main_prop, "info", main_prop), "name", getattr(main_prop, "property_name", getattr(main_prop, "type", "Atributo")))
                            m_val = getattr(main_prop, "value", getattr(main_prop, "display_value", getattr(main_prop, "stat_value", "")))
                            main_stat = f"{m_name} ({m_val})"
                        else:
                            main_stat = "Desconhecido"
                            
                        substats_str = "Sem substatus"
                        sub_props = getattr(art, "properties", getattr(art, "sub_stats", getattr(art, "sub_properties", getattr(art, "sub_property_list", []))))
                        if sub_props:
                            subs = []
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                subs.append(f"{s_name}: {s_val}")
                            substats_str = ", ".join(subs)
                        
                        genshin_slot_map = {
                            "EQUIP_BRACER": "Flor da Vida",
                            "EQUIP_NECKLACE": "Pluma da Morte",
                            "EQUIP_SHOES": "Areia do Tempo",
                            "EQUIP_RING": "Cálice de Eonothem",
                            "EQUIP_DRESS": "Tiara de Logos"
                        }
                        # Genshin usa equip_type, mas tem um formato de string as vezes
                        pos = getattr(art, 'pos', getattr(art, 'equip_type', '?'))
                        if hasattr(pos, "name"): pos = pos.name # caso seja enum
                        pos_name = genshin_slot_map.get(str(pos), str(pos))
                        lines.append(f"  • [{pos_name}] {art.name}")
                        lines.append(f"    - Principal: {main_stat}")
                        lines.append(f"    - Substatus: {substats_str}")
                        
                lines.append("")
                lines.append("---")
                lines.append("")
                
        # Salva dados estruturados em JSON para a Galeria Visual da UI
        roster_json_path = "genshin/roster_data_genshin.json"
        try:
            char_json_list = []
            genshin_slot_map = {
                "EQUIP_BRACER": "Flor da Vida",
                "EQUIP_NECKLACE": "Pluma da Morte",
                "EQUIP_SHOES": "Areia do Tempo",
                "EQUIP_RING": "Cálice de Eonothem",
                "EQUIP_DRESS": "Tiara de Logos"
            }
            for char in sorted(chars, key=lambda c: (c.rarity, c.level), reverse=True):
                w_info = {}
                if hasattr(char, "weapon") and char.weapon:
                    w_info = {
                        "name": char.weapon.name,
                        "level": getattr(char.weapon, "level", 90),
                        "rank": getattr(char.weapon, "refinement", 1),
                        "icon": getattr(char.weapon, "icon", "")
                    }
                artifacts_json = []
                if hasattr(char, "artifacts") and char.artifacts:
                    for art in char.artifacts:
                        pos = getattr(art, 'pos', getattr(art, 'equip_type', '?'))
                        if hasattr(pos, "name"): pos = pos.name
                        pos_name = genshin_slot_map.get(str(pos), str(pos))
                        main_prop = getattr(art, "main_stat", getattr(art, "main_property", None))
                        main_stat = "Desconhecido"
                        if main_prop:
                            m_name = getattr(getattr(main_prop, "info", main_prop), "name", getattr(main_prop, "property_name", getattr(main_prop, "type", "Atributo")))
                            m_val = getattr(main_prop, "value", getattr(main_prop, "display_value", getattr(main_prop, "stat_value", "")))
                            main_stat = f"{m_name} ({m_val})"
                            
                        sub_props = getattr(art, "properties", getattr(art, "sub_stats", getattr(art, "sub_properties", getattr(art, "sub_property_list", []))))
                        subs = []
                        if sub_props:
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                subs.append(f"{s_name}: {s_val}")
                        artifacts_json.append({
                            "name": art.name,
                            "icon": getattr(art, "icon", ""),
                            "slot": pos_name,
                            "main": main_stat,
                            "sub": ", ".join(subs) if subs else "Sem substatus"
                        })
                        
                char_json_list.append({
                    "name": char.name,
                    "level": char.level,
                    "rarity": char.rarity,
                    "rank_str": f"C{char.constellation}",
                    "element": getattr(char, "element", "Anemo"),
                    "icon": getattr(char, "icon", ""),
                    "weapon": w_info,
                    "relics": artifacts_json
                })
            os.makedirs(os.path.dirname(roster_json_path) or ".", exist_ok=True)
            with open(roster_json_path, "w", encoding="utf-8") as jf:
                json.dump(char_json_list, jf, ensure_ascii=False, indent=2)
        except Exception as json_err:
            print(f"Aviso ao salvar roster_data_genshin.json: {json_err}")

        markdown_content = "\n".join(lines)
        
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filename


class ZZZExtractor(BaseExtractor):
    def __init__(self, cookies: dict):
        super().__init__(cookies)
        self.client.game = genshin.Game.ZZZ

    async def extrair_e_salvar(self, filename: str = "zzz/roster_zzz.md") -> str:
        """
        Busca os dados de Zenless Zone Zero (ZZZ) e gera um arquivo Markdown formatado.
        """
        zzz_acc = await self.get_account("nap")
        if not zzz_acc:
            raise Exception("Nenhuma conta ativa de Zenless Zone Zero (ZZZ) encontrada vinculada a este perfil HoYoLAB.")
            
        uid = zzz_acc.uid
        
        try:
            user_data = await self.client.get_zzz_user(uid)
            # Para obter W-Engines e discos, precisamos buscar os detalhes completos de cada agente
            partial_agents = await self.client.get_zzz_agents(uid)
            agent_ids = [agent.id for agent in partial_agents]
            
            if agent_ids:
                agents = await self.client.get_zzz_agent_info(agent_ids, uid=uid)
                # Garante que seja tratado como lista se retornar apenas um
                if not isinstance(agents, (list, tuple)):
                    agents = [agents]
            else:
                agents = []
        except Exception as e:
            raise Exception(
                f"Não foi possível obter dados detalhados para o UID {uid}.\n"
                f"Certifique-se de que o Registro de Batalha de ZZZ está público nas configurações de privacidade."
            )
            
        lines = []
        lines.append("# Relatório de Agentes - Zenless Zone Zero")
        lines.append(f"**UID:** {uid}")
        lines.append(f"**Nível de Intermediário:** {zzz_acc.level}")
        lines.append(f"**Reputação:** {user_data.stats.inter_knot_reputation}")
        lines.append(f"**Dias Ativos:** {user_data.stats.active_days}")
        lines.append(f"**Agentes Obtidos:** {user_data.stats.character_num}")
        lines.append(f"**Bangboos Obtidos:** {user_data.stats.bangboo_obtained}")
        lines.append(f"**Conquistas:** {user_data.stats.achievement_count}")
        
        try:
            endgame_text = await endgame_extractor.extrair_endgame_zzz(self.client, uid)
            if endgame_text:
                lines.append("")
                lines.append(endgame_text)
        except Exception as e:
            print(f"Aviso: Não foi possível puxar dados de Endgame ZZZ: {e}")
            
        lines.append("")
        lines.append("## Detalhes do Roster de Agentes")
        lines.append("")
        lines.append("| Agente | Nível | Raridade | Cinema | W-Engine Equipado | Discos Equipados |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for agent in sorted(agents, key=lambda a: (a.rarity, a.level), reverse=True):
            stars = "⭐" * (5 if agent.rarity == "S" else 4) # ZZZ usa S e A para raridade
            
            w_engine = "Nenhum"
            if agent.w_engine:
                w_engine = f"{agent.w_engine.name} (Nv. {agent.w_engine.level}, R{agent.w_engine.refinement})"
                
            disc_sets = {}
            for disc in agent.discs:
                if hasattr(disc, "set_effect") and disc.set_effect:
                    disc_sets[disc.set_effect.name] = disc.set_effect.owned_num
            
            disc_strings = []
            for s_name, count in sorted(disc_sets.items(), key=lambda x: x[1], reverse=True):
                disc_strings.append(f"{s_name} ({count} peças)")
            disc_str = " + ".join(disc_strings) if disc_strings else "Sem discos"
            
            lines.append(f"| {agent.name} | Nv. {agent.level} | {agent.rarity} ({stars}) | M{agent.rank} | {w_engine} | {disc_str} |")
            
        # Seção de Builds para Agentes Nível 60
        lines.append("")
        lines.append("## Detalhes de Builds (Agentes Nv. 60)")
        lines.append("")
        
        for agent in sorted(agents, key=lambda a: (a.rarity, a.level), reverse=True):
            if agent.level == 60:
                # 1. W-Engine
                if agent.w_engine:
                    refinement = getattr(agent.w_engine, "refinement", 1)
                    w_engine_text = f"{agent.w_engine.name} (Nv. {agent.w_engine.level}, R{refinement})"
                else:
                    w_engine_text = "Nenhum W-Engine equipado"
                
                # 2. Discos de Áudio
                disc_sets = {}
                for disc in agent.discs:
                    if hasattr(disc, "set_effect") and disc.set_effect:
                        disc_sets[disc.set_effect.name] = disc.set_effect.owned_num
                
                set_strings = []
                for s_name, count in sorted(disc_sets.items(), key=lambda x: x[1], reverse=True):
                    set_strings.append(f"{s_name} ({count} peças)")
                discs_text = " + ".join(set_strings) if set_strings else "Nenhum disco equipado"
                
                # 3. Status Finais
                properties_list = []
                if hasattr(agent, "properties") and agent.properties:
                    for prop in agent.properties:
                        name = getattr(prop, "name", "Atributo")
                        val = getattr(prop, "final", "")
                        if name and val:
                            properties_list.append(f"{name}: {val}")
                properties_text = ", ".join(properties_list) if properties_list else "Status não disponíveis"
                
                # Escreve o bloco do agente
                cinema = f"M{agent.rank}"
                lines.append(f"**Agente:** {agent.name} | **Nível:** {agent.level} | **Cinema:** {cinema}")
                lines.append(f"- **W-Engine:** {w_engine_text}")
                lines.append(f"- **Discos:** {discs_text}")
                lines.append(f"- **Status Finais:** {properties_text}")
                
                if hasattr(agent, "discs") and agent.discs:
                    lines.append("\n  **Detalhamento de Peças (Substatus):**")
                    for disc in agent.discs:
                        main_props_list = getattr(disc, "main_properties", getattr(disc, "main_stat", []))
                        if not isinstance(main_props_list, list): main_props_list = [main_props_list]
                        main_prop = main_props_list[0] if main_props_list else None
                        
                        if main_prop:
                            m_name = getattr(getattr(main_prop, "info", main_prop), "name", getattr(main_prop, "property_name", getattr(main_prop, "type", "Atributo")))
                            m_val = getattr(main_prop, "value", getattr(main_prop, "display_value", getattr(main_prop, "stat_value", "")))
                            main_stat = f"{m_name} ({m_val})"
                        else:
                            main_stat = "Desconhecido"
                            
                        substats_str = "Sem substatus"
                        sub_props = getattr(disc, "properties", getattr(disc, "sub_stats", getattr(disc, "sub_properties", getattr(disc, "sub_property_list", []))))
                        if sub_props:
                            subs = []
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                subs.append(f"{s_name}: {s_val}")
                            substats_str = ", ".join(subs)
                        
                        pos = getattr(disc, 'position', getattr(disc, 'pos', '?'))
                        lines.append(f"  • [Disco {pos}] {disc.name}")
                        lines.append(f"    - Principal: {main_stat}")
                        lines.append(f"    - Substatus: {substats_str}")

                lines.append("")
                lines.append("---")
                lines.append("")
                
        # Salva dados estruturados em JSON para a Galeria Visual da UI
        roster_json_path = "zzz/roster_data_zzz.json"
        try:
            char_json_list = []
            for agent in sorted(agents, key=lambda a: (a.rarity, a.level), reverse=True):
                w_info = {}
                if hasattr(agent, "w_engine") and agent.w_engine:
                    w_info = {
                        "name": agent.w_engine.name,
                        "level": getattr(agent.w_engine, "level", 60),
                        "rank": getattr(agent.w_engine, "refinement", 1),
                        "icon": getattr(agent.w_engine, "icon", "")
                    }
                discs_json = []
                if hasattr(agent, "discs") and agent.discs:
                    for disc in agent.discs:
                        pos = getattr(disc, 'position', getattr(disc, 'pos', '?'))
                        pos_name = f"Disco {pos}"
                        main_props_list = getattr(disc, "main_properties", getattr(disc, "main_stat", []))
                        if not isinstance(main_props_list, list): main_props_list = [main_props_list]
                        main_prop = main_props_list[0] if main_props_list else None
                        main_stat = "Desconhecido"
                        if main_prop:
                            m_name = getattr(getattr(main_prop, "info", main_prop), "name", getattr(main_prop, "property_name", getattr(main_prop, "type", "Atributo")))
                            m_val = getattr(main_prop, "value", getattr(main_prop, "display_value", getattr(main_prop, "stat_value", "")))
                            main_stat = f"{m_name} ({m_val})"
                            
                        sub_props = getattr(disc, "properties", getattr(disc, "sub_stats", getattr(disc, "sub_properties", getattr(disc, "sub_property_list", []))))
                        subs = []
                        if sub_props:
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                subs.append(f"{s_name}: {s_val}")
                        discs_json.append({
                            "name": disc.name,
                            "icon": getattr(disc, "icon", ""),
                            "slot": pos_name,
                            "main": main_stat,
                            "sub": ", ".join(subs) if subs else "Sem substatus"
                        })
                icon_url = getattr(agent, "square_icon", getattr(agent, "rectangle_icon", getattr(agent, "icon", "")))
                rarity_num = 5 if str(agent.rarity).upper() in ["S", "5"] else 4
                char_json_list.append({
                    "name": agent.name,
                    "level": agent.level,
                    "rarity": rarity_num,
                    "rank_str": f"M{agent.rank}",
                    "element": getattr(agent.element, "name", str(agent.element)),
                    "icon": icon_url,
                    "weapon": w_info,
                    "relics": discs_json
                })
            os.makedirs(os.path.dirname(roster_json_path) or ".", exist_ok=True)
            with open(roster_json_path, "w", encoding="utf-8") as jf:
                json.dump(char_json_list, jf, ensure_ascii=False, indent=2)
        except Exception as json_err:
            print(f"Aviso ao salvar roster_data_zzz.json: {json_err}")

        markdown_content = "\n".join(lines)
        
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filename


class MultiGameExtractor:
    def __init__(self, cookies: dict):
        self.cookies = cookies
        
    async def extrair_jogo(self, game: str, output_file: str = None) -> str:
        """
        Extrai os dados do jogo especificado e salva no arquivo.
        
        Args:
            game (str): 'hsr', 'genshin' ou 'zzz'.
            output_file (str, opcional): Caminho do arquivo de saída.
            
        Retorna:
            str: Caminho do arquivo de saída gerado.
        """
        game = game.lower()
        if game == "hsr":
            extractor = HSRExtractor(self.cookies)
            return await extractor.extrair_e_salvar(output_file or "hsr/roster_hsr.md")
        elif game == "genshin":
            extractor = GenshinExtractor(self.cookies)
            return await extractor.extrair_e_salvar(output_file or "genshin/roster_genshin.md")
        elif game == "zzz":
            extractor = ZZZExtractor(self.cookies)
            return await extractor.extrair_e_salvar(output_file or "zzz/roster_zzz.md")
        else:
            raise ValueError(f"Jogo não suportado: {game}")
