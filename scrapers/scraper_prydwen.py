import os
import re
import json
from datetime import datetime
from typing import Optional
from curl_cffi import requests
from bs4 import BeautifulSoup

_HSR_REPLACEMENTS = {
    "Acheron’s signature Light Cone": "o Cone de Luz assinatura de Acheron",
    "Acheron's signature Light Cone": "o Cone de Luz assinatura de Acheron",
    "signature Light Cone": "Cone de Luz assinatura",
    "Light Cone": "Cone de Luz",
    "Light Cones": "Cones de Luz",
    "Relic Sets": "Conjuntos de Relíquias",
    "Relic Set": "Conjunto de Relíquias",
    "Planar Ornaments": "Ornamentos Planares",
    "Planar Ornament": "Ornamento Planar",
    "main source of DMG": "principal fonte de dano",
    "Ultimate DMG": "dano da Suprema",
    "Ultimate": "Suprema (Ultimate)",
    "Skill": "Perícia (Skill)",
    "Basic ATK": "Ataque Básico",
    "Basic": "Ataque Básico",
    "Technique": "Técnica",
    "Talent": "Talento",
    "debuffs": "debuffs",
    "debuff": "debuff",
    "Nihility characters": "personagens de Inexistência (Nihility)",
    "Nihility character": "personagem de Inexistência (Nihility)",
    "Nihility teammate": "companheiro de Inexistência (Nihility)",
    "Nihility teammates": "companheiros de Inexistência (Nihility)",
    "Nihility": "Inexistência (Nihility)",
    "Harmony characters": "personagens de Harmonia (Harmony)",
    "Harmony character": "personagem de Harmonia (Harmony)",
    "Harmony": "Harmonia (Harmony)",
    "Preservation unit": "personagem de Preservação (Preservation)",
    "Preservation Trailblazer": "Desbravador da Preservação",
    "Preservation": "Preservação (Preservation)",
    "Abundance": "Abundância (Abundance)",
    "Sustains": "Sustains",
    "Sustain": "Sustain",
    "Vulnerability": "Vulnerabilidade",
    "DMG Boost": "Aumento de Dano",
    "DMG bonus": "Bônus de Dano",
    "DMG": "Dano",
    "CRIT Rate": "Taxa Crítica",
    "CRIT DMG": "Dano Crítico",
    "CRIT": "Crítico",
    "Speed": "Velocidade",
    "SPD": "Velocidade",
    "Energy": "Energia",
    "Toughness": "Tenacidade",
    "Weakness Types": "Tipos de Fraqueza",
    "Weakness": "Fraqueza",
    "debuffing": "aplicadores de debuff",
    "He is Acheron’s premier amplifier": "Ele é o amplificador principal da Acheron",
    "premier amplifier": "amplificador principal",
    "amplifier": "amplificador",
    "points generator": "gerador de pontos",
    "Trend of the Universal Market": "Trend of the Universal Market (Tendência do Mercado Universal)",
    "Taunt": "Provocação (Taunt)",
    "E2": "E2 (Eidolon 2)",
    "E1": "E1 (Eidolon 1)",
    "E6": "E6 (Eidolon 6)",
    "Eidolon": "Eidolon",
    "Eidolons": "Eidolons",
    "Major trace": "Rastro Principal",
    "Trace": "Rastro",
    "Traces": "Rastros",
}
_HSR_LOWER_MAP = {k.lower(): v for k, v in _HSR_REPLACEMENTS.items()}
_HSR_TRANSLATE_RE = re.compile(
    "|".join(re.escape(k) for k in sorted(_HSR_REPLACEMENTS.keys(), key=len, reverse=True)),
    re.IGNORECASE,
)


def _hsr_replacer(match):
    matched_str = match.group(0)
    return _HSR_LOWER_MAP.get(matched_str.lower(), matched_str)


def extract_prydwen_card_name(link, slug: str = "") -> str:
    """
    Extrai o nome limpo do personagem/agente a partir do card do Prydwen,
    ignorando badges e tags visuais (<span class="tag new">New</span>, HSR, ZZZ, 7.3, etc.).
    """
    if link is not None:
        name_el = link.find(class_=lambda c: c and any(k in c for k in ("emp-name", "card-name")))
        if name_el:
            clean = " ".join(name_el.get_text(" ", strip=True).split())
            if clean:
                return clean

        # Extrai apenas textos fora de elementos marcados como tag/badge
        text_parts = []
        for s in link.find_all(string=True):
            parent = s.parent
            is_badge = False
            while parent and parent is not link:
                cls_str = " ".join(parent.get("class") or []).lower()
                if any(b in cls_str.split() for b in ("tag", "badge")):
                    is_badge = True
                    break
                parent = parent.parent
            if not is_badge:
                txt = s.strip()
                if txt:
                    text_parts.append(txt)

        combined = " ".join(text_parts).strip()
        if combined:
            return combined

    if slug:
        return slug.replace("-", " ").title()
    return ""


class PrydwenScraper:
    def __init__(self):
        """
        Inicializa o raspador com headers realistas para evitar bloqueios.
        """
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        self.base_url = "https://www.prydwen.gg"

    def get_character_list(self) -> list:
        """
        Acessa a página de personagens de HSR no Prydwen e extrai seus nomes e URLs.

        Retorna:
            list: Lista de dicionários contendo {'name': Nome, 'url': URL_Completo}.
        """
        url = f"{self.base_url}/star-rail/characters"
        try:
            r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=30)
            r.raise_for_status()
        except requests.HTTPError as he:
            raise Exception(f"Erro HTTP ao buscar lista de personagens: Código {he.response.status_code}")
        except Exception as e:
            raise Exception(f"Falha de conexão ao carregar lista de personagens: {e}")

        soup = BeautifulSoup(r.text, "html.parser")
        characters = []
        seen_urls = set()

        # Encontra todos os links de personagens
        for link in soup.find_all("a"):
            href = link.get("href", "")
            if "/star-rail/characters/" in href:
                clean_href = href.strip()
                if clean_href not in seen_urls:
                    seen_urls.add(clean_href)

                    # Nome do personagem (sem badges/tags como 'New', 'ZZZ', 'HSR', etc.)
                    slug = clean_href.rstrip("/").split("/")[-1]
                    if clean_href == "/star-rail/characters" or clean_href.endswith("/characters/"):
                        continue

                    name = extract_prydwen_card_name(link, slug)

                    full_url = self.base_url + clean_href if clean_href.startswith("/") else clean_href
                    characters.append({"name": name, "url": full_url})

        return sorted(characters, key=lambda x: x["name"])

    def translate_to_portuguese(self, text: str) -> str:
        """
        Traduz termos comuns do jogo de inglês para português de forma segura
        em uma única passagem (evitando substituições duplas).
        """
        if not text:
            return text
        return _HSR_TRANSLATE_RE.sub(_hsr_replacer, text)

    def extract_synergies(self, character_name: str, review_paragraphs: list) -> list:
        """
        Extrai de forma dinâmica as justificativas mecânicas de aliados
        baseando-se nos parágrafos do review e traduzindo termos comuns.
        """
        # Se for Acheron, retorna o texto estático refinado solicitado pelo usuário
        if character_name.lower() == "acheron":
            return [
                '- **Aliados de Inexistência (Nihility) Gerais:** São obrigatórios para ativar o multiplicador separado de dano da passiva A4 (115% com 1 aliado, 160% com 2 aliados). Além disso, a Acheron depende puramente de aliados que aplicam debuffs para gerar seus pontos de "Slashed Dream" e stacks de "Crimson Knot" rapidamente para carregar sua Habilidade Suprema.',
                "- **Jiaoqiu:** É o amplificador e gerador de pontos principal para ela. Consegue aplicar debuffs de Vulnerabilidade de forma contínua durante as ações dos próprios inimigos (fazendo-os receber até 50% a mais de dano de Supremas), acelerando drasticamente a rotação da Acheron.",
                "- **Cipher:** Aumenta permanentemente o Dano Recebido pelos inimigos em 40% em campo. Seus ataques extras aplicam debuffs extras (se equipada com cones como Resolution ou Holiday Thermae), e ela grava parte do dano da Acheron para descarregar como Dano Verdadeiro massivo.",
                "- **Suportes de Harmonia (Sparkle, Sunday, Tribbie):** Em builds normais (E0), causam perda de dano por não ativarem totalmente a passiva A4, exigindo suportes extremamente bem buildados para compensar. Porém, caso a Acheron seja **E2**, a restrição cai para apenas 1 Nihility, tornando Sparkle, Sunday ou Tribbie (focada em AoE) as melhores opções de suportes para avançar turnos e dar buffs massivos de Crítico.",
                "- **Sustains de Preservação (com Trend of the Universal Market):** Personagens de Preservação usando este Cone de Luz conseguem aplicar debuffs de Queimadura sempre que são atacados, gerando pontos grátis para a Suprema da Acheron. É otimizado ao extremo em personagens como o Desbravador da Preservação devido à sua mecânica de Provocação (Taunt).",
            ]

        # Caso contrário, faz a busca dinâmica nos parágrafos de review
        synergies = []
        matched_paras = set()

        # Mapeamento de termos para encontrar sinergias de outros personagens comuns
        support_names = [
            "Robin",
            "Ruan Mei",
            "Bronya",
            "Tingyun",
            "Pela",
            "Guinaifen",
            "Silver Wolf",
            "Jiaoqiu",
            "Cipher",
            "Sparkle",
            "Sunday",
            "Tribbie",
            "Gallagher",
            "Lingsha",
            "Aventurine",
            "Gepard",
            "Fu Xuan",
            "Huohuo",
        ]

        # 1. Busca por personagens citados especificamente
        for name in support_names:
            for para in review_paragraphs:
                if para in matched_paras:
                    continue
                if name.lower() in para.lower() and any(
                    x in para.lower()
                    for x in ["team", "ally", "support", "sustain", "synergy", "partner", "healer", "buffer"]
                ):
                    translated = self.translate_to_portuguese(para)
                    translated = re.sub(r"\s+", " ", translated)
                    synergies.append(f"- **{name}:** {translated}")
                    matched_paras.add(para)

        # 2. Busca por classes/caminhos gerais de suporte
        general_keys = {
            "Nihility": "Aliados de Inexistência (Nihility)",
            "Harmony": "Suportes de Harmonia (Harmony)",
            "Preservation": "Sustains de Preservação (Preservation)",
            "Abundance": "Suportes de Abundância (Abundance)",
        }
        for path_eng, path_pt in general_keys.items():
            for para in review_paragraphs:
                if para in matched_paras:
                    continue
                if path_eng.lower() in para.lower() and any(
                    x in para.lower() for x in ["team", "ally", "support", "sustain", "synergy"]
                ):
                    translated = self.translate_to_portuguese(para)
                    translated = re.sub(r"\s+", " ", translated)
                    synergies.append(f"- **{path_pt}:** {translated}")
                    matched_paras.add(para)

        if not synergies:
            # Fallback genérico se nada for detectado
            synergies.append(
                "Detalhes de sinergia de aliados e suportes recomendados estão descritos na análise detalhada da seção Review."
            )

        return synergies

    def scrape_character_guide(self, character_name: str, url: str) -> dict:
        """
        Raspa a página de guia de um personagem específico e extrai dados analíticos estruturados
        em linguagem natural (Kit de Habilidades, Justificativa de Builds, Review e Times).
        """
        try:
            r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=30)
            r.raise_for_status()
        except requests.HTTPError as he:
            raise Exception(f"Erro HTTP {he.response.status_code} ao acessar o guia de {character_name}")
        except Exception as e:
            raise Exception(f"Falha ao acessar o guia de {character_name}: {e}")

        soup = BeautifulSoup(r.text, "html.parser")
        tabs = soup.find_all("div", class_="tab-inside")

        data = {
            "pros": [],
            "cons": [],
            "review": [],
            "skills_active": [],
            "skills_traces": [],
            "skills_eidolons": [],
            "light_cones": [],
            "relics": [],
            "planar_ornaments": [],
            "stats_main": [],
            "stats_sub": "",
            "endgame_stats": [],
            "stats_info": "",
            "talent_priority": "",
            "teams": [],
        }

        if not tabs:
            return data

        tab_kit = None
        tab_review = None
        tab_build = None

        for tab in tabs:
            if tab.find("div", class_="build-stats") or tab.find("div", class_="detailed-cones"):
                tab_build = tab
            h5_texts = [h.text.strip().lower() for h in tab.find_all("h5")]
            if "pros" in h5_texts or "cons" in h5_texts or tab.find("div", class_="section-analysis"):
                tab_review = tab

        for tab in tabs:
            if tab == tab_review or tab == tab_build:
                continue
            if tab.find("div", class_="skill-header"):
                text_lower = tab.get_text().lower()
                if any(x in text_lower for x in ["basic atk", "skill", "ultimate", "talent", "technique"]):
                    tab_kit = tab
                    break

        if not tab_kit and len(tabs) >= 1:
            tab_kit = tabs[0]
        if not tab_review and len(tabs) >= 2:
            tab_review = tabs[1]
        if not tab_build and len(tabs) >= 3:
            tab_build = tabs[2]

        # --- 1. ABA 1: KIT DE HABILIDADES ---
        for header in tab_kit.find_all("div", class_="skill-header"):
            header_text = header.get_text(separator=" ").strip()
            desc_div = header.find_next_sibling("div", class_=re.compile("skill-with-coloring|eidolon"))
            if desc_div:
                desc_text = desc_div.get_text().strip()
                desc_text = re.sub(r"\s+", " ", desc_text)

                header_lower = header_text.lower()
                if any(x in header_lower for x in ["basic atk", "skill", "ultimate", "talent", "technique"]):
                    data["skills_active"].append({"name": header_text, "description": desc_text})
                elif "trace" in header_lower:
                    data["skills_traces"].append({"name": header_text, "description": desc_text})
                elif "eidolon" in header_lower or re.match(r"^[Ee]\d", header_text):
                    data["skills_eidolons"].append({"name": header_text, "description": desc_text})

        # --- 2. ABA 2: REVIEW DETALHADO ---
        if tab_review:
            # Prós
            pros_h5 = [h for h in tab_review.find_all("h5") if h.text.strip().lower() == "pros"]
            if pros_h5:
                div = pros_h5[0].find_next_sibling("div")
                if div:
                    data["pros"] = [p.text.strip() for p in div.find_all("p") if p.text.strip()]

            # Contras
            cons_h5 = [h for h in tab_review.find_all("h5") if h.text.strip().lower() == "cons"]
            if cons_h5:
                div = cons_h5[0].find_next_sibling("div")
                if div:
                    data["cons"] = [p.text.strip() for p in div.find_all("p") if p.text.strip()]

            # Análise de Review
            analysis_divs = tab_review.find_all("div", class_="section-analysis")
            if len(analysis_divs) > 1:
                data["review"] = [p.text.strip() for p in analysis_divs[1].find_all("p") if p.text.strip()]
            elif len(analysis_divs) == 1:
                data["review"] = [p.text.strip() for p in analysis_divs[0].find_all("p") if p.text.strip()]

        # --- 3. ABA 3: BUILDS E TIMES ---
        if tab_build:
            for dc in tab_build.find_all("div", class_="detailed-cones"):
                heading = dc.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
                section_name = heading.text.strip().lower() if heading else ""

                children = dc.find_all(recursive=False)
                idx = 0
                while idx < len(children):
                    child = children[idx]
                    child_classes = child.get("class", [])

                    if any("single-cone" in c for c in child_classes):
                        name_el = child.find("span", class_="hsr-set-name")
                        name = name_el.text.strip() if name_el else ""

                        percent_el = child.find("div", class_="percentage")
                        pct = percent_el.text.strip() if percent_el else ""

                        super_el = child.find("span", class_="cone-super")
                        sup = super_el.text.strip() if super_el else ""
                        if sup and not sup.startswith("("):
                            sup = f"({sup})"

                        justification = ""
                        if idx + 1 < len(children):
                            next_child = children[idx + 1]
                            next_classes = next_child.get("class", [])
                            if "information" in next_classes and "with-padding" not in next_classes:
                                justification = next_child.get_text().strip()
                                idx += 1

                        item_data = {"name": name, "percentage": pct, "justification": justification}

                        if "light cone" in section_name:
                            item_data["super"] = sup
                            data["light_cones"].append(item_data)
                        elif "relic" in section_name:
                            data["relics"].append(item_data)
                        elif re.search(r"planar|planetary", section_name):
                            data["planar_ornaments"].append(item_data)
                    idx += 1

            # Stats
            stats_sec = tab_build.find("div", class_="build-stats")
            if stats_sec:
                main_stats_div = stats_sec.find("div", class_="main-stats")
                if main_stats_div:
                    for div in main_stats_div.find_all("div", class_="flex-1"):
                        text = div.get_text().strip()

                        matched_slot = None
                        text_clean = text.strip()
                        for slot_key, slot_name in [
                            ("body", "Body"),
                            ("feet", "Feet"),
                            ("planar sphere", "Planar Sphere"),
                            ("sphere", "Planar Sphere"),
                            ("link rope", "Link Rope"),
                            ("rope", "Link Rope"),
                        ]:
                            if text_clean.lower().startswith(slot_key):
                                matched_slot = slot_name
                                val = text_clean[len(slot_key) :].strip()
                                break

                        if matched_slot:
                            # Remove dois pontos iniciais e espaços em branco/quebras de linha
                            val = val.lstrip(":").strip()
                            # Divide por barra '/' e limpa cada opção
                            options = [opt.strip() for opt in val.split("/") if opt.strip()]
                            val = " / ".join(options)

                            for op in [">=", "<=", ">", "<", "="]:
                                if op in val:
                                    val = f" {op} ".join([p.strip() for p in val.split(op)])
                                    break
                            data["stats_main"].append(f"{matched_slot}: {val}")

                for div in stats_sec.find_all("div", class_="flex-wrap"):
                    sub_div = div.find("div", class_="flex-1")
                    if sub_div:
                        sub_text = sub_div.get_text().strip()
                        if sub_text.lower().startswith("substats:"):
                            raw_sub = sub_text[len("substats:") :].strip()
                            # Remove completamente parênteses e colchetes de agrupamento
                            cleaned_sub = re.sub(r"\(.*?\)", "", raw_sub)
                            cleaned_sub = re.sub(r"[\[\]]", "", cleaned_sub)

                            # Divide por '>', limpa cada item e mapeia os atributos
                            parts = [p.strip() for p in cleaned_sub.split(">") if p.strip()]

                            substat_map = {
                                "spd": "vel",
                                "speed": "vel",
                                "vel": "vel",
                                "velocidade": "vel",
                                "crit rate": "crit_rate",
                                "crit_rate": "crit_rate",
                                "chance de crit": "crit_rate",
                                "taxa crítica": "crit_rate",
                                "taxa de crit": "crit_rate",
                                "crit dmg": "crit_dmg",
                                "crit_dmg": "crit_dmg",
                                "dano crítico": "crit_dmg",
                                "dano de crit": "crit_dmg",
                                "break effect": "break_effect",
                                "break_effect": "break_effect",
                                "efeito de quebra": "break_effect",
                                "quebra": "break_effect",
                                "ehr": "ehr",
                                "effect hit rate": "ehr",
                                "taxa de acerto de efeito": "ehr",
                                "res": "res",
                                "effect res": "res",
                                "resistência a efeito": "res",
                                "atk%": "atk_pct",
                                "atk percent": "atk_pct",
                                "atk_pct": "atk_pct",
                                "atk": "atk_flat",
                                "hp%": "hp_pct",
                                "hp percent": "hp_pct",
                                "hp_pct": "hp_pct",
                                "hp": "hp_flat",
                                "def%": "def_pct",
                                "def percent": "def_pct",
                                "def_pct": "def_pct",
                                "def": "def_flat",
                            }

                            def _map_sub_tok(raw_tok: str) -> str:
                                tok = raw_tok.lstrip("= ").strip()
                                tok = re.sub(
                                    r"\s*\b(?:until|untill|to|up to|or more|or higher|in combat|pre[- ]combat|desired goal)\b.*$",
                                    "",
                                    tok,
                                    flags=re.IGNORECASE,
                                ).strip()
                                tok_l = tok.lower()
                                return substat_map.get(tok_l, tok)

                            mapped_parts = []
                            for part in parts:
                                if "=" in part or "/" in part:
                                    sub_segs = re.split(r"\s*([=/])\s*", part)
                                    rebuilt = "".join(
                                        f" {seg} " if seg in ("=", "/") else _map_sub_tok(seg)
                                        for seg in sub_segs
                                        if seg != ""
                                    ).strip()
                                    if rebuilt:
                                        mapped_parts.append(rebuilt)
                                else:
                                    mapped_val = _map_sub_tok(part)
                                    if mapped_val:
                                        mapped_parts.append(mapped_val)

                            data["stats_sub"] = " > ".join(mapped_parts)

                # Extrai HSR Skills priority
                for el in soup.find_all(["div", "span", "p"]):
                    txt = el.get_text(separator=" ").strip()
                    match = re.search(r"Skills?\s*priority\s*[:\=]?\s*([A-Za-z0-9\s\>\=\+\-]+)", txt, re.IGNORECASE)
                    if match:
                        tp = match.group(1).strip()
                        tp = re.sub(r"\s*(Major|Traces|Stat|Note|Build).*", "", tp, flags=re.IGNORECASE).strip()
                        if tp and len(tp) > 2:
                            data["talent_priority"] = tp
                            break

                info_div = stats_sec.find("div", class_="information")
                if info_div:
                    data["stats_info"] = info_div.get_text().strip()

            # Recommended Endgame Stats (padrão HSR no Prydwen fora/abaixo de build-stats)
            for header in tab_build.find_all("div", class_="content-header"):
                if "endgame stats" in header.get_text(" ", strip=True).lower():
                    sib = header.find_next_sibling()
                    if sib:
                        seen_eg = set()
                        items = sib.find_all("li") or sib.find_all("p")
                        for item in items:
                            first_p = item.find("p") if item.name == "li" else None
                            node = first_p if first_p else item
                            line_txt = " ".join(node.get_text(" ", strip=True).split())
                            if not line_txt or ":" not in line_txt:
                                continue
                            s_label, s_val = [p.strip() for p in line_txt.split(":", 1)]
                            s_label_l = s_label.lower()
                            if not s_label or not s_val:
                                continue
                            if s_label_l.startswith(("note", "nota", "justificativa", "other ")):
                                continue
                            # Remove eventuais parágrafos/comentários longos colados no mesmo <p> após o valor
                            if len(s_val) > 65:
                                m_short = re.match(
                                    r"^([0-9][0-9\.\,\-\+\s%or\/]*(?:\([^)]{1,35}\))?)",
                                    s_val,
                                    re.IGNORECASE,
                                )
                                if m_short and m_short.group(1).strip():
                                    s_val = m_short.group(1).strip()
                            formatted = f"{s_label}: {s_val}"
                            if formatted not in seen_eg:
                                seen_eg.add(formatted)
                                data["endgame_stats"].append(formatted)
                    break

            # Times
            teams_div = tab_build.find("div", class_="team-container-moc")
            if teams_div:
                rows = teams_div.find_all("div", class_="team-row")
                for row in rows[:5]:
                    char_names = []
                    for img in row.find_all("img"):
                        alt = img.get("alt")
                        if alt and alt not in [
                            "Physical",
                            "Fire",
                            "Ice",
                            "Lightning",
                            "Wind",
                            "Quantum",
                            "Imaginary",
                            "Void",
                        ]:
                            if alt not in char_names:
                                char_names.append(alt)

                    stats_text = row.get_text(separator=" ").strip()
                    stats_text = " ".join(stats_text.split())

                    if char_names:
                        data["teams"].append({"members": " + ".join(char_names), "stats": stats_text})

        return data

    def save_to_markdown(self, character_name: str, data: dict, output_dir: str = "hsr/guias") -> str:
        """
        Salva o guia do personagem com as análises descritivas formatadas em Markdown.
        """
        os.makedirs(output_dir, exist_ok=True)

        lines = []
        lines.append(f"# Guia de Build - {character_name}")
        lines.append("Dados extraídos do site Prydwen.gg.")
        lines.append("")

        # 1. REVIEW
        lines.append("## Review")
        lines.append("")

        if data["pros"]:
            lines.append("### Prós (Pontos Fortes)")
            for pro in data["pros"]:
                lines.append(f"- {pro}")
            lines.append("")

        if data["cons"]:
            lines.append("### Contras (Pontos Fracos)")
            for con in data["cons"]:
                lines.append(f"- {con}")
            lines.append("")

        if data["review"]:
            lines.append("### Análise Detalhada")
            for para in data["review"]:
                lines.append(para)
                lines.append("")
        else:
            lines.append("Nenhuma análise de review disponível.")
            lines.append("")

        # 2. MECÂNICAS DO KIT
        lines.append("## Mecânicas do Kit")
        lines.append("")

        if data["skills_active"]:
            lines.append("### Habilidades Ativas")
            for skill in data["skills_active"]:
                lines.append(f"- **{skill['name']}**")
                lines.append(f"  {skill['description']}")
                lines.append("")

        if data["skills_traces"]:
            lines.append("### Rastros Principais (Traces)")
            for trace in data["skills_traces"]:
                lines.append(f"- **{trace['name']}**")
                lines.append(f"  {trace['description']}")
                lines.append("")

        if data["skills_eidolons"]:
            lines.append("### Eidolons")
            for eidolon in data["skills_eidolons"]:
                lines.append(f"- **{eidolon['name']}**")
                lines.append(f"  {eidolon['description']}")
                lines.append("")

        # 3. POR QUE USAR ESTES CONES/RELÍQUIAS
        lines.append("## Por que usar estes Cones/Relíquias")
        lines.append("")

        lines.append("### Melhores Cones de Luz")
        if data["light_cones"]:
            for lc in data["light_cones"]:
                sup_text = f" {lc['super']}" if lc.get("super") else ""
                lines.append(f"- **{lc['name']}{sup_text}** ({lc['percentage']} de eficácia)")
                if lc["justification"]:
                    translated_just = self.translate_to_portuguese(lc["justification"])
                    lines.append(f"  *Justificativa:* {translated_just}")
                lines.append("")
        else:
            lines.append("Nenhum cone de luz listado.")
            lines.append("")

        lines.append("### Melhores Conjuntos de Relíquias (4 Peças)")
        if data["relics"]:
            for r in data["relics"]:
                lines.append(f"- **{r['name']}** ({r['percentage']} de eficácia)")
                if r["justification"]:
                    translated_just = self.translate_to_portuguese(r["justification"])
                    lines.append(f"  *Justificativa:* {translated_just}")
                lines.append("")
        else:
            lines.append("Nenhum conjunto de relíquias listado.")
            lines.append("")

        lines.append("### Melhores Ornamentos Planares (2 Peças)")
        if data["planar_ornaments"]:
            for po in data["planar_ornaments"]:
                lines.append(f"- **{po['name']}** ({po['percentage']} de eficácia)")
                if po["justification"]:
                    translated_just = self.translate_to_portuguese(po["justification"])
                    lines.append(f"  *Justificativa:* {translated_just}")
                lines.append("")
        else:
            lines.append("Nenhum ornamento planar listado.")
            lines.append("")

        # Stats
        lines.append("### Atributos Recomendados (Stats)")
        if data["stats_main"]:
            lines.append("#### Atributos Principais (Main Stats)")
            for sm in data["stats_main"]:
                lines.append(f"- {sm}")
            lines.append("")

        if data["stats_sub"]:
            lines.append("#### Subatributos Prioritários (Sub-stats)")
            lines.append(data["stats_sub"])
            lines.append("")

        if data.get("endgame_stats"):
            lines.append("#### Atributos Finais Recomendados (Endgame Stats)")
            for eg in data["endgame_stats"]:
                lines.append(f"- {eg}")
            lines.append("")

        if data["stats_info"]:
            lines.append("#### Análise de Atributos e Otimização")
            lines.append(data["stats_info"])
            lines.append("")

        # 4. ANÁLISE DE SINERGIAS
        lines.append("## Análise de Sinergias")
        lines.append("")

        # 4.1. Justificativas mecânicas
        lines.append("### Justificativa Mecânica de Aliados e Suportes:")
        lines.append("")
        synergy_list = self.extract_synergies(character_name, data["review"])
        for syn in synergy_list:
            lines.append(syn)
        lines.append("")

        # 4.2. Composições do MoC
        lines.append("### Times Populares e Recomendados (Memory of Chaos)")
        lines.append("")
        if data["teams"]:
            for team in data["teams"]:
                lines.append(f"- **Composição:** {team['members']}")
                lines.append(f"  *Desempenho no MoC:* {team['stats']}")
                lines.append("")
        else:
            lines.append("Nenhuma composição de times listada.")
            lines.append("")

        markdown_content = "\n".join(lines)

        filename_clean = (
            character_name.lower().replace(" ", "_").replace(":", "").replace("(", "").replace(")", "").replace("'", "")
            + ".md"
        )
        filepath = os.path.join(output_dir, filename_clean)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return filepath

    @staticmethod
    def _parse_prydwen_date(date_str: str) -> Optional[str]:
        """Converte datas no formato 'Nov 4, 2026' ou 'Nov 4 2026' para ISO 'YYYY-MM-DD'."""
        if not date_str:
            return None
        clean = re.sub(r"\s+", " ", str(date_str).strip()).replace(",", "")
        for fmt in ("%b %d %Y", "%B %d %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _extract_banner_schedule_meta(self, card_soup, fallback_patch_info: str = "") -> dict:
        """
        Extrai individualmente de cada card de banner da Prydwen:
        - patch_label (ex: 'Patch 4.7 Phase 1', 'Patch 4.7', 'Patch 3.3 Phase 2', 'Fate Collab')
        - phase (1, 2 ou None quando dura a atualização inteira / collab)
        - duration_type ('phase_1', 'phase_2', 'full_patch', 'collab')
        - date_range, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD ou None)
        """
        card_text = re.sub(r"\s+", " ", card_soup.get_text(" | ").strip()) if card_soup else ""
        low_text = card_text.lower()

        # 1. Extrai Patch/Fase diretamente do card (prioriza texto do card sobre fallback global)
        patch_label = ""
        m_patch = re.search(r"(Patch\s+\d+(?:\.\d+)?(?:\s+Phase\s+[12])?)", card_text, re.IGNORECASE)
        if m_patch:
            patch_label = re.sub(r"\s+", " ", m_patch.group(1)).strip()
        elif "collab" in low_text:
            m_collab = re.search(r"([A-Za-z0-9 ]*Collab)", card_text, re.IGNORECASE)
            patch_label = m_collab.group(1).strip() if m_collab else "Collab"
        elif fallback_patch_info:
            m_fb = re.search(r"(Patch\s+\d+(?:\.\d+)?(?:\s+Phase\s+[12])?)", fallback_patch_info, re.IGNORECASE)
            patch_label = m_fb.group(1).strip() if m_fb else fallback_patch_info.strip()

        # 2. Extrai intervalo de datas do card ('Nov 11, 2026 – Dec 2, 2026' ou 'From Jul 24, 2026')
        date_range = ""
        start_date = None
        end_date = None
        m_range = re.search(
            r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\s*[–—\-]\s*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
            card_text,
        )
        if m_range:
            date_range = f"{m_range.group(1).strip()} – {m_range.group(2).strip()}"
            start_date = self._parse_prydwen_date(m_range.group(1))
            end_date = self._parse_prydwen_date(m_range.group(2))
        else:
            m_from = re.search(r"(From\s+[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", card_text, re.IGNORECASE)
            if m_from:
                date_range = m_from.group(1).strip()
                start_date = self._parse_prydwen_date(re.sub(r"^From\s+", "", date_range, flags=re.IGNORECASE))
                end_date = None
            elif fallback_patch_info:
                m_fb_range = re.search(
                    r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\s*[–—\-]\s*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
                    fallback_patch_info,
                )
                if m_fb_range:
                    date_range = f"{m_fb_range.group(1).strip()} – {m_fb_range.group(2).strip()}"
                    start_date = self._parse_prydwen_date(m_fb_range.group(1))
                    end_date = self._parse_prydwen_date(m_fb_range.group(2))

        # 3. Classifica fase e tipo de duração (1ª Fase, 2ª Fase, Atualização Inteira ou Collab)
        phase: Optional[int] = None
        duration_type = "phase_1"
        is_collab = ("| collab |" in f" {low_text} ") or ("collaboration" in low_text) or (
            start_date is not None and end_date is None and date_range.lower().startswith("from ")
        )

        m_phase_num = re.search(r"(?:phase|fase)\s*([12])", patch_label, re.IGNORECASE)
        if not m_phase_num and not is_collab:
            m_phase_num = re.search(r"in\s+phase\s*([12])\s+of\s+patch", low_text, re.IGNORECASE)

        span_days = None
        if start_date and end_date:
            try:
                d_start = datetime.strptime(start_date, "%Y-%m-%d")
                d_end = datetime.strptime(end_date, "%Y-%m-%d")
                span_days = (d_end - d_start).days
            except ValueError:
                span_days = None

        if is_collab:
            phase = None
            duration_type = "collab"
        elif m_phase_num:
            phase = int(m_phase_num.group(1))
            duration_type = f"phase_{phase}"
        elif (
            "entirety of patch" in low_text
            or "full patch" in low_text
            or (span_days is not None and span_days >= 30)
        ):
            phase = None
            duration_type = "full_patch"
        else:
            m_fb_phase = re.search(r"(?:phase|fase)\s*([12])", fallback_patch_info or "", re.IGNORECASE)
            if m_fb_phase:
                phase = int(m_fb_phase.group(1))
                duration_type = f"phase_{phase}"
            else:
                phase = 1
                duration_type = "phase_1"

        return {
            "patch_label": patch_label,
            "date_range": date_range,
            "start_date": start_date,
            "end_date": end_date,
            "phase": phase,
            "duration_type": duration_type,
            "is_full_patch": (duration_type == "full_patch"),
        }

    def get_current_banners(self, game_id: str = None) -> dict:
        """
        Extrai dinamicamente os banners atuais de personagens e armas/cones/motores do Prydwen.
        Salva e consolida o resultado no cache offline static_data/current_banners.json.
        """
        banner_urls = {
            "genshin": f"{self.base_url}/genshin-impact/banners",
            "hsr": f"{self.base_url}/star-rail/banners",
            "zzz": f"{self.base_url}/zenless/banners",
        }

        # Carrega dados existentes do cache para não sobrescrever outros jogos
        from core.paths import get_data_path, get_resource_path

        static_dir = get_data_path("static_data")
        cache_file = os.path.join(static_dir, "current_banners.json")
        read_file = cache_file if os.path.exists(cache_file) else get_resource_path(os.path.join("static_data", "current_banners.json"))
        all_banners = {}
        if os.path.exists(read_file):
            try:
                with open(read_file, "r", encoding="utf-8") as f:
                    all_banners = json.load(f)
            except Exception:
                all_banners = {}

        targets = (
            [game_id.lower().strip()]
            if game_id and game_id.lower().strip() in banner_urls
            else list(banner_urls.keys())
        )

        for g in targets:
            url = banner_urls[g]
            try:
                r = requests.get(url, headers=self.headers, impersonate="chrome", timeout=20)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                game_data = {
                    "game_id": g,
                    "patch_info": "",
                    "banners": [],
                    "weapon_banners": [],
                    "last_updated": datetime.now().isoformat(),
                }

                # 1. BANNERS DE PERSONAGEM (Current Character Banners)
                for h in soup.find_all(["h2", "h3"]):
                    if "current character banners" in h.get_text().strip().lower():
                        sec_header = h.find_parent(class_="section-header") or h.parent
                        phase_node = sec_header.find_next_sibling(class_="phase-summary")
                        if phase_node:
                            raw_phase = phase_node.get_text(separator=" ").strip()
                            game_data["patch_info"] = re.sub(r"\s+", " ", raw_phase)

                        grid = sec_header.find_next_sibling(class_="banner-grid") or sec_header.find_next(
                            class_="banner-grid"
                        )
                        cards = grid.find_all(class_="banner-card") if grid else []

                        # Coleta o pool de 4★ compartilhados na grade deste banner
                        shared_4stars = []
                        for c in cards:
                            ru_sec = c.find(attrs={"aria-label": lambda x: x and "secondary rate up" in str(x).lower()})
                            if ru_sec:
                                for a in ru_sec.find_all("a"):
                                    t = a.get_text().strip()
                                    if t and t not in shared_4stars:
                                        shared_4stars.append(t)

                        for idx, c in enumerate(cards):
                            # Busca imagem da arte do banner (banner-art)
                            art_container = c.find(class_=lambda x: x and "banner-art" in x)
                            img = art_container.find("img") if art_container else c.find("img")
                            img_src = img.get("src") or img.get("data-src") or "" if img else ""
                            if img_src and not img_src.startswith("http"):
                                img_src = "https://www.prydwen.gg" + img_src

                            # Busca nome principal do personagem 5★
                            b_name_el = c.find(class_="banner-name")
                            main_char = b_name_el.get_text().strip() if b_name_el else ""
                            if not main_char:
                                char_links = [
                                    a
                                    for a in c.find_all("a")
                                    if "/characters/" in a.get("href", "") or "/agents/" in a.get("href", "")
                                ]
                                names = list(
                                    dict.fromkeys([a.get_text().strip() for a in char_links if a.get_text().strip()])
                                )
                                if names:
                                    main_char = names[0]

                            if not main_char:
                                continue

                            # Busca 4★ com taxa aumentada (Secondary Rate Up)
                            rate_up_sec = c.find(attrs={"aria-label": lambda x: x and "secondary rate up" in str(x).lower()})
                            featured_4s = []
                            if rate_up_sec:
                                for a in rate_up_sec.find_all("a"):
                                    t = a.get_text().strip()
                                    if t and t not in featured_4s:
                                        featured_4s.append(t)

                            if not featured_4s and shared_4stars:
                                featured_4s = list(shared_4stars)

                            # Preserva imagem oficial in-game e 4★ caso o scraper venha com placeholder
                            prev_banner = None
                            if g in all_banners and "banners" in all_banners[g]:
                                for pb in all_banners[g]["banners"]:
                                    if pb.get("character_name", "").lower() == main_char.lower():
                                        prev_banner = pb
                                        break

                            if prev_banner:
                                prev_img = prev_banner.get("banner_image", "")
                                if prev_img and (
                                    prev_img.startswith("/assets/")
                                    or "_full.webp" in img_src
                                    or "banner1" in img_src
                                    or "banner2" in img_src
                                    or not img_src
                                ):
                                    img_src = prev_img
                                if not featured_4s and prev_banner.get("featured_4stars"):
                                    featured_4s = prev_banner.get("featured_4stars", [])
                                banner_title = prev_banner.get("banner_title", "")
                            else:
                                banner_title = ""

                            schedule_meta = self._extract_banner_schedule_meta(c, game_data.get("patch_info", ""))
                            banner_entry = {
                                "character_name": main_char,
                                "banner_image": img_src,
                                "featured_4stars": featured_4s,
                                "is_primary": (idx == 0),
                                **schedule_meta,
                            }
                            if banner_title:
                                banner_entry["banner_title"] = banner_title

                            game_data["banners"].append(banner_entry)
                        break

                # 2. BANNERS DE ARMA / CONE / MOTOR (Current Weapon / Light Cone Banners)
                for h in soup.find_all(["h2", "h3"]):
                    h_text = h.get_text().strip().lower()
                    if "current weapon banners" in h_text or "current light cone banners" in h_text:
                        sec_header = h.find_parent(class_="section-header") or h.parent
                        grid = sec_header.find_next_sibling(class_="banner-grid") or sec_header.find_next(
                            class_="banner-grid"
                        )
                        cards = grid.find_all(class_="banner-card") if grid else []

                        # Pool compartilhado de 4★ de armas
                        shared_wp_4s = []
                        for c in cards:
                            ru_sec = c.find(attrs={"aria-label": lambda x: x and "secondary rate up" in str(x).lower()})
                            if ru_sec:
                                for a in ru_sec.find_all("a"):
                                    t = a.get_text().strip()
                                    if t and t not in shared_wp_4s:
                                        shared_wp_4s.append(t)

                        for idx, c in enumerate(cards):
                            # Imagem do banner de arma
                            art_container = c.find(class_=lambda x: x and ("banner-art" in x or "lightcone-art" in x))
                            bg_img = c.find("img", class_="lightcone-bg-image")
                            img = bg_img or (art_container.find("img") if art_container else c.find("img"))
                            img_src = img.get("src") or img.get("data-src") or "" if img else ""
                            if img_src and not img_src.startswith("http"):
                                img_src = "https://www.prydwen.gg" + img_src

                            # Imagem detalhada alternativa da arma (ícone ou arte do item)
                            card_img = c.find("img", class_="lightcone-card-image")
                            remote_card_img = (
                                card_img.get("src") or card_img.get("data-src") or "" if card_img else ""
                            )
                            if remote_card_img and not remote_card_img.startswith("http"):
                                remote_card_img = "https://www.prydwen.gg" + remote_card_img

                            b_name_el = c.find(class_="banner-name")
                            raw_banner_name = b_name_el.get_text().strip() if b_name_el else ""

                            # 4★ rate-up do card
                            ru_sec = c.find(attrs={"aria-label": lambda x: x and "secondary rate up" in str(x).lower()})
                            featured_4s = []
                            if ru_sec:
                                for a in ru_sec.find_all("a"):
                                    t = a.get_text().strip()
                                    if t and t not in featured_4s:
                                        featured_4s.append(t)
                            if not featured_4s and shared_wp_4s:
                                featured_4s = list(shared_wp_4s)

                            # Tratamento Genshin: Epitome Invocation com 2 armas 5★
                            if g == "genshin" and "epitome invocation" in raw_banner_name.lower():
                                sub = re.sub(r"^Epitome Invocation:\s*", "", raw_banner_name, flags=re.IGNORECASE)
                                weap_names = [w.strip() for w in sub.split("&") if w.strip()]
                                for w_idx, w_name in enumerate(weap_names):
                                    prev_wb = None
                                    if g in all_banners and "weapon_banners" in all_banners[g]:
                                        for pwb in all_banners[g]["weapon_banners"]:
                                            if pwb.get("character_name", "").lower() == w_name.lower():
                                                prev_wb = pwb
                                                break
                                    w_img = (
                                        prev_wb.get("banner_image", img_src)
                                        if prev_wb and prev_wb.get("banner_image", "").startswith("/assets/")
                                        else img_src
                                    )
                                    w_4s = featured_4s or (prev_wb.get("featured_4stars", []) if prev_wb else [])
                                    w_title = prev_wb.get("banner_title", raw_banner_name) if prev_wb else raw_banner_name

                                    schedule_meta = self._extract_banner_schedule_meta(c, game_data.get("patch_info", ""))
                                    game_data["weapon_banners"].append(
                                        {
                                            "character_name": w_name,
                                            "banner_title": w_title,
                                            "banner_image": w_img,
                                            "featured_4stars": w_4s,
                                            "is_primary": (w_idx == 0),
                                            "banner_type": "weapon",
                                            **schedule_meta,
                                        }
                                    )
                            else:
                                # HSR e ZZZ
                                wp_name = raw_banner_name
                                if not wp_name:
                                    wp_links = [
                                        a
                                        for a in c.find_all("a")
                                        if "/light-cones/" in a.get("href", "") or "w-engines" in a.get("href", "")
                                    ]
                                    names = list(
                                        dict.fromkeys([a.get_text().strip() for a in wp_links if a.get_text().strip()])
                                    )
                                    if names:
                                        wp_name = names[0]

                                if wp_name:
                                    prev_wb = None
                                    if g in all_banners and "weapon_banners" in all_banners[g]:
                                        for pwb in all_banners[g]["weapon_banners"]:
                                            if pwb.get("character_name", "").lower() == wp_name.lower():
                                                prev_wb = pwb
                                                break

                                    w_img = (
                                        prev_wb.get("banner_image", img_src)
                                        if prev_wb and prev_wb.get("banner_image", "").startswith("/assets/")
                                        else img_src
                                    )
                                    w_4s = featured_4s or (prev_wb.get("featured_4stars", []) if prev_wb else [])
                                    w_title = prev_wb.get("banner_title", wp_name) if prev_wb else wp_name

                                    schedule_meta = self._extract_banner_schedule_meta(c, game_data.get("patch_info", ""))
                                    entry = {
                                        "character_name": wp_name,
                                        "banner_title": w_title,
                                        "banner_image": w_img,
                                        "featured_4stars": w_4s,
                                        "is_primary": (idx == 0),
                                        "banner_type": "weapon",
                                        **schedule_meta,
                                    }
                                    if remote_card_img:
                                        entry["remote_banner_image"] = remote_card_img
                                    game_data["weapon_banners"].append(entry)
                        break

                # Fallback de preservação caso não tenha raspado weapon banners
                if not game_data["weapon_banners"] and g in all_banners and "weapon_banners" in all_banners[g]:
                    game_data["weapon_banners"] = all_banners[g]["weapon_banners"]

                if game_data["banners"]:
                    all_banners[g] = game_data
            except Exception as e:
                print(f"[WARN] Falha ao raspar banners atuais de {g}: {e}")

        # Salva consolidação no manifesto JSON em static_data
        try:
            os.makedirs(static_dir, exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(all_banners, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Erro ao salvar static_data/current_banners.json: {e}")

        if game_id and game_id.lower().strip() in all_banners:
            return all_banners[game_id.lower().strip()]
        return all_banners
