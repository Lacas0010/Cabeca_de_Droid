import os
import re
import json
from curl_cffi import requests
from bs4 import BeautifulSoup

class PrydwenZZZScraper:
    def __init__(self):
        """
        Inicializa o raspador de ZZZ do Prydwen com headers realistas para evitar bloqueios.
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        self.base_url = "https://www.prydwen.gg/zenless"
        self.domain = "https://www.prydwen.gg"

    def get_agent_list(self) -> list:
        """
        Acessa a página de personagens de ZZZ no Prydwen e extrai seus nomes e URLs.
        
        Retorna:
            list: Lista de dicionários contendo {'name': Nome, 'url': URL_Completa}.
        """
        url = f"{self.base_url}/characters"
        try:
            r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=30)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Falha de conexão ao carregar lista de agentes ZZZ: {e}")
            
        soup = BeautifulSoup(r.text, 'html.parser')
        agents = []
        seen_urls = set()
        
        # Encontra todos os links de personagens
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if '/zenless/characters/' in href:
                clean_href = href.strip()
                if clean_href not in seen_urls:
                    slug = clean_href.split('/')[-1]
                    # Ignora links genéricos de filtro ou sub-rotas
                    if not slug or slug == 'characters' or slug.endswith('-calculations') or slug.endswith('-synergy'):
                        continue
                        
                    seen_urls.add(clean_href)
                    name = link.text.strip()
                    if not name:
                        name = slug.replace('-', ' ').title()
                        
                    full_url = self.domain + clean_href if clean_href.startswith('/') else clean_href
                    agents.append({
                        "name": name,
                        "url": full_url
                    })
                    
        return sorted(agents, key=lambda x: x["name"])

    def translate_to_portuguese(self, text: str) -> str:
        """
        Traduz termos comuns de ZZZ de inglês para português de forma segura.
        """
        replacements = {
            "W-Engine": "W-Engine",
            "W-Engines": "W-Engines",
            "Audio Discs": "Discos de Áudio",
            "Audio Disc": "Disco de Áudio",
            "Disk Drives": "Discos de Áudio",
            "Disk Drive": "Disco de Áudio",
            "Disk Sets": "Conjuntos de Discos",
            "Disk Set": "Conjunto de Discos",
            "Mindscape Cinema": "Cinema de Mente",
            "Mindscape Cinemas": "Cinemas de Mente",
            "Mindscape": "Cinema (Mindscape)",
            "Mindscapes": "Cinemas (Mindscapes)",
            "Anomaly Mastery": "Maestria de Anomalia",
            "Anomaly Proficiency": "Proficiência de Anomalia",
            "Impact": "Impacto",
            "Daze": "Atordoamento (Daze)",
            "PEN Rate": "Taxa de Perfuração",
            "PEN": "Perfuração",
            "Energy Regen": "Recuperação de Energia",
            "Basic Attack": "Ataque Básico",
            "Dodge Counter": "Contra-ataque de Esquiva",
            "Dodge": "Esquiva",
            "Special Attack": "Ataque Especial",
            "EX Special Attack": "Ataque Especial EX",
            "Chain Attack": "Ataque em Cadeia",
            "Ultimate": "Suprema (Ultimate)",
            "Assist Follow-Up": "Ataque de Suporte",
            "Defensive Assist": "Suporte Defensivo",
            "Quick Assist": "Suporte Rápido",
            "Additional Ability": "Habilidade Adicional",
            "Core Passive": "Passiva de Núcleo",
            "Core Passive Bonuses": "Bônus de Passiva de Núcleo",
            "Substats": "Substatus",
            "CRIT Rate": "Taxa Crítica",
            "CRIT DMG": "Dano Crítico",
            "Electric DMG Bonus": "Bônus de Dano Elétrico",
            "Electric DMG": "Dano Elétrico",
            "Physical DMG Bonus": "Bônus de Dano Físico",
            "Physical DMG": "Dano Físico",
            "Fire DMG Bonus": "Bônus de Dano de Fogo",
            "Fire DMG": "Dano de Fogo",
            "Ice DMG Bonus": "Bônus de Dano de Gelo",
            "Ice DMG": "Dano de Gelo",
            "Ether DMG Bonus": "Bônus de Dano de Éter",
            "Ether DMG": "Dano de Éter",
            "Wind DMG Bonus": "Bônus de Dano de Vento",
            "Wind DMG": "Dano de Vento",
            "Shiyu Defense": "Defesa de Shiyu",
            "Deadly Assault": "Assalto Mortal (Deadly Assault)",
            "pros": "Prós",
            "cons": "Contras",
            "Pros": "Prós",
            "Cons": "Contras",
            "Support": "Suporte",
            "Stun": "Atordoamento (Stun)",
            "Anomaly": "Anomalia",
            "Attack": "Ataque",
            "Defense": "Defesa",
        }
        sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
        pattern = re.compile("|".join(rf"\b{re.escape(k)}\b" for k in sorted_keys), re.IGNORECASE)
        
        def replacer(match):
            matched_str = match.group(0)
            for k in sorted_keys:
                if k.lower() == matched_str.lower():
                    return replacements[k]
            return matched_str
            
        return pattern.sub(replacer, text)

    def scrape_agent_guide(self, agent_name: str, url: str) -> dict:
        """
        Raspa a página de guia de um Agente do ZZZ e estrutura os dados.
        """
        try:
            r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=30)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Falha ao acessar o guia de {agent_name}: {e}")
            
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {
            "pros": [],
            "cons": [],
            "review": [],
            "skills_active": [],
            "skills_passives": [],
            "skills_mindscapes": [],
            "w_engines": [],
            "discs": [],
            "disk_sets": [],
            "stats_main": [],
            "stats_sub": "",
            "stats_info": "",
            "stats_endgame": [],
            "talent_priority": "",
            "teams": []
        }

        # Extrai ZZZ Skill Priority (skill-priority)
        sp_div = soup.find('div', class_=lambda c: c and 'skill-priority' in c)
        if sp_div:
            items = [s.get_text().strip() for s in sp_div.find_all(['span', 'strong', 'div']) if s.get_text().strip() and len(s.get_text().strip()) < 30]
            seen = set()
            clean_items = [x for x in items if not (x in seen or seen.add(x))]
            if clean_items:
                data["talent_priority"] = " > ".join(clean_items)
        tabs_div = soup.find('div', class_='tabs')
        if not tabs_div:
            return data
            
        divs = [sibling for sibling in tabs_div.next_siblings if sibling.name == 'div' and sibling.get('class') and 'tab-inside' in sibling.get('class')]
        if len(divs) < 4:
            return data
            
        # --- 1. ABA 0: KIT DE HABILIDADES ---
        tab_kit = divs[0]
        for header in tab_kit.find_all(class_='skill-header'):
            header_text = header.get_text(separator=' ').strip()
            header_text = re.sub(r'\s+', ' ', header_text)
            
            desc_div = header.find_next_sibling('div')
            desc_text = desc_div.get_text().strip() if desc_div else ""
            desc_text = re.sub(r'\s+', ' ', desc_text)
            
            item = {"name": header_text, "description": desc_text}
            
            header_lower = header_text.lower()
            if any(m in header_lower for m in ["m1", "m2", "m3", "m4", "m5", "m6", "mindscape"]):
                data["skills_mindscapes"].append(item)
            elif any(p in header_lower for p in ["core passive", "additional ability"]):
                data["skills_passives"].append(item)
            else:
                data["skills_active"].append(item)

        # --- 2. ABA 1: REVIEW ---
        tab_review = divs[1]
        
        # Pros
        pros_box = tab_review.find('div', class_='pros')
        if pros_box:
            data["pros"] = [li.text.strip() for li in pros_box.find_all('li')]
            
        # Cons
        cons_box = tab_review.find('div', class_='cons')
        if cons_box:
            data["cons"] = [li.text.strip() for li in cons_box.find_all('li')]
            
        # Review text
        for sec in tab_review.find_all('div', class_='section-analysis'):
            for p in sec.find_all('p'):
                p_text = p.text.strip()
                if p_text:
                    data["review"].append(p_text)

        # --- 3. ABA 2: BUILDS ---
        tab_build = divs[2]
        
        current_section = ""
        for el in tab_build.find_all():
            if el.name == 'div' and el.get('class') and 'content-header' in el.get('class'):
                current_section = el.text.strip()
            elif el.name == 'div' and el.get('class') and 'single-item' in el.get('class'):
                img = el.find('img')
                name = img.get('alt', '').strip() if img else ''
                
                pct_el = el.find('div', class_='percentage')
                pct = pct_el.get_text().strip() if pct_el else ''
                pct = "/".join(pct.split())
                
                sup = el.find('span', class_='cone-super').text.strip() if el.find('span', class_='cone-super') else ''
                if not sup:
                    m = re.search(r'\(\d+-PC\)', el.get_text())
                    if m:
                        sup = m.group(0)
                        
                just_div = el.find_next_sibling('div', class_='information')
                just = just_div.text.strip() if just_div else ''
                
                item_data = {
                    "name": name,
                    "percentage": pct,
                    "super": sup,
                    "justification": just
                }
                
                if "W-Engines" in current_section:
                    data["w_engines"].append(item_data)
                elif "Disk Drives Sets" in current_section:
                    data["disk_sets"].append(item_data)

        # Stats recomendados (Disk 4, 5, 6 e Substats)
        inner_tips = tab_build.find_all('div', class_='build-tips')
        for tip in inner_tips:
            main_stats_div = tip.find('div', class_='main-stats')
            if main_stats_div:
                for box in main_stats_div.find_all('div', class_='box'):
                    data["stats_main"].append(box.get_text(separator=' ').strip())
                    
            sub_div = tip.find('div', class_='flex-wrap') or tip.find(class_=re.compile('flex.*wrap'))
            if sub_div and "Substats:" in sub_div.text:
                data["stats_sub"] = sub_div.text.replace("Substats:", "").strip()

        # Stats de Endgame
        endgame_div = tab_build.find('div', class_='endgame-stats')
        if endgame_div:
            ul = endgame_div.find('ul')
            if ul:
                for li in ul.find_all('li'):
                    txt = li.get_text(separator=' ').strip()
                    txt = re.sub(r'\s+', ' ', txt)
                    data["stats_endgame"].append(txt)

        # --- 4. ABA 3: TIMES ---
        tab_teams = divs[3]
        for p in tab_teams.find_all('p'):
            txt = p.text.strip()
            if txt and len(txt) > 20 and not txt.startswith("Teams & Synergy"):
                data["teams"].append(txt)
                
        return data

    def save_to_markdown(self, agent_name: str, data: dict, output_dir: str = "zzz/guias") -> str:
        """
        Gera e salva o guia estruturado em formato Markdown.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{agent_name.lower().replace(' ', '_')}.md")
        
        lines = []
        lines.append(f"# Guia de Build - {agent_name}")
        lines.append("Dados extraídos do site Prydwen.gg.")
        lines.append("")
        
        # 1. Review
        lines.append("## Review")
        lines.append("")
        
        if data["pros"]:
            lines.append("### Prós (Pontos Fortes)")
            for pro in data["pros"]:
                lines.append(f"- {self.translate_to_portuguese(pro)}")
            lines.append("")
            
        if data["cons"]:
            lines.append("### Contras (Pontos Fracos)")
            for con in data["cons"]:
                lines.append(f"- {self.translate_to_portuguese(con)}")
            lines.append("")
            
        if data["review"]:
            lines.append("### Análise Detalhada")
            for para in data["review"]:
                lines.append(self.translate_to_portuguese(para))
                lines.append("")
        else:
            lines.append("Nenhuma análise de review disponível.")
            lines.append("")
            
        # 2. Habilidades
        lines.append("## Mecânicas do Kit")
        lines.append("")
        
        if data["skills_active"]:
            lines.append("### Habilidades Ativas")
            for skill in data["skills_active"]:
                lines.append(f"- **{self.translate_to_portuguese(skill['name'])}**")
                lines.append(f"  {self.translate_to_portuguese(skill['description'])}")
                lines.append("")
                
        if data["skills_passives"]:
            lines.append("### Habilidades Passivas")
            for passive in data["skills_passives"]:
                lines.append(f"- **{self.translate_to_portuguese(passive['name'])}**")
                lines.append(f"  {self.translate_to_portuguese(passive['description'])}")
                lines.append("")
                
        if data["skills_mindscapes"]:
            lines.append("### Cinemas de Mente (Mindscapes)")
            for ms in data["skills_mindscapes"]:
                lines.append(f"- **{self.translate_to_portuguese(ms['name'])}**")
                lines.append(f"  {self.translate_to_portuguese(ms['description'])}")
                lines.append("")
                
        # 3. W-Engines
        lines.append("## Melhores W-Engines")
        lines.append("")
        if data["w_engines"]:
            for we in data["w_engines"]:
                pct_str = f" ({we['percentage']})" if we['percentage'] else ""
                sup_str = f" {we['super']}" if we['super'] else ""
                lines.append(f"- **{we['name']}{sup_str}**{pct_str}")
                if we['justification']:
                    lines.append(f"  {self.translate_to_portuguese(we['justification'])}")
                lines.append("")
        else:
            lines.append("Nenhum W-Engine recomendado.")
            lines.append("")
            
        # 4. Discos
        lines.append("## Melhores Discos de Áudio")
        lines.append("")
        if data["disk_sets"]:
            for ds in data["disk_sets"]:
                pct_str = f" ({ds['percentage']})" if ds['percentage'] else ""
                sup_str = f" {ds['super']}" if ds['super'] else ""
                lines.append(f"- **{ds['name']}{sup_str}**{pct_str}")
                if ds['justification']:
                    lines.append(f"  {self.translate_to_portuguese(ds['justification'])}")
                lines.append("")
        else:
            lines.append("Nenhum conjunto de discos de áudio recomendado.")
            lines.append("")
            
        lines.append("### Atributos Recomendados (Stats)")
        lines.append("")
        if data["stats_main"]:
            for stat in data["stats_main"]:
                lines.append(f"- {self.translate_to_portuguese(stat)}")
        if data["stats_sub"]:
            lines.append(f"- Substatus prioritários: {self.translate_to_portuguese(data['stats_sub'])}")
        lines.append("")
        
        if data["stats_endgame"]:
            lines.append("### Atributos Finais Recomendados (Endgame Stats)")
            lines.append("")
            for stat in data["stats_endgame"]:
                lines.append(f"- {self.translate_to_portuguese(stat)}")
            lines.append("")
            
        # 5. Times
        lines.append("## Sinergias e Composições de Times")
        lines.append("")
        if data["teams"]:
            for team in data["teams"]:
                lines.append(self.translate_to_portuguese(team))
                lines.append("")
        else:
            lines.append("Nenhuma composição recomendada disponível.")
            lines.append("")
            
        markdown_content = "\n".join(lines)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filename

    def scrape_tier_list(self) -> dict:
        """
        Acessa a tier list de ZZZ no Prydwen e extrai o changelog e a classificação por tier.
        """
        url = f"{self.domain}/zenless/tier-list"
        try:
            r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=30)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Falha ao carregar Tier List de ZZZ: {e}")
            
        html = r.text
        
        # Reconstrói os pushes do Next.js
        payloads = []
        for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html):
            payloads.append(match.group(1))
        for match in re.finditer(r"self\.__next_f\.push\(\[\d+,\s*'(.*?)'\]\)", html):
            payloads.append(match.group(1))
            
        combined = "".join(payloads).replace('\\\\', '\\')
        unescaped = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), combined)
        unescaped = unescaped.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
        
        payload_soup = BeautifulSoup(unescaped, 'html.parser')
        
        # 1. Changelog
        changelog = []
        for heading in payload_soup.find_all(['h5', 'h6', 'h4']):
            h_text = heading.text.strip()
            if re.search(r'\d{1,2}/[A-Za-z]+/\d{4}', h_text) or "changelog" in h_text.lower():
                entry = {
                    "title": h_text,
                    "paragraphs": []
                }
                sibling = heading.find_next_sibling()
                while sibling and sibling.name in ['p', 'ul', 'ol', 'div'] and 'meta-line' not in sibling.get('class', []):
                    text = sibling.get_text(separator=' ').strip()
                    if text:
                        text = re.sub(r'\s+', ' ', text)
                        entry["paragraphs"].append(self.translate_to_portuguese(text))
                    sibling = sibling.find_next_sibling()
                if entry["paragraphs"]:
                    changelog.append(entry)
                    
        # 2. Personagens & Ratings
        characters = []
        idx = unescaped.find('"characters":')
        if idx != -1:
            start_pos = idx + len('"characters":')
            bracket_count = 0
            end_pos = start_pos
            for i in range(start_pos, len(unescaped)):
                if unescaped[i] == '[':
                    bracket_count += 1
                elif unescaped[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_pos = i + 1
                        break
            try:
                characters = json.loads(unescaped[start_pos:end_pos])
            except Exception as e:
                print(f"Erro ao converter JSON de personagens: {e}")
                
        return {
            "changelog": changelog,
            "characters": characters
        }

    def _parse_endgame_page(self, page_name: str) -> dict:
        url = f"{self.domain}/zenless/{page_name}"
        try:
            r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"Aviso: Não foi possível obter dados de {page_name}: {e}")
            return {"characters": [], "teams": []}
            
        html = r.text
        payloads = []
        for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html):
            payloads.append(match.group(1))
        for match in re.finditer(r"self\.__next_f\.push\(\[\d+,\s*'(.*?)'\]\)", html):
            payloads.append(match.group(1))
            
        combined = "".join(payloads).replace('\\\\', '\\')
        unescaped = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), combined)
        unescaped = unescaped.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
        
        # 1. Extrai estatísticas dos personagens
        char_list = []
        idx_char = unescaped.find('"current_app_rate"')
        if idx_char != -1:
            start_pos = unescaped.rfind('[', 0, idx_char)
            bracket_count = 0
            end_pos = start_pos
            for i in range(start_pos, len(unescaped)):
                if unescaped[i] == '[':
                    bracket_count += 1
                elif unescaped[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_pos = i + 1
                        break
            try:
                char_list = json.loads(unescaped[start_pos:end_pos])
            except Exception as e:
                print(f"Erro ao converter JSON de stats de {page_name}: {e}")
                
        # 2. Extrai times populares
        teams_list = []
        idx_teams = unescaped.find('"teams":{')
        if idx_teams != -1:
            start_pos = idx_teams + len('"teams":')
            bracket_count = 0
            end_pos = start_pos
            for i in range(start_pos, len(unescaped)):
                if unescaped[i] == '{':
                    bracket_count += 1
                elif unescaped[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_pos = i + 1
                        break
            try:
                teams_obj = json.loads(unescaped[start_pos:end_pos])
                teams_list = teams_obj.get("all", [])
            except Exception as e:
                print(f"Erro ao converter JSON de times de {page_name}: {e}")
                
        return {
            "characters": char_list,
            "teams": teams_list
        }

    def scrape_endgame_stats(self) -> dict:
        """
        Raspa os dados de Shiyu Defense e Deadly Assault.
        """
        shiyu = self._parse_endgame_page("shiyu-defense")
        deadly = self._parse_endgame_page("deadly-assault")
        return {
            "shiyu": shiyu,
            "deadly": deadly
        }

    def save_meta_to_markdown(self, filepath: str = "zzz/meta_endgame_zzz.md") -> str:
        """
        Compila a Tier List + Shiyu Defense + Deadly Assault em um único arquivo Markdown.
        """
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        
        lines = []
        lines.append("# Relatório de Meta de Endgame - Zenless Zone Zero")
        lines.append("Análise consolidada extraída do site Prydwen.gg contendo a Tier List atualizada e dados estatísticos de Shiyu Defense e Deadly Assault.")
        lines.append("")
        
        # 1. TIER LIST
        lines.append("## 1. Zenless Zone Zero Tier List")
        lines.append("")
        
        try:
            tier_data = self.scrape_tier_list()
            
            # Changelog
            if tier_data["changelog"]:
                lines.append("### Notas de Atualização e Análise do Meta (Changelog)")
                lines.append("")
                for entry in tier_data["changelog"]:
                    lines.append(f"#### {entry['title']}")
                    lines.append("")
                    for para in entry["paragraphs"]:
                        lines.append(para)
                        lines.append("")
            
            # Classificação por Tiers
            lines.append("### Classificação dos Agentes por Tier")
            lines.append("Agrupados por Tiers baseados em Deadly Assault (DA) e Shiyu Defense (SD).")
            lines.append("")
            
            rating_map = {
                11: "T0",
                10: "T0.5",
                9: "T1",
                8: "T1.5",
                7: "T2",
                6: "T3"
            }
            
            tier_groups = {label: [] for label in rating_map.values()}
            
            for char in tier_data.get("characters", []):
                name = char.get("name")
                rarity = char.get("rarity", "S")
                element = self.translate_to_portuguese(char.get("element", ""))
                style = self.translate_to_portuguese(char.get("style", ""))
                
                ratings = char.get("tierRatings", [])
                if ratings:
                    r_val = ratings[0].get("rating")
                    category = self.translate_to_portuguese(ratings[0].get("category", ""))
                    tags = ratings[0].get("tags", "")
                    tags_str = f" [{tags}]" if tags else ""
                    
                    if r_val in rating_map:
                        t_label = rating_map[r_val]
                        char_str = f"{name} ({rarity}-Rank {element} - {style}) | Categoria: {category}{tags_str}"
                        tier_groups[t_label].append(char_str)
                        
            for t_label in sorted(tier_groups.keys(), key=lambda x: float(x[1:]) if x[1:].replace('.', '', 1).isdigit() else 99):
                lines.append(f"#### Tier {t_label}")
                if tier_groups[t_label]:
                    for char_line in sorted(tier_groups[t_label]):
                        lines.append(f"- {char_line}")
                else:
                    lines.append("- Nenhum agente classificado neste tier.")
                lines.append("")
                
        except Exception as e:
            lines.append(f"⚠️ Erro ao carregar a Tier List: {e}")
            lines.append("")
            
        # 2. ENDGAME REPORT
        endgame_data = self.scrape_endgame_stats()
        
        # --- SHIYU DEFENSE ---
        lines.append("## 2. Relatório de Shiyu Defense")
        lines.append("")
        shiyu = endgame_data.get("shiyu", {})
        if shiyu.get("characters"):
            # Taxa de Uso (Top 15)
            lines.append("### Taxas de Uso dos Agentes (Top 15)")
            lines.append("")
            sorted_chars = sorted(shiyu["characters"], key=lambda x: x.get("current_app_rate", 0), reverse=True)
            for c in sorted_chars[:15]:
                rate = c.get("current_app_rate", 0) * 100
                prev_rate = c.get("prev_app_rate", 0) * 100
                lines.append(f"- **{c.get('name')}**: {rate:.1f}% (Anterior: {prev_rate:.1f}%)")
            lines.append("")
            
            # Equipes populares (Top 10)
            if shiyu.get("teams"):
                lines.append("### Equipes Mais Populares e Eficientes (Top 10)")
                lines.append("")
                for team in shiyu["teams"][:10]:
                    c1 = team.get("char_one", "").replace("-", " ").title()
                    c2 = team.get("char_two", "").replace("-", " ").title()
                    c3 = team.get("char_three", "").replace("-", " ").title()
                    bangboo = team.get("bangboo", "").replace("-", " ").title()
                    app_rate = team.get("app_rate", 0)
                    avg_round = team.get("avg_round", 0)
                    
                    if avg_round > 1000:
                        time_str = f"{avg_round / 1000:.2f}s"
                    else:
                        time_str = f"{avg_round}"
                        
                    lines.append(f"1. **Composição**: {c1} + {c2} + {c3} (Bangboo: {bangboo})")
                    lines.append(f"   - Taxa de Uso: {app_rate}%")
                    lines.append(f"   - Tempo Médio de Conclusão: {time_str}")
                    lines.append("")
        else:
            lines.append("Estatísticas de Shiyu Defense indisponíveis ou em período de transição.")
            lines.append("")
            
        # --- DEADLY ASSAULT ---
        lines.append("## 3. Relatório de Deadly Assault")
        lines.append("")
        deadly = endgame_data.get("deadly", {})
        if deadly.get("characters"):
            # Taxa de Uso (Top 15)
            lines.append("### Taxas de Uso dos Agentes (Top 15)")
            lines.append("")
            sorted_chars = sorted(deadly["characters"], key=lambda x: x.get("current_app_rate", 0), reverse=True)
            for c in sorted_chars[:15]:
                rate = c.get("current_app_rate", 0) * 100
                prev_rate = c.get("prev_app_rate", 0) * 100
                lines.append(f"- **{c.get('name')}**: {rate:.1f}% (Anterior: {prev_rate:.1f}%)")
            lines.append("")
            
            # Equipes populares (Top 10)
            if deadly.get("teams"):
                lines.append("### Equipes Mais Populares e Eficientes (Top 10)")
                lines.append("")
                for team in deadly["teams"][:10]:
                    c1 = team.get("char_one", "").replace("-", " ").title()
                    c2 = team.get("char_two", "").replace("-", " ").title()
                    c3 = team.get("char_three", "").replace("-", " ").title()
                    bangboo = team.get("bangboo", "").replace("-", " ").title()
                    app_rate = team.get("app_rate", 0)
                    avg_round = team.get("avg_round", 0)
                    
                    if avg_round > 1000:
                        time_str = f"{avg_round / 1000:.2f}s"
                    else:
                        time_str = f"{avg_round}"
                        
                    lines.append(f"1. **Composição**: {c1} + {c2} + {c3} (Bangboo: {bangboo})")
                    lines.append(f"   - Taxa de Uso: {app_rate}%")
                    lines.append(f"   - Tempo Médio de Conclusão: {time_str}")
                    lines.append("")
        else:
            lines.append("Estatísticas de Deadly Assault indisponíveis ou em período de transição.")
            lines.append("")
            
        markdown_content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filepath
