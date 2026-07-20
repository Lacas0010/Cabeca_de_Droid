import re
import requests
import asyncio
import genshin

# Dicionários de mapeamento para traduzir Elementos e Caminhos para Português
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

class HSRExtractor:
    def __init__(self, cookies: dict):
        """
        Inicializa o extrator de Honkai: Star Rail utilizando a biblioteca genshin.py.
        A inicialização define explicitamente a localidade como 'pt-pt' para evitar
        erros de validação na API do HoYoLAB.
        """
        self.client = genshin.Client(cookies=cookies, lang="pt-pt")
        self.client.game = genshin.Game.STARRAIL
        
    async def extrair_e_salvar(self, filename: str = "meus_personagens_hsr.md") -> str:
        """
        Rotina assíncrona para buscar os dados de Honkai: Star Rail e criar o arquivo Markdown.
        
        Retorna:
            str: O caminho do arquivo Markdown gerado.
        """
        # 1. Busca as contas vinculadas para obter o UID de Star Rail
        try:
            accounts = await self.client.get_game_accounts()
        except Exception as e:
            raise Exception(f"Erro ao obter contas vinculadas: {e}")
        
        hsr_account = None
        for acc in accounts:
            if acc.game_biz.startswith("hkrpg"):
                hsr_account = acc
                break
                
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
                lines.append("")
                lines.append("---")
                lines.append("")

        markdown_content = "\n".join(lines)
        
        # Salva o arquivo no diretório
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filename
