import os
import re
import json
import requests
from bs4 import BeautifulSoup

class PrydwenMetaScraper:
    def __init__(self):
        """
        Inicializa o raspador de meta, tier list e relatórios de endgame da Prydwen.
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        self.url = "https://www.prydwen.gg/star-rail/tier-list"
        self.rating_map = {
            11: "T0",
            10: "T0.5",
            9: "T1",
            8: "T1.5",
            7: "T2",
            6: "T3",
            5: "T4",
            4: "T5"
        }
        
    def translate_to_portuguese(self, text: str) -> str:
        """
        Traduz termos comuns de meta e jogo de inglês para português de forma segura
        em uma única passagem (evitando loops ou substituições duplas).
        """
        replacements = {
            "Memory of Chaos": "Memory of Chaos (MoC)",
            "Pure Fiction": "Pure Fiction (PF)",
            "Apocalyptic Shadow": "Apocalyptic Shadow (AS)",
            "Anomaly Arbitration": "Anomaly Arbitration (AA)",
            "Apex characters": "Personagens Apex (T0 / T0.5)",
            "Meta characters": "Personagens Meta (T1 / T1.5 / T2)",
            "Off-Meta characters": "Personagens Off-Meta (T3 / T4)",
            "The Forgotten Ones": "Os Esquecidos (T5)",
            "Amplifiers": "Amplificadores (Suportes)",
            "Amplifier": "Amplificador (Suporte)",
            "Sustains": "Sustains (Defensores/Curas)",
            "Sustain": "Sustain (Defensor/Cura)",
            "DPS": "DPS (Dano Principal)",
            "Specialist": "Especialista",
            "Support Damage": "Dano de Suporte",
            "tier list": "Tier List",
            "tier lists": "Tier Lists",
            "patch": "patch",
            "debuff": "debuff",
            "debuffs": "debuffs",
            "buff": "buff",
            "buffs": "buffs",
            "Ultimate": "Suprema (Ultimate)",
            "Skill": "Perícia (Skill)",
            "Energy": "Energia",
            "speed": "velocidade",
            "Break": "Break (Quebra)",
            "Elation": "Elation (Júbilo)",
            "Remembrance": "Remembrance (Recordação)",
            "Nihility": "Inexistência (Nihility)",
            "Harmony": "Harmonia (Harmony)",
            "Preservation": "Preservação (Preservation)",
            "Abundance": "Abundância (Abundance)",
            "Destruction": "Destruição (Destruction)",
            "Hunt": "Caça (Hunt)",
            "Erudition": "Erudição (Erudition)",
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

    def scrape_tier_list(self) -> dict:
        """
        Acessa a tier list da Prydwen e extrai:
        1. Histórico de notas de meta (changelog) unescapados do payload RSC.
        2. Lista de personagens e seus ratings de tier para cada modo do JSON do payload.
        """
        try:
            r = requests.get(self.url, headers=self.headers, timeout=15)
            r.raise_for_status()
        except requests.HTTPError as he:
            raise Exception(f"Erro HTTP {he.response.status_code} ao acessar a Tier List")
        except Exception as e:
            raise Exception(f"Falha de conexão ao carregar a Tier List: {e}")
            
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        
        changelog = []
        payloads = []
        
        for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html):
            payloads.append(match.group(1))
        for match in re.finditer(r"self\.__next_f\.push\(\[\d+,\s*'(.*?)'\]\)", html):
            payloads.append(match.group(1))
            
        combined_text = "".join(payloads)
        combined_text = combined_text.replace('\\\\', '\\')
        
        unescaped_html = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), combined_text)
        unescaped_html = unescaped_html.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
        
        payload_soup = BeautifulSoup(unescaped_html, 'html.parser')
        
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
                    
        characters_data = []
        script_data = None
        
        for s in soup.find_all('script'):
            if "cmoxpr78c0099oakoj7c16z0e" in s.text:
                script_data = s.text
                break
                
        if script_data:
            idx = script_data.find('\\"characters\\":')
            if idx == -1:
                idx = script_data.find('"characters":')
                
            if idx != -1:
                start_pos = idx
                while start_pos > 0 and script_data[start_pos] != '{':
                    start_pos -= 1
                    
                sub = script_data[start_pos:]
                sub_clean = sub.replace('\\"', '"').replace('\\\\', '\\')
                
                bracket_count = 0
                end_idx = 0
                for i, char in enumerate(sub_clean):
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i + 1
                            break
                            
                if end_idx > 0:
                    try:
                        parsed_data = json.loads(sub_clean[:end_idx])
                        characters_data = parsed_data.get("characters", [])
                    except Exception as je:
                        pass
                        
        return {
            "changelog": changelog,
            "characters": characters_data
        }
        
    def scrape_endgame_reports(self) -> dict:
        """
        Varre as URLs de cada modo de endgame (MoC, PF, AS, AA)
        e extrai as métricas de performance, visão geral e top equipes.
        """
        urls = {
            "moc": ("https://www.prydwen.gg/star-rail/memory-of-chaos", "moc", "Memory of Chaos (MoC)", "média de ciclos"),
            "pure": ("https://www.prydwen.gg/star-rail/pure-fiction", "pf", "Pure Fiction (PF)", "pontuação média"),
            "apo": ("https://www.prydwen.gg/star-rail/apocalyptic-shadow", "as", "Apocalyptic Shadow (AS)", "pontuação média"),
            "aa": ("https://www.prydwen.gg/star-rail/anomaly-arbitration", "aa", "Anomaly Arbitration (AA)", "média de rodadas")
        }
        
        results = {}
        
        for key, (url, mode_key, mode_title, metric_name) in urls.items():
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
            except Exception as e:
                print(f"Erro ao carregar dados de endgame para {mode_title}: {e}")
                continue
                
            html = r.text
            
            # Reconstroi o payload RSC do NextJS
            payloads = []
            for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html):
                payloads.append(match.group(1))
            for match in re.finditer(r"self\.__next_f\.push\(\[\d+,\s*'(.*?)'\]\)", html):
                payloads.append(match.group(1))
                
            combined = "".join(payloads)
            combined = combined.replace('\\\\', '\\')
            unescaped = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), combined)
            unescaped = unescaped.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
            
            # Localiza a chave de modo correspondente
            idx = unescaped.find(f'"mode":"{mode_key}"')
            if idx == -1:
                idx = unescaped.find(f'{{"mode":"{mode_key}"')
                
            if idx != -1:
                start_pos = idx
                while start_pos > 0 and unescaped[start_pos] != '{':
                    start_pos -= 1
                sub = unescaped[start_pos:]
                
                # Acha o fechamento do bloco correspondente
                bracket_count = 0
                end_idx = 0
                for i, char in enumerate(sub):
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i + 1
                            break
                            
                if end_idx > 0:
                    try:
                        parsed_data = json.loads(sub[:end_idx])
                        results[key] = {
                            "title": mode_title,
                            "metric_name": metric_name,
                            "data": parsed_data
                        }
                    except Exception as je:
                        print(f"Erro ao ler JSON de endgame para {mode_title}: {je}")
                        
        return results

    def save_meta_markdown(self, data: dict, filepath: str = "meta_e_tierlists_atual.md") -> str:
        """
        Formata o changelog e a tier list de cada modo de jogo em Markdown em linguagem natural.
        """
        lines = []
        lines.append("# Análise de Meta e Tier Lists - Honkai: Star Rail")
        lines.append("Relatório gerado automaticamente extraindo dados analíticos e changelogs do site Prydwen.gg.")
        lines.append("")
        
        # 1. Changelog & Meta Reviews
        lines.append("## 1. Notas de Atualização e Análise do Meta (Changelog)")
        lines.append("")
        if data["changelog"]:
            for entry in data["changelog"]:
                lines.append(f"### {entry['title']}")
                lines.append("")
                for para in entry["paragraphs"]:
                    lines.append(para)
                    lines.append("")
        else:
            lines.append("Nenhuma nota de atualização recente localizada.")
            lines.append("")
            
        # 2. Tier Lists por Modo de Jogo
        lines.append("## 2. Classificação de Tiers por Modo de Jogo")
        lines.append("")
        
        modes = {
            "moc_rating": "Memory of Chaos (MoC)",
            "pure_rating": "Pure Fiction (PF)",
            "apo_rating": "Apocalyptic Shadow (AS)"
        }
        
        for mode_key, mode_name in modes.items():
            lines.append(f"### {mode_name}")
            lines.append("")
            
            tier_groups = {}
            for t_val in sorted(self.rating_map.keys(), reverse=True):
                tier_label = self.rating_map[t_val]
                tier_groups[tier_label] = []
                
            for char in data["characters"]:
                name = char.get("name")
                rarity = char.get("rarity", "5")
                element = self.translate_to_portuguese(char.get("element", ""))
                path = self.translate_to_portuguese(char.get("path", ""))
                
                r_list = char.get("tierRatings", [])
                for r_info in r_list:
                    r_val = r_info.get(mode_key)
                    category = self.translate_to_portuguese(r_info.get("category", ""))
                    
                    if r_val in self.rating_map:
                        tier_label = self.rating_map[r_val]
                        char_str = f"{name} ({rarity}★ {element} - {path}) | Função: {category}"
                        if char_str not in tier_groups[tier_label]:
                            tier_groups[tier_label].append(char_str)
                            
            sorted_labels = sorted(tier_groups.keys(), key=lambda x: float(x[1:]) if x[1:].replace('.', '', 1).isdigit() else 99)
            for t_label in sorted_labels:
                lines.append(f"#### Tier {t_label}")
                if tier_groups[t_label]:
                    for char_line in sorted(tier_groups[t_label]):
                        lines.append(f"- {char_line}")
                else:
                    lines.append("- Nenhum personagem classificado neste tier.")
                lines.append("")
                
        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filepath

    def save_endgame_markdown(self, reports: dict, filepath: str = "meta_endgame_report.md") -> str:
        """
        Salva o relatório consolidado de dados de endgame para cada um dos 4 modos em Markdown
        estruturado em linguagem natural para consumo por LLM.
        """
        lines = []
        lines.append("# Relatório de Meta de Endgame - Honkai: Star Rail")
        lines.append("Análise detalhada extraída do Prydwen.gg contendo estatísticas de performance, taxas de uso e equipes populares.")
        lines.append("")
        
        for key in ["moc", "pure", "apo", "aa"]:
            if key not in reports:
                continue
                
            report = reports[key]
            mode_title = report["title"]
            metric_name = report["metric_name"]
            data = report["data"]
            
            analytics = data.get("analyticsData", {})
            phase = analytics.get("phase", {})
            
            # Cria mapa de slugs de personagens
            name_map = {}
            for char in data.get("characters", []):
                slug = char.get("slug")
                name_disp = char.get("name")
                if slug and name_disp:
                    name_map[slug] = name_disp
            # Fallbacks especiais
            name_map["dan-heng-imbibitor-lunae"] = "Dan Heng • Imbibitor Lunae"
            name_map["march-7th-swordmaster"] = "March 7th (Swordmaster)"
            name_map["trailblazer-elation"] = "Trailblazer (Elation)"
            name_map["trailblazer-remembrance"] = "Trailblazer (Remembrance)"
            name_map["trailblazer-harmony"] = "Trailblazer (Harmony)"
            name_map["tingyun-fugue"] = "Tingyun • Fugue"
            
            lines.append(f"# Report: {mode_title}")
            lines.append("")
            lines.append("## Visão Geral e Buff do Patch")
            lines.append("")
            lines.append(f"- **Fase Atual:** {self.translate_to_portuguese(phase.get('displayName', ''))} (versão {phase.get('displayVersion')})")
            lines.append(f"- **Total de Jogadores na Amostra:** {phase.get('totalUsers')} jogadores")
            if phase.get("bossNames"):
                bosses = [self.translate_to_portuguese(b) for b in phase.get("bossNames")]
                lines.append(f"- **Inimigos/Chefes Principais:** {', '.join(bosses)}")
            lines.append("")
            
            lines.append("### Análise de Diretrizes do Patch")
            lines.append(f"O ciclo atual de {self.translate_to_portuguese(mode_title)} favorece arquétipos específicos com base no posicionamento dos chefes e nos bônus mecânicos sazonais da versão {phase.get('displayVersion')}. Veja os detalhes de performance a seguir:")
            lines.append("")
            
            # Character Stats
            lines.append("## Métricas Globais de Personagens")
            lines.append("")
            lines.append(f"A tabela abaixo mostra a taxa de uso (Usage/Appearance Rate) e a {metric_name} na conclusão do estágio mais desafiador deste modo:")
            lines.append("")
            
            char_stats = analytics.get("charStats", [])
            active_stats = [c for c in char_stats if c.get("sample", 0) > 0]
            active_stats = sorted(active_stats, key=lambda x: x.get("app_rate", 0), reverse=True)
            
            for c in active_stats[:25]:
                name_c = c.get("name")
                app = c.get("app_rate")
                avg = c.get("avg_round")
                
                if avg == 99.99 or avg == 0:
                    avg_str = "N/A"
                else:
                    avg_str = f"{avg} ciclos" if "ciclo" in metric_name else (f"{avg} rodadas" if "rodada" in metric_name else f"{avg} pontos")
                    
                lines.append(f"- **{name_c}:** Taxa de Uso: {app}% | Média de Performance: {avg_str}")
            lines.append("")
            
            # Teams
            lines.append("## Top Composições (Teams)")
            lines.append("")
            lines.append("Equipes mais populares e eficientes utilizadas pelos jogadores para vencer os desafios deste patch:")
            lines.append("")
            
            teams = analytics.get("teams", {})
            if isinstance(teams, dict):
                for side in sorted(teams.keys()):
                    if side == "all":
                        lines.append("### Composições Combinadas (Geral)")
                    else:
                        lines.append(f"### Stage / Side {side}")
                    lines.append("")
                    
                    for t in teams[side][:8]:
                        char_slugs = [t.get("char_one"), t.get("char_two"), t.get("char_three"), t.get("char_four")]
                        char_list = [name_map.get(slug, slug.replace('-', ' ').title()) for slug in char_slugs if slug]
                        team_str = " + ".join(char_list)
                        
                        t_avg = t.get("avg_round")
                        t_avg_str = f"{t_avg} ciclos" if "ciclo" in metric_name else (f"{t_avg} rodadas" if "rodada" in metric_name else f"{t_avg} pontos")
                        lines.append(f"- **Rank {t.get('rank')}:** {team_str} (Uso: {t.get('app_rate')}% | Média: {t_avg_str})")
                    lines.append("")
            lines.append("---")
            lines.append("")
            
        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filepath

if __name__ == "__main__":
    scraper = PrydwenMetaScraper()
    print("Iniciando a extração do meta e das tier lists da Prydwen...")
    try:
        data = scraper.scrape_tier_list()
        path1 = scraper.save_meta_markdown(data)
        print(f"Sucesso! Relatório de tier list salvo em: {os.path.abspath(path1)}")
        
        print("\nIniciando a extração dos dados de endgame...")
        reports = scraper.scrape_endgame_reports()
        path2 = scraper.save_endgame_markdown(reports)
        print(f"Sucesso! Relatório de endgame salvo em: {os.path.abspath(path2)}")
    except Exception as e:
        print(f"Erro durante a execução: {e}")
