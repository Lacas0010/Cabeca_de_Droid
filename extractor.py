import os
import re
import json
import requests
import asyncio
import genshin
import endgame_extractor

def patch_genshin_enums():
    """
    Registra dinamicamente novos valores de enum no genshin.py para ZZZ/HSR/Genshin
    evitando que Pydantic levante ValidationError quando a API do HoYoLAB adiciona novos elementos ou especialidades (ex: element_type=300).
    """
    try:
        from genshin.models.zzz.character import ZZZElementType, ZZZSpecialty
        for val in range(200, 350):
            if val not in ZZZElementType._value2member_map_:
                member_name = f"ELEMENT_{val}"
                new_member = int.__new__(ZZZElementType, val)
                new_member._name_ = member_name
                new_member._value_ = val
                ZZZElementType._member_map_[member_name] = new_member
                ZZZElementType._value2member_map_[val] = new_member

        for val in range(1, 30):
            if val not in ZZZSpecialty._value2member_map_:
                member_name = f"SPECIALTY_{val}"
                new_member = int.__new__(ZZZSpecialty, val)
                new_member._name_ = member_name
                new_member._value_ = val
                ZZZSpecialty._member_map_[member_name] = new_member
                ZZZSpecialty._value2member_map_[val] = new_member
    except Exception as err:
        print(f"[AVISO] Falha ao aplicar patch nos enums do genshin.py: {err}")

patch_genshin_enums()

# Mapeamento de IDs de costumes (skins) para os nomes correspondentes no Enka.Network
GENSHIN_SKIN_MAP = {
    200201: "UI_AvatarIcon_AyakaCostumeFruhling",
    200301: "UI_AvatarIcon_QinCostumeSea",
    200302: "UI_AvatarIcon_QinCostumeWic",
    200601: "UI_AvatarIcon_LisaCostumeStudentin",
    201401: "UI_AvatarIcon_BarbaraCostumeSummertime",
    201501: "UI_AvatarIcon_KaeyaCostumeDancer",
    201601: "UI_AvatarIcon_DilucCostumeFlamme",
    202101: "UI_AvatarIcon_AmborCostumeWic",
    202301: "UI_AvatarIcon_XianglingCostumeWinter",
    202501: "UI_AvatarIcon_XingqiuCostumeBamboo",
    202701: "UI_AvatarIcon_NingguangCostumeFloral",
    202901: "UI_AvatarIcon_KleeCostumeWitch",
    203101: "UI_AvatarIcon_FischlCostumeHighness",
    203201: "UI_AvatarIcon_BennettCostumeSummer",
    203701: "UI_AvatarIcon_GanyuCostumeYu",
    204101: "UI_AvatarIcon_MonaCostumeWic",
    204201: "UI_AvatarIcon_KeqingCostumeFeather",
    204501: "UI_AvatarIcon_RosariaCostumeWic",
    204601: "UI_AvatarIcon_HutaoCostumeWinter",
    206001: "UI_AvatarIcon_YelanCostumeSummer",
    206101: "UI_AvatarIcon_MomokaCostumeErrantry",
    206301: "UI_AvatarIcon_ShenheCostumeDai",
    207001: "UI_AvatarIcon_NilouCostumeFairy",
    210701: "UI_AvatarIcon_CitlaliCostumeXia",
    212301: "UI_AvatarIcon_DurinCostumeWic"
}

def get_genshin_costume_info(costume_id):
    """Busca com segurança o nome da skin e arte de splash para Genshin Impact."""
    if not costume_id:
        return None
    c_name = None
    try:
        cid_int = int(costume_id)
        if cid_int in GENSHIN_SKIN_MAP:
            c_name = GENSHIN_SKIN_MAP[cid_int]
    except (ValueError, TypeError):
        pass
    if not c_name and str(costume_id) in GENSHIN_SKIN_MAP:
        c_name = GENSHIN_SKIN_MAP[str(costume_id)]
    
    if c_name:
        return {
            "icon": c_name,
            "art": c_name.replace("UI_AvatarIcon_", "UI_Costume_")
        }
    return None

def get_zzz_prydwen_slug(agent_name: str) -> str:
    """Converte o nome de um Agente do ZZZ para o slug de imagem HD no Prydwen."""
    if not agent_name:
        return ""
    clean = agent_name.lower().strip()
    special_cases = {
        "anby demara": "anby-demara",
        "anby": "anby-demara",
        "anton ivanov": "anton",
        "astra yao": "astra-yao",
        "ben bigger": "ben",
        "billy kid": "billy-kid",
        "billy": "billy-kid",
        "grace howard": "grace-howard",
        "grace": "grace-howard",
        "hoshimi miyabi": "miyabi",
        "asaba harumasa": "harumasa",
        "jane doe": "jane-doe",
        "jane": "jane-doe",
        "koleda belobog": "koleda",
        "nicole demara": "nicole-demara",
        "nicole": "nicole-demara",
        "orphie & magus": "orphie-magus",
        "piper wheel": "piper",
        "seth lowell": "seth",
        "soldier 11": "soldier-11",
        "von lycaon": "lycaon",
        "zhu yuan": "zhu-yuan"
    }
    if clean in special_cases:
        return special_cases[clean]
    for k, v in special_cases.items():
        if clean == k or k in clean:
            return v
    return clean.replace('&', '').replace(' ', '-').replace('_', '-')


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

def clean_relic_name(text: str) -> str:
    """
    Remove tags de variação de gênero (ex: {F#da Portadora}{M#do Portador})
    retornando o nome limpo da relíquia/artefato/disco.

    Exemplos:
        'Capuz {F#da Portadora}{M#do Portador}' -> 'Capuz da Portadora'
        'Manopla da Espada {F#da Portadora}{M#do Portador}' -> 'Manopla da Espada da Portadora'
        'Botas Pioneiras {F#da Portadora}{M#do Portador}' -> 'Botas Pioneiras da Portadora'
    """
    if not text or not isinstance(text, str):
        return "" if text is None else str(text)

    def replace_gender_block(match):
        block = match.group(0)
        tags = re.findall(r'\{([fFmM])\s*#\s*([^}]*)\}', block)
        if not tags:
            return ""
        for gender, content in tags:
            if gender.upper() == 'F':
                return content.strip()
        return tags[0][1].strip()

    cleaned = re.sub(
        r'(\{[fFmM]\s*#\s*[^}]*\}\s*)+',
        replace_gender_block,
        text
    )

    return re.sub(r'\s+', ' ', cleaned).strip()


# Mapeamento oficial de sanitização e abreviação compacta de nomes de atributos (Stats / Substats)
STAT_SHORT_NAMES = {
    # Honkai: Star Rail (HSR)
    "Bônus de Dano de Fogo": "Dano Fogo",
    "Bônus de Dano Fogo": "Dano Fogo",
    "Bônus de Dano de Gelo": "Dano Gelo",
    "Bônus de Dano Gelo": "Dano Gelo",
    "Bônus de Dano de Raio": "Dano Raio",
    "Bônus de Dano Raio": "Dano Raio",
    "Bônus de Dano de Vento": "Dano Vento",
    "Bônus de Dano Vento": "Dano Vento",
    "Bônus de Dano Quântico": "Dano Quântico",
    "Bônus de Dano de Quântico": "Dano Quântico",
    "Bônus de Dano Imaginário": "Dano Imaginário",
    "Bônus de Dano de Imaginário": "Dano Imaginário",
    "Bônus de Dano Físico": "Dano Físico",
    "Bônus de Dano de Físico": "Dano Físico",
    "Taxa de Acerto de Efeito": "Acerto Efeito",
    "Resistência a Efeito": "RES Efeito",
    "RES a Efeito": "RES Efeito",
    "Efeito de Quebra": "Quebra",
    "Chance de CRIT": "Taxa CRIT",
    "Taxa de CRIT": "Taxa CRIT",
    "Taxa Crítica": "Taxa CRIT",
    "Dano de CRIT": "Dano CRIT",
    "Dano Crítico": "Dano CRIT",
    "Regeneração de Energia": "Regen. Energia",
    "Taxa de Reg. de Energia": "Regen. Energia",
    "Taxa de Regeneração de Energia": "Regen. Energia",

    # Genshin Impact
    "Proficiência Elemental": "Prof. Element.",
    "Recarga de Energia": "Recarga",
    "Bônus de Dano Anemo": "Dano Anemo",
    "Bônus de Dano Pyro": "Dano Pyro",
    "Bônus de Dano Hydro": "Dano Hydro",
    "Bônus de Dano Electro": "Dano Electro",
    "Bônus de Dano Cryo": "Dano Cryo",
    "Bônus de Dano Geo": "Dano Geo",
    "Bônus de Dano Dendro": "Dano Dendro",
    "Bônus de Dano Elemental": "Dano Elem.",

    # Zenless Zone Zero (ZZZ)
    "Proficiência de Anomalia": "Prof. Anomalia",
    "Taxa de Acerto de Anomalia": "Maest. Anomalia",
    "Maestria de Anomalia": "Maest. Anomalia",
    "Recuperação de Energia": "Recup. Energia",
    "Taxa de Recuperação de Energia": "Recup. Energia",
    "Taxa de Perfuração": "Perfuração",
    "Bônus de Dano Elétrico": "Dano Elétrico",
    "Bônus de Dano de Elétrico": "Dano Elétrico",
    "Bônus de Dano Éter": "Dano Éter",
    "Bônus de Dano de Éter": "Dano Éter",

    # Inglês (API HSR, ZZZ retorna em inglês em alguns idiomas)
    "CRIT Rate": "Taxa CRIT",
    "CRIT DMG": "Dano CRIT",
    "Effect Hit Rate": "Acerto Efeito",
    "Effect RES": "RES Efeito",
    "Break Effect": "Quebra",
    "Energy Regeneration Rate": "Regen. Energia",
    "Outgoing Healing Boost": "Cura Bônus",
    "Physical DMG Boost": "Dano Físico",
    "Fire DMG Boost": "Dano Fogo",
    "Ice DMG Boost": "Dano Gelo",
    "Lightning DMG Boost": "Dano Raio",
    "Wind DMG Boost": "Dano Vento",
    "Quantum DMG Boost": "Dano Quântico",
    "Imaginary DMG Boost": "Dano Imaginário",
    # ZZZ English
    "Anomaly Proficiency": "Prof. Anomalia",
    "Anomaly Mastery": "Maest. Anomalia",
    "PEN Ratio": "Perfuração",
    "Energy Regen": "Regen. Energia",
    "Impact": "Impacto",
    # Genshin English
    "Elemental Mastery": "Prof. Element.",
    "Energy Recharge": "Recarga",
    "Healing Bonus": "Cura Bônus",
    "Anemo DMG Bonus": "Dano Anemo",
    "Pyro DMG Bonus": "Dano Pyro",
    "Hydro DMG Bonus": "Dano Hydro",
    "Electro DMG Bonus": "Dano Electro",
    "Cryo DMG Bonus": "Dano Cryo",
    "Geo DMG Bonus": "Dano Geo",
    "Dendro DMG Bonus": "Dano Dendro",
}

def sanitize_stat_name(stat_text: str) -> str:
    """
    Substitui nomes longos de atributos por siglas e versões compactas (máx 12-14 caracteres),
    preservando valores numéricos e sufixos de porcentagem.
    """
    if not stat_text:
        return ""
    s = str(stat_text).strip()
    if s in STAT_SHORT_NAMES:
        return STAT_SHORT_NAMES[s]
    for k, v in STAT_SHORT_NAMES.items():
        if k in s:
            s = s.replace(k, v)
    s = re.sub(r'Bônus de Dano (?:de )?([A-Za-zÀ-ÿ]+)', r'Dano \1', s, flags=re.IGNORECASE)
    return s



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
            if isinstance(e, genshin.errors.DataNotPublic):
                raise Exception(
                    f"Não foi possível obter dados para o UID {uid}.\n"
                    f"Certifique-se de que o perfil no HoYoLAB ('Registro de Batalha') está público nas configurações de privacidade."
                )
            else:
                raise Exception(f"Não foi possível obter dados para o UID {uid}: {e}")
        
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
            
        # Seção de Builds para Personagens Nível 70 ou mais
        lines.append("")
        lines.append("## Detalhes de Builds (Personagens Nv. 70 ou mais)")
        lines.append("")
        
        for char in sorted(characters_data.avatar_list, key=lambda c: (c.rarity, c.level), reverse=True):
            if char.level >= 70:
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
                    set_name = clean_relic_name(r.name)  # Fallback
                    if hasattr(r, "wiki") and r.wiki:
                        match = re.search(r'/entry/(\d+)', r.wiki)
                        if match:
                            w_id = match.group(1)
                            set_name = clean_relic_name(wiki_map.get(w_id, f"Conjunto {w_id}"))
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
                        lines.append(f"  • [{pos_name}] {clean_relic_name(relic.name)}")
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
                        main_stat = sanitize_stat_name(f"{m_name} ({m_val})" if m_val else m_name)
                        
                    sub_props = getattr(r, "properties", getattr(r, "sub_properties", getattr(r, "sub_stats", getattr(r, "sub_property_list", []))))
                    subs = []
                    if sub_props:
                        for sub in sub_props:
                            s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                            s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                            s_clean = sanitize_stat_name(s_name)
                            subs.append(f"{s_clean}: {s_val}")
                    relics_json.append({
                        "name": clean_relic_name(r.name),
                        "icon": getattr(r, "icon", ""),
                        "slot": pos_name,
                        "main": main_stat,
                        "sub": ", ".join(subs) if subs else "Sem substatus"
                    })
                    
                char_icon = getattr(char, "icon", getattr(char, "image", ""))
                hsr_splash = getattr(char, "portrait", getattr(char, "draw", getattr(char, "art_url", getattr(char, "image", getattr(char, "figure_path", getattr(char, "gacha_art", getattr(char, "icon", "")))))))
                costumes = getattr(char, "costumes", getattr(char, "skins", getattr(char, "outfits", None)))
                if costumes:
                    c_item = costumes[0]
                    char_icon = getattr(c_item, "icon", getattr(c_item, "image", char_icon))
                    c_splash = getattr(c_item, "portrait", getattr(c_item, "draw", getattr(c_item, "art_url", getattr(c_item, "image", getattr(c_item, "figure_path", getattr(c_item, "gacha_art", getattr(c_item, "icon", None)))))))
                    if c_splash:
                        hsr_splash = c_splash

                # Extrai Status Finais (Final Stats) do personagem HSR
                hsr_stats = {}
                props = getattr(char, "properties", [])
                for prop in (props or []):
                    p_name = getattr(getattr(prop, "info", prop), "name", getattr(prop, "property_name", None))
                    p_final = getattr(prop, "final", getattr(prop, "value", ""))
                    if p_name and p_final and str(p_final) not in ('', '0', '0.0%', '0.0'):
                        label = sanitize_stat_name(p_name)
                        hsr_stats[label] = str(p_final)

                char_json_list.append({
                    "id": str(char.id),
                    "name": char.name,
                    "level": char.level,
                    "rarity": char.rarity,
                    "rank_str": f"E{char.rank}",
                    "element": element,
                    "icon": char_icon,
                    "gacha_art": hsr_splash,
                    "weapon": w_info,
                    "relics": relics_json,
                    "stats": hsr_stats
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
            
        # Salva no SQLite
        try:
            import database
            database.save_game_account(uid, "hsr", info.nickname, info.level, stats.active_days)
            for c in char_json_list:
                char_md = ""
                pattern = rf'(\*\*(?:Personagem):\*\*\s*{re.escape(c["name"])}.*?)(?=\n\*\*(?:Personagem)|\n## |\Z)'
                match = re.search(pattern, markdown_content, re.DOTALL | re.I)
                if match:
                    char_md = match.group(1).strip()
                # NOTA: O arquivo database.py e a tabela SQLite precisarão ser atualizados para receber a nova coluna char_id
                database.save_character(
                    uid=uid,
                    game_id="hsr",
                    char_id=str(c["id"]),
                    name=c["name"],
                    level=c["level"],
                    rarity=c["rarity"],
                    rank_str=c["rank_str"],
                    element=c["element"],
                    icon=c["icon"],
                    gacha_art=c.get("gacha_art"),
                    weapon_name=c["weapon"].get("name") if c["weapon"] else None,
                    weapon_level=c["weapon"].get("level") if c["weapon"] else None,
                    weapon_rank=c["weapon"].get("rank") if c["weapon"] else None,
                    weapon_icon=c["weapon"].get("icon") if c["weapon"] else None,
                    raw_md=char_md
                )
                database.clear_character_relics(uid, c["name"])
                for r in c["relics"]:
                    database.save_relic(
                        uid=uid,
                        character_name=c["name"],
                        name=r["name"],
                        slot=r["slot"],
                        main_stat=r["main"],
                        sub_stats=r["sub"],
                        icon=r["icon"]
                    )
            print("[INFO] Roster HSR salvo com sucesso no banco de dados SQLite.")
        except Exception as sqlite_err:
            print(f"Aviso ao salvar HSR no SQLite: {sqlite_err}")

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
            if isinstance(e, genshin.errors.DataNotPublic):
                raise Exception(
                    f"Não foi possível obter dados detalhados para o UID {uid}.\n"
                    f"Certifique-se de que o Registro de Batalha de Genshin está público nas configurações de privacidade."
                )
            else:
                raise Exception(f"Não foi possível obter dados detalhados para o UID {uid}: {e}")
            
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
            
        # Seção de Builds para Personagens Nível 70 ou mais
        lines.append("")
        lines.append("## Detalhes de Builds (Personagens Nv. 70 ou mais)")
        lines.append("")
        
        for char in sorted(chars, key=lambda c: (c.rarity, c.level), reverse=True):
            if char.level >= 70:
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
                        lines.append(f"  • [{pos_name}] {clean_relic_name(art.name)}")
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
                            main_stat = sanitize_stat_name(f"{m_name} ({m_val})" if m_val else m_name)
                            
                        sub_props = getattr(art, "properties", getattr(art, "sub_stats", getattr(art, "sub_properties", getattr(art, "sub_property_list", []))))
                        subs = []
                        if sub_props:
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                s_clean = sanitize_stat_name(s_name)
                                subs.append(f"{s_clean}: {s_val}")
                        artifacts_json.append({
                            "name": clean_relic_name(art.name),
                            "icon": getattr(art, "icon", ""),
                            "slot": pos_name,
                            "main": main_stat,
                            "sub": ", ".join(subs) if subs else "Sem substatus"
                        })
                        
                char_icon = getattr(char, "icon", "")
                genshin_splash = None
                
                if hasattr(char, "costumes") and char.costumes:
                    costume = char.costumes[0]
                    costume_id = getattr(costume, "id", None)
                    c_info = get_genshin_costume_info(costume_id)
                    if c_info:
                        char_icon = f"https://enka.network/ui/{c_info['icon']}.png"
                        genshin_splash = f"https://enka.network/ui/{c_info['art']}.png"
                    elif hasattr(costume, "icon") and costume.icon:
                        char_icon = costume.icon
                        if "UI_AvatarIcon_" in costume.icon:
                            if "Costume" in costume.icon:
                                genshin_splash = costume.icon.replace("UI_AvatarIcon_", "UI_Costume_")
                            else:
                                genshin_splash = costume.icon.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_")
                        else:
                            genshin_splash = getattr(costume, "gacha_art", getattr(costume, "splash_art", costume.icon))

                if not genshin_splash:
                    genshin_splash = getattr(char, "gacha_card", getattr(char, "gacha_slice", getattr(char, "gacha_art", getattr(char, "splash_art", getattr(char, "display_image", getattr(char, "card_icon", char_icon))))))
                    if not genshin_splash or "UI_AvatarIcon_" in genshin_splash:
                        if "UI_AvatarIcon_" in char_icon:
                            if "Costume" in char_icon:
                                genshin_splash = char_icon.replace("UI_AvatarIcon_", "UI_Costume_")
                            else:
                                genshin_splash = char_icon.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_")

                # Extrai Status Finais (Final Stats) do personagem Genshin
                genshin_stats = {}
                props = getattr(char, "properties", getattr(char, "fight_props", None))
                if props:
                    for prop in (props or []):
                        p_name = getattr(getattr(prop, "info", prop), "name", getattr(prop, "property_name", None))
                        p_final = getattr(prop, "final", getattr(prop, "value", ""))
                        if p_name and p_final and str(p_final) not in ('', '0', '0.0%', '0.0'):
                            label = sanitize_stat_name(p_name)
                            genshin_stats[label] = str(p_final)
                else:
                    # Genshin API de Battle Chronicle não retorna fight_props diretamente;
                    # Extraímos o que está disponível no objeto do personagem
                    for attr_name in ['hp', 'max_hp', 'atk', 'base_atk', 'def_', 'base_def', 'crit_rate', 'crit_dmg', 'healing_bonus', 'elemental_mastery', 'energy_recharge']:
                        v = getattr(char, attr_name, None)
                        if v is not None and v not in (0, 0.0, '', None):
                            label_map = {
                                'hp': 'HP', 'max_hp': 'HP', 'atk': 'ATQ', 'base_atk': 'ATQ Base',
                                'def_': 'DEF', 'base_def': 'DEF Base', 'crit_rate': 'Taxa CRIT',
                                'crit_dmg': 'Dano CRIT', 'healing_bonus': 'Cura Bônus',
                                'elemental_mastery': 'Prof. Element.', 'energy_recharge': 'Recarga'
                            }
                            genshin_stats[label_map.get(attr_name, attr_name)] = str(v)

                char_json_list.append({
                    "id": str(char.id),
                    "name": char.name,
                    "level": char.level,
                    "rarity": char.rarity,
                    "rank_str": f"C{char.constellation}",
                    "element": getattr(char, "element", "Anemo"),
                    "icon": char_icon,
                    "gacha_art": genshin_splash,
                    "weapon": w_info,
                    "relics": artifacts_json,
                    "stats": genshin_stats
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
            
        # Salva no SQLite
        try:
            import database
            database.save_game_account(uid, "genshin", genshin_acc.nickname if hasattr(genshin_acc, "nickname") else "Viajante", genshin_acc.level, getattr(genshin_acc, "active_days", 0))
            for c in char_json_list:
                char_md = ""
                pattern = rf'(\*\*(?:Personagem):\*\*\s*{re.escape(c["name"])}.*?)(?=\n\*\*(?:Personagem)|\n## |\Z)'
                match = re.search(pattern, markdown_content, re.DOTALL | re.I)
                if match:
                    char_md = match.group(1).strip()
                # NOTA: O arquivo database.py e a tabela SQLite precisarão ser atualizados para receber a nova coluna char_id
                database.save_character(
                    uid=uid,
                    game_id="genshin",
                    char_id=str(c["id"]),
                    name=c["name"],
                    level=c["level"],
                    rarity=c["rarity"],
                    rank_str=c["rank_str"],
                    element=c["element"],
                    icon=c["icon"],
                    gacha_art=c.get("gacha_art"),
                    weapon_name=c["weapon"].get("name") if c["weapon"] else None,
                    weapon_level=c["weapon"].get("level") if c["weapon"] else None,
                    weapon_rank=c["weapon"].get("rank") if c["weapon"] else None,
                    weapon_icon=c["weapon"].get("icon") if c["weapon"] else None,
                    raw_md=char_md
                )
                database.clear_character_relics(uid, c["name"])
                for r in c["relics"]:
                    database.save_relic(
                        uid=uid,
                        character_name=c["name"],
                        name=r["name"],
                        slot=r["slot"],
                        main_stat=r["main"],
                        sub_stats=r["sub"],
                        icon=r["icon"]
                    )
            print("[INFO] Roster Genshin salvo com sucesso no banco de dados SQLite.")
        except Exception as sqlite_err:
            print(f"Aviso ao salvar Genshin no SQLite: {sqlite_err}")

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
            if isinstance(e, genshin.errors.DataNotPublic):
                raise Exception(
                    f"Não foi possível obter dados detalhados para o UID {uid}.\n"
                    f"Certifique-se de que o Registro de Batalha de ZZZ está público nas configurações de privacidade."
                )
            else:
                raise Exception(f"Não foi possível obter dados detalhados para o UID {uid}: {e}")
            
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
            
        # Seção de Builds para Agentes Nível 50 ou mais
        lines.append("")
        lines.append("## Detalhes de Builds (Agentes Nv. 50 ou mais)")
        lines.append("")
        
        for agent in sorted(agents, key=lambda a: (a.rarity, a.level), reverse=True):
            if agent.level >= 50:
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
                        lines.append(f"  • [Disco {pos}] {clean_relic_name(disc.name)}")
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
                            main_stat = sanitize_stat_name(f"{m_name} ({m_val})" if m_val else m_name)
                            
                        sub_props = getattr(disc, "properties", getattr(disc, "sub_stats", getattr(disc, "sub_properties", getattr(disc, "sub_property_list", []))))
                        subs = []
                        if sub_props:
                            for sub in sub_props:
                                s_name = getattr(getattr(sub, "info", sub), "name", getattr(sub, "property_name", getattr(sub, "type", "Atributo")))
                                s_val = getattr(sub, "value", getattr(sub, "display_value", getattr(sub, "stat_value", "")))
                                s_clean = sanitize_stat_name(s_name)
                                subs.append(f"{s_clean}: {s_val}")
                        discs_json.append({
                            "name": clean_relic_name(disc.name),
                            "icon": getattr(disc, "icon", ""),
                            "slot": pos_name,
                            "main": main_stat,
                            "sub": ", ".join(subs) if subs else "Sem substatus"
                        })
                icon_url = getattr(agent, "square_icon", getattr(agent, "rectangle_icon", getattr(agent, "icon", "")))
                hoyolab_splash = getattr(agent, "portrait", getattr(agent, "draw", getattr(agent, "art_url", getattr(agent, "banner_icon", getattr(agent, "rectangle_icon", getattr(agent, "full_icon", icon_url))))))
                outfit_id = getattr(agent, "outfit_id", None)
                has_skin = bool(outfit_id) or (bool(hoyolab_splash) and any(p.isdigit() and len(p) >= 7 for p in str(hoyolab_splash).split("_")))
                
                costumes = getattr(agent, "costumes", getattr(agent, "skins", getattr(agent, "outfits", None)))
                if costumes:
                    c_item = costumes[0]
                    icon_url = getattr(c_item, "square_icon", getattr(c_item, "icon", icon_url))
                    c_splash = getattr(c_item, "portrait", getattr(c_item, "draw", getattr(c_item, "art_url", getattr(c_item, "banner_icon", getattr(c_item, "vertical_painting", getattr(c_item, "full_icon", getattr(c_item, "gacha_art", getattr(c_item, "splash_art", getattr(c_item, "rectangle_icon", getattr(c_item, "icon", None))))))))))
                    if c_splash:
                        hoyolab_splash = c_splash
                        has_skin = True

                if has_skin and hoyolab_splash:
                    splash_url = hoyolab_splash
                else:
                    zzz_slug = get_zzz_prydwen_slug(agent.name)
                    prydwen_splash = f"https://cdn.prydwen.gg/images/zenless-zone-zero/characters/{zzz_slug}_full.webp" if zzz_slug else ""
                    splash_url = prydwen_splash if prydwen_splash else hoyolab_splash
                rarity_num = 5 if str(agent.rarity).upper() in ["S", "5"] else 4

                # Extrai Status Finais (Final Stats) do Agente ZZZ
                zzz_stats = {}
                try:
                    full_agents = await self.client.get_zzz_agent_info([agent.id], uid=zzz_account.uid)
                    if not isinstance(full_agents, list): full_agents = [full_agents]
                    full_agent = full_agents[0] if full_agents else None
                    if full_agent:
                        for prop in (getattr(full_agent, "properties", []) or []):
                            p_name = getattr(prop, "name", None)
                            p_final = getattr(prop, "final", getattr(prop, "value", ""))
                            if p_name and p_final and str(p_final) not in ('', '0', '0.0%', '0.0'):
                                label = sanitize_stat_name(p_name)
                                zzz_stats[label] = str(p_final)
                except Exception:
                    pass

                char_json_list.append({
                    "id": str(agent.id),
                    "name": agent.name,
                    "level": agent.level,
                    "rarity": rarity_num,
                    "rank_str": f"M{agent.rank}",
                    "element": getattr(agent.element, "name", str(agent.element)),
                    "icon": icon_url,
                    "gacha_art": splash_url,
                    "weapon": w_info,
                    "relics": discs_json,
                    "stats": zzz_stats
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
            
        # Salva no SQLite
        try:
            import database
            database.save_game_account(uid, "zzz", zzz_acc.nickname if hasattr(zzz_acc, "nickname") else "Proxy", zzz_acc.level, getattr(user_data.stats, "active_days", 0))
            for c in char_json_list:
                char_md = ""
                pattern = rf'(\*\*(?:Agente):\*\*\s*{re.escape(c["name"])}.*?)(?=\n\*\*(?:Agente)|\n## |\Z)'
                match = re.search(pattern, markdown_content, re.DOTALL | re.I)
                if match:
                    char_md = match.group(1).strip()
                # NOTA: O arquivo database.py e a tabela SQLite precisarão ser atualizados para receber a nova coluna char_id
                database.save_character(
                    uid=uid,
                    game_id="zzz",
                    char_id=str(c["id"]),
                    name=c["name"],
                    level=c["level"],
                    rarity=c["rarity"],
                    rank_str=c["rank_str"],
                    element=c["element"],
                    icon=c["icon"],
                    gacha_art=c.get("gacha_art"),
                    weapon_name=c["weapon"].get("name") if c["weapon"] else None,
                    weapon_level=c["weapon"].get("level") if c["weapon"] else None,
                    weapon_rank=c["weapon"].get("rank") if c["weapon"] else None,
                    weapon_icon=c["weapon"].get("icon") if c["weapon"] else None,
                    raw_md=char_md
                )
                database.clear_character_relics(uid, c["name"])
                for r in c["relics"]:
                    database.save_relic(
                        uid=uid,
                        character_name=c["name"],
                        name=r["name"],
                        slot=r["slot"],
                        main_stat=r["main"],
                        sub_stats=r["sub"],
                        icon=r["icon"]
                    )
            print("[INFO] Roster ZZZ salvo com sucesso no banco de dados SQLite.")
        except Exception as sqlite_err:
            print(f"Aviso ao salvar ZZZ no SQLite: {sqlite_err}")

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
