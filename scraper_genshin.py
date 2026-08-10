import os
import re
import json
import requests
from bs4 import BeautifulSoup

class PrydwenGenshinScraper:
    def __init__(self):
        """
        Inicializa o raspador do Genshin Impact no Prydwen com headers realistas.
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
        self.base_url = "https://www.prydwen.gg/genshin-impact"
        self.domain = "https://www.prydwen.gg"

    def get_character_list(self) -> list:
        """
        Acessa a página de personagens de Genshin Impact no Prydwen e extrai nomes e URLs.
        
        Retorna:
            list: Lista de dicionários contendo {'name': Nome, 'url': URL_Completa}.
        """
        url = f"{self.base_url}/characters"
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Falha de conexão ao carregar lista de personagens de Genshin: {e}")
            
        soup = BeautifulSoup(r.text, 'html.parser')
        characters = []
        seen_slugs = set()
        
        for link in soup.find_all('a'):
            href = link.get('href', '').strip()
            if '/genshin-impact/characters/' in href:
                rel = href.split('/genshin-impact/characters/')[-1].strip('/')
                if not rel or '/' in rel or rel in ['characters', 'rarity', 'element', 'weapon', 'role']:
                    continue
                if rel.endswith('-calculations') or rel.endswith('-synergy'):
                    continue
                    
                if rel not in seen_slugs:
                    seen_slugs.add(rel)
                    raw_name = link.text.strip()
                    if raw_name:
                        name = re.sub(r'\d+\.\d+$', '', raw_name).strip()
                        name = re.sub(r'New$', '', name).strip()
                    else:
                        name = rel.replace('-', ' ').title()
                        
                    full_url = self.domain + href if href.startswith('/') else href
                    characters.append({
                        "name": name,
                        "url": full_url
                    })
                    
        return sorted(characters, key=lambda x: x["name"])

    def translate_to_portuguese(self, text: str) -> str:
        """
        Traduz termos comuns de Genshin Impact de inglês para português.
        """
        replacements = {
            "Energy Recharge": "Recarga de Energia",
            "CRIT Rate": "Taxa Crítica",
            "CRIT DMG": "Dano Crítico",
            "Elemental Mastery": "Maestria Elemental",
            "Hydro DMG Bonus": "Bônus de Dano Hydro",
            "Pyro DMG Bonus": "Bônus de Dano Pyro",
            "Electro DMG Bonus": "Bônus de Dano Electro",
            "Anemo DMG Bonus": "Bônus de Dano Anemo",
            "Cryo DMG Bonus": "Bônus de Dano Cryo",
            "Geo DMG Bonus": "Bônus de Dano Geo",
            "Dendro DMG Bonus": "Bônus de Dano Dendro",
            "Physical DMG Bonus": "Bônus de Dano Físico",
            "Hydro DMG": "Bônus de Dano Hydro",
            "Pyro DMG": "Bônus de Dano Pyro",
            "Electro DMG": "Bônus de Dano Electro",
            "Anemo DMG": "Bônus de Dano Anemo",
            "Cryo DMG": "Bônus de Dano Cryo",
            "Geo DMG": "Bônus de Dano Geo",
            "Dendro DMG": "Bônus de Dano Dendro",
            "Physical DMG": "Bônus de Dano Físico",
            "ATK%": "ATK%",
            "HP%": "HP%",
            "DEF%": "DEF%",
            "Healing Bonus": "Bônus de Cura",
            "Healing%": "Bônus de Cura",
            "Healing": "Bônus de Cura",
            "Sands": "Ampulheta (Sands)",
            "Goblet": "Cálice (Goblet)",
            "Circlet": "Tiara (Circlet)",
            "Normal Attack": "Ataque Básico",
            "Elemental Skill": "Habilidade Elemental",
            "Elemental Burst": "Suprema (Elemental Burst)",
            "Passive Talents": "Talentos Passivos",
            "Constellations": "Constelações",
            "Constellation": "Constelação",
            "Artifact Sets": "Conjuntos de Artefatos",
            "Artifact Set": "Conjunto de Artefatos",
            "Weapons": "Armas",
            "Weapon": "Arma",
            "Main Stats": "Atributos Principais",
            "Substats": "Substatus",
            "Substat Priority": "Prioridade de Substatus",
            "Vaporize": "Vaporização",
            "Melt": "Fusão",
            "Overload": "Sobrecarga",
            "Electro-Charged": "Eletrocultivo",
            "Superconduct": "Superconduta",
            "Hyperbloom": "Hiperflorescimento",
            "Burgeon": "Germinação",
            "Bloom": "Florescimento",
            "Swirl": "Redemoinho",
            "Crystallize": "Cristalização",
        }
        
        sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
        pattern = re.compile("|".join(re.escape(k) for k in sorted_keys), re.IGNORECASE)
        
        def replacer(match):
            matched_str = match.group(0)
            for k in sorted_keys:
                if k.lower() == matched_str.lower():
                    return replacements[k]
            return matched_str
            
        return pattern.sub(replacer, text)

    def scrape_character_guide(self, character_name: str, url: str) -> dict:
        """
        Raspa a página de guia de um personagem de Genshin e extrai dados estruturados.
        """
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.raise_for_status()
        except requests.HTTPError as he:
            raise Exception(f"Erro HTTP {he.response.status_code} ao acessar guia de {character_name}")
        except Exception as e:
            raise Exception(f"Falha ao acessar guia de {character_name}: {e}")
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        data = {
            "weapons": [],
            "artifacts": [],
            "stats_main": [],
            "stats_sub": "",
            "stats_info": "",
            "talent_priority": "",
            "skills_active": [],
            "skills_passives": [],
            "constellations": [],
            "synergies": [],
            "teams": []
        }

        # 1. ARMAS (Curadas via weapon-rank-table)
        for w_table in soup.find_all('div', class_='weapon-rank-table'):
            for row in w_table.find_all('div', class_='build-rank-row'):
                a_tag = row.find('a', class_='loadout-item')
                w_name = a_tag.find('strong').get_text().strip() if a_tag and a_tag.find('strong') else ''
                dupes = row.find('span', class_='build-gear-dupes')
                r_val = f" ({dupes.get_text().strip()})" if dupes else ""
                note = row.find('span', class_='weapon-note')
                note_txt = f" - {note.get_text().strip()}" if note else ""
                if w_name:
                    data["weapons"].append(f"**{w_name}{r_val}**{note_txt}")

        # 1b. Fallback de Armas via Estatísticas de Uso (usage-list-card)
        if not data["weapons"]:
            for card in soup.find_all('article', class_='usage-list-card'):
                label = card.find('span', class_='mini-label')
                if label and 'weapon' in label.get_text().lower():
                    for row in card.find_all('div', class_='usage-row'):
                        a_tag = row.find('a')
                        w_name = a_tag.get_text().strip() if a_tag else ''
                        pct = row.find('strong')
                        pct_txt = f" ({pct.get_text().strip()})" if pct else ""
                        if w_name:
                            data["weapons"].append(f"**{w_name}**{pct_txt}")

        # 2. ARTEFATOS (Curados via artifact-rank-table)
        for a_table in soup.find_all('div', class_='artifact-rank-table'):
            for row in a_table.find_all('div', class_='build-rank-row'):
                a_tag = row.find('a', class_='loadout-item')
                a_name = a_tag.find('strong').get_text().strip() if a_tag and a_tag.find('strong') else ''
                note = row.find('span', class_='artifact-note')
                note_txt = f" - {note.get_text().strip()}" if note else ""
                if a_name:
                    data["artifacts"].append(f"**{a_name}**{note_txt}")

        # 2b. Fallback de Artefatos via Estatísticas de Uso (usage-list-card)
        if not data["artifacts"]:
            seen_art = set()
            for card in soup.find_all('article', class_='usage-list-card'):
                label = card.find('span', class_='mini-label')
                if label and 'artifact' in label.get_text().lower():
                    for row in card.find_all('div', class_='usage-row'):
                        a_tag = row.find('a')
                        a_name = a_tag.get_text().strip() if a_tag else ''
                        pct = row.find('strong')
                        pct_txt = f" ({pct.get_text().strip()})" if pct else ""
                        if a_name and a_name not in seen_art:
                            seen_art.add(a_name)
                            data["artifacts"].append(f"**{a_name}**{pct_txt}")

        # 3. STATS PRINCIPAIS (Curados via main-stat-row)
        for row in soup.find_all('div', class_='main-stat-row'):
            slot_span = row.find('div', class_='main-stat-slot')
            slot = slot_span.get_text().strip() if slot_span else ""
            strong = row.find('strong')
            val = strong.get_text().strip() if strong else ""
            if slot and val:
                data["stats_main"].append({
                    "slot": slot,
                    "value": val
                })

        # 3b. Fallback de Stats Principais via Estatísticas de Uso (main-stat-card)
        if not data["stats_main"]:
            for card in soup.find_all('article', class_='main-stat-card'):
                label_elem = card.find('span', class_='mini-label')
                slot_name = label_elem.get_text().strip() if label_elem else ""
                top_stats = []
                for r_item in card.find_all('div', class_='stat-bar-row'):
                    s_name = r_item.find('span')
                    s_val = r_item.find('strong')
                    if s_name and s_val:
                        try:
                            val_pct = float(s_val.get_text().replace('%', '').strip())
                            if val_pct >= 5.0:
                                top_stats.append(s_name.get_text().strip())
                        except ValueError:
                            pass
                if slot_name and top_stats:
                    data["stats_main"].append({
                        "slot": slot_name,
                        "value": " / ".join(top_stats[:2])
                    })

        # 4. SUBSTATS PRIORITY (via stat-priority-strip)
        for strip in soup.find_all('div', class_='stat-priority-strip'):
            sub_val = strip.get('aria-label') or strip.get_text(separator=' ').strip()
            if sub_val:
                data["stats_sub"] = sub_val.strip()

        # 4b. PRIORIDADE DE TALENTOS (via talent-priority-strip)
        for t_strip in soup.find_all('div', class_=lambda c: c and 'talent-priority-strip' in c):
            aria_p = t_strip.get('aria-label')
            if aria_p:
                data["talent_priority"] = aria_p.strip()
                break
        if not data["talent_priority"]:
            for grid in soup.find_all('div', class_=re.compile('investment-priority|build-stats')):
                gtxt = grid.get_text(separator=' ').strip()
                match = re.search(r'Talents?\s*[:\=]?\s*([A-Za-z0-9\s\>\=\+\-]+)', gtxt, re.IGNORECASE)
                if match:
                    data["talent_priority"] = match.group(1).strip()
                    break

        # Observações e informações adicionais
        for info in soup.find_all('div', class_=re.compile('build-energy|statistics|information')):
            itxt = info.get_text(separator=' ').strip()
            itxt = re.sub(r'\s+', ' ', itxt)
            if itxt and len(itxt) > 10 and itxt not in data["stats_info"]:
                data["stats_info"] += ("\n" + itxt)

        # 5. Habilidades Ativas
        for skill_item in soup.find_all('div', class_='skill-database-header'):
            stitle = skill_item.get_text(separator=' ').strip()
            sdesc_elem = skill_item.find_next_sibling('div')
            sdesc = sdesc_elem.get_text(separator=' ').strip() if sdesc_elem else ""
            if stitle:
                data["skills_active"].append({"name": stitle, "description": re.sub(r'\s+', ' ', sdesc)})

        # 6. Talentos Passivos
        for pass_grid in soup.find_all('div', class_='passive-database-grid'):
            ptxt = pass_grid.get_text(separator=' ').strip()
            ptxt = re.sub(r'\s+', ' ', ptxt)
            if ptxt:
                data["skills_passives"].append(ptxt)

        # 7. Constelações
        for c_list in soup.find_all('div', class_='constellation-database-list'):
            ctxt = c_list.get_text(separator=' ').strip()
            ctxt = re.sub(r'\s+', ' ', ctxt)
            if ctxt:
                data["constellations"].append(ctxt)

        # 8. Sinergias e Times
        for sec in soup.find_all('div', class_=re.compile('subsection|synergy|team')):
            stxt = sec.get_text(separator=' ').strip()
            stxt = re.sub(r'\s+', ' ', stxt)
            if 'synerg' in stxt.lower() or 'team' in stxt.lower():
                if len(stxt) > 20 and stxt not in data["synergies"]:
                    data["synergies"].append(stxt)

        return data

    def save_to_markdown(self, character_name: str, data: dict, output_dir: str = "genshin/guias") -> str:
        """
        Salva o guia de um personagem em formato Markdown.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        lines = []
        lines.append(f"# Guia de Build - {character_name}")
        lines.append("Dados extraídos do site Prydwen.gg.")
        lines.append("")
        
        # 1. RECOMENDAÇÕES DE BUILD (ARMAS E ARTEFATOS)
        lines.append("## Melhores Armas e Artefatos")
        lines.append("")
        
        lines.append("### Armas Recomendadas")
        if data["weapons"]:
            for w in data["weapons"]:
                w_trans = self.translate_to_portuguese(w)
                lines.append(f"- {w_trans}")
            lines.append("")
        else:
            lines.append("Nenhuma arma listada.")
            lines.append("")
            
        lines.append("### Conjuntos de Artefatos Recomendados")
        if data["artifacts"]:
            for a in data["artifacts"]:
                a_trans = self.translate_to_portuguese(a)
                lines.append(f"- {a_trans}")
            lines.append("")
        else:
            lines.append("Nenhum conjunto de artefatos listado.")
            lines.append("")

        # 2. ATRIBUTOS RECOMENDADOS
        lines.append("## Atributos Recomendados (Stats)")
        lines.append("")
        
        if data["stats_main"]:
            lines.append("### Atributos Principais (Main Stats)")
            for sm in data["stats_main"]:
                slot_trans = self.translate_to_portuguese(sm["slot"])
                val_trans = self.translate_to_portuguese(sm["value"])
                lines.append(f"- **{slot_trans}:** {val_trans}")
            lines.append("")

        if data["stats_sub"]:
            lines.append("### Subatributos Prioritários (Sub-stats)")
            sub_trans = self.translate_to_portuguese(data["stats_sub"])
            lines.append(sub_trans)
            lines.append("")
            
        if data.get("talent_priority"):
            lines.append("### Prioridade de Talentos")
            talent_trans = self.translate_to_portuguese(data["talent_priority"])
            lines.append(talent_trans)
            lines.append("")
            
        if data["stats_info"]:
            lines.append("### Observações e Atributos Secundários")
            info_trans = self.translate_to_portuguese(data["stats_info"].strip())
            lines.append(info_trans)
            lines.append("")

        # 3. MECÂNICAS DO KIT & CONSTELAÇÕES
        lines.append("## Habilidades e Constelações")
        lines.append("")
        
        if data["skills_active"]:
            lines.append("### Habilidades Ativas")
            for sk in data["skills_active"]:
                lines.append(f"- **{sk['name']}**")
                if sk['description']:
                    lines.append(f"  {sk['description']}")
                lines.append("")
                
        if data["skills_passives"]:
            lines.append("### Talentos Passivos")
            for p in data["skills_passives"]:
                lines.append(f"- {p}")
            lines.append("")
            
        if data["constellations"]:
            lines.append("### Constelações")
            for c in data["constellations"]:
                lines.append(f"- {c}")
            lines.append("")

        # 4. SINERGIAS E TIMES
        if data["synergies"]:
            lines.append("## Sinergias e Composições de Time")
            lines.append("")
            for syn in data["synergies"]:
                syn_trans = self.translate_to_portuguese(syn)
                lines.append(f"- {syn_trans}")
            lines.append("")

        markdown_content = "\n".join(lines)
        
        filename_clean = character_name.lower().replace(" ", "_").replace(":", "").replace("(", "").replace(")", "").replace("'", "") + ".md"
        filepath = os.path.join(output_dir, filename_clean)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return filepath

    def scrape_tier_list(self) -> dict:
        """
        Raspa a Tier List de Genshin Impact no Prydwen.
        """
        url = f"{self.base_url}/tier-list"
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Falha de conexão ao carregar Tier List de Genshin: {e}")
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        tier_data = {
            "title": "Genshin Impact Tier List - Prydwen.gg",
            "tiers": []
        }
        
        for c_tier in soup.find_all('div', class_='custom-tier'):
            header_elem = c_tier.find('div', class_='custom-tier-header')
            header_title = header_elem.get_text().strip() if header_elem else "Tier"
            
            chars = []
            for link in c_tier.find_all('a'):
                href = link.get('href', '')
                if '/genshin-impact/characters/' in href:
                    cname = link.text.strip()
                    if cname and cname not in chars:
                        chars.append(cname)
                        
            if chars:
                tier_data["tiers"].append({
                    "category": header_title,
                    "characters": chars
                })
                
        return tier_data

    def save_meta_to_markdown(self, output_filepath: str = "genshin/meta_endgame_genshin.md") -> str:
        """
        Salva os dados de meta e Tier List de Genshin em arquivo Markdown.
        """
        os.makedirs(os.path.dirname(output_filepath) or ".", exist_ok=True)
        tier_data = self.scrape_tier_list()
        
        lines = []
        lines.append("# Genshin Impact - Meta & Tier List (Prydwen.gg)")
        lines.append("Relatório consolidado de avaliação de personagens extraído do Prydwen.gg.")
        lines.append("")
        
        lines.append("## Tier List de Personagens")
        lines.append("")
        
        if tier_data["tiers"]:
            for t in tier_data["tiers"]:
                lines.append(f"### {t['category']}")
                char_list_str = ", ".join(t['characters'])
                lines.append(f"**Personagens:** {char_list_str}")
                lines.append("")
        else:
            lines.append("Nenhum dado de Tier List encontrado.")
            lines.append("")
            
        lines.append("---")
        lines.append("Análise consolidada extraída do site Prydwen.gg.")
        
        markdown_content = "\n".join(lines)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return output_filepath

if __name__ == "__main__":
    scraper = PrydwenGenshinScraper()
    print("Testando busca de lista de personagens Genshin...")
    chars = scraper.get_character_list()
    print(f"Encontrados {len(chars)} personagens.")
    if chars:
        first = chars[0]
        print(f"Raspando primeiro personagem: {first['name']} ({first['url']})...")
        guide_data = scraper.scrape_character_guide(first["name"], first["url"])
        path = scraper.save_to_markdown(first["name"], guide_data)
        print(f"Salvo em {path}")
    print("Testando raspagem da Tier List...")
    meta_path = scraper.save_meta_to_markdown()
    print(f"Tier list salva em {meta_path}")
