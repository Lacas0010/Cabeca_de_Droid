import os
import re
import time
import requests
from bs4 import BeautifulSoup, NavigableString, Comment
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class KQMScraper:
    def __init__(self, output_dir: str = "genshin/guias/"):
        """
        Inicializa o raspador de guias do KeqingMains (KQM) com Sessão HTTP resiliente
        e suporte a fallback automático para o Game8.
        """
        self.base_url = "https://keqingmains.com"
        self.output_dir = output_dir
        self.game8_url_map = None
        
        # Mapeamento especial de nomes de personagens do Genshin para a slug do KQM (Nome bruto PT-BR/EN -> Slug base)
        self.slug_map = {
            "viajante": "dendro-traveler",
            "traveler": "dendro-traveler",
            "kaedehara kazuha": "kazuha",
            "kazuha": "kazuha",
            "shogun raiden": "raiden",
            "raiden shogun": "raiden",
            "kujou sara": "sara",
            "kuki shinobu": "shinobu",
            "kamisato ayaka": "ayaka",
            "kamisato ayato": "ayato",
            "shikanoin heizou": "heizou",
            "sangonomiya kokomi": "kokomi",
            "yae miko": "yae"
        }

        # Dicionário de exceções conhecidas de nomes/slugs do KQM pós-processamento
        self.slug_aliases = {
            "kaedehara-kazuha": "kazuha",
            "shogun-raiden": "raiden",
            "raiden-shogun": "raiden",
            "kujou-sara": "sara",
            "kuki-shinobu": "shinobu",
            "viajante": "dendro-traveler",
            "traveler": "dendro-traveler",
            "kamisato-ayaka": "ayaka",
            "kamisato-ayato": "ayato",
            "shikanoin-heizou": "heizou",
            "sangonomiya-kokomi": "kokomi",
        }

        # Slugs/Personagens a ignorar (NPCs/Manequins do Roster)
        self.skip_slugs = {"manequina", "mannequin", "nicole"}

        # Configuração da Sessão HTTP Resiliente com Urllib3 Retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        # Estratégia de re-tentativa exponencial para falhas temporárias (status 429, 500, 502, 503, 504)
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # sleep exponencial: 1s, 2s, 4s...
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _log(self, message: str, level: str = "INFO", logger_cb=None, progresso: float = None):
        if logger_cb:
            try:
                logger_cb(message, level, progresso=progresso)
            except TypeError:
                logger_cb(message, level)
        else:
            print(f"[{level}] {message}")

    def _normalize_name(self, char_name: str) -> str:
        """
        Normaliza o nome do personagem para encontrar a slug do KQM correta.
        """
        name_clean = char_name.strip().lower()
        if name_clean in self.slug_map:
            name_clean = self.slug_map[name_clean]
        
        # Remove caracteres especiais e troca espaços por hifens
        slug = re.sub(r'[^a-z0-9\s-]', '', name_clean)
        slug = re.sub(r'[\s_]+', '-', slug)
        
        # Aplica aliases secundários se houver
        return self.slug_aliases.get(slug, slug)

    def _is_kqm_guide_valid(self, md_content: str) -> bool:
        """
        Verifica se o guia extraído do KQM é válido e completo,
        rejeitando stubs/placeholders que avisam que o guia precisa de autor ou está em desenvolvimento.
        """
        if not md_content or len(md_content.strip()) < 400:
            return False
        md_lower = md_content.lower()
        placeholder_phrases = [
            "needs an author",
            "guide is currently under development",
            "coming soon",
            "wip guide",
            "work in progress",
            "under construction"
        ]
        if len(md_content) < 1200 and any(phrase in md_lower for phrase in placeholder_phrases):
            return False
        return True

    def _build_game8_url_map(self):
        """
        Coleta e mapeia dinamicamente as URLs de guias de personagens do Game8.
        """
        index_urls = [
            "https://game8.co/games/Genshin-Impact/archives/297465",
            "https://game8.co/games/Genshin-Impact/archives/297491",
            "https://game8.co/games/Genshin-Impact/archives/530535"
        ]
        url_map = {}
        excluded_kws = [
            'tier', 'version', 'codes', 'update', 'weapon', 'artifact', 'map',
            'quest', 'boss', 'story', 'comment', 'livestream', 'reroll', 'team comp',
            'character', 'fishing', 'ore', 'walkthrough', 'banner', 'lore', 'profile',
            'materials', 'quiz', 'survey'
        ]
        for idx_url in index_urls:
            try:
                r = self.session.get(idx_url, timeout=12)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/games/Genshin-Impact/archives/' not in href:
                        continue
                    if href.startswith('/'):
                        href = 'https://game8.co' + href
                    
                    texts = [a.get_text(strip=True)]
                    img = a.find('img')
                    if img and img.get('alt'):
                        texts.append(img['alt'])
                        
                    for raw in texts:
                        if not raw:
                            continue
                        clean_name = raw.lower().strip()
                        clean_name = re.sub(r'genshin\s*-\s*', '', clean_name)
                        clean_name = re.sub(r'\s+(dps|sub-dps|support|healer|shielder)\s+rank', '', clean_name)
                        clean_name = re.sub(r'\s+(best\s+builds?|builds?|guides?|rating\s+and\s+info|tier\s+list|banner|lore|profile|materials).*$', '', clean_name)
                        clean_name = clean_name.strip()
                        
                        if clean_name and len(clean_name) > 2:
                            if not any(kw in clean_name for kw in excluded_kws):
                                if clean_name not in url_map:
                                    url_map[clean_name] = href
            except Exception as e:
                pass
        self.game8_url_map = url_map
        return url_map

    def get_game8_guide(self, char_name: str, logger_cb=None) -> str:
        """
        Extrai o guia de um personagem do Game8 como fallback quando o KQM não estiver disponível.
        """
        if self.game8_url_map is None:
            self._log("Carregando mapa de guias do Game8...", "DEBUG", logger_cb)
            self._build_game8_url_map()

        clean_name = char_name.lower().strip()
        clean_name_short = re.sub(r'\s+(shogun|kamisato|sangonomiya|shikanoin|kujou|kuki)\s*', ' ', clean_name).strip()

        target_url = None
        # Busca por correspondência exata
        for key, url in self.game8_url_map.items():
            if key == clean_name or key == clean_name_short:
                target_url = url
                break
        
        if not target_url:
            for key, url in self.game8_url_map.items():
                if key in clean_name or clean_name in key:
                    target_url = url
                    break

        if not target_url:
            # Fallback de busca ativa no Game8
            try:
                search_url = f"https://game8.co/games/Genshin-Impact/search?keyword={requests.utils.quote(char_name)}"
                r = self.session.get(search_url, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if '/games/Genshin-Impact/archives/' in href and ('build' in href.lower() or 'guide' in href.lower() or char_name.lower() in href.lower()):
                            if not any(x in href.lower() for x in ['banner', 'lore', 'profile', 'materials', 'quiz', 'survey']):
                                target_url = href if href.startswith('http') else 'https://game8.co' + href
                                break
            except Exception:
                pass

        if not target_url:
            raise FileNotFoundError(f"Guia do Game8 não encontrado para '{char_name}'.")

        self._log(f"Buscando guia Game8 para {char_name}: {target_url}", "DEBUG", logger_cb)
        r = self.session.get(target_url, timeout=15)
        if r.status_code != 200:
            raise FileNotFoundError(f"Status {r.status_code} ao acessar {target_url}")

        soup = BeautifulSoup(r.text, 'html.parser')
        container = (
            soup.find('div', class_='p-archiveContent__container') or
            soup.find('div', class_='p-archiveBody__main') or
            soup.find('div', class_='archive-style-wrapper') or
            soup.find('article')
        )
        if not container:
            raise Exception(f"Não foi possível localizar o conteúdo principal da página no Game8 para {char_name}.")

        import copy
        clean_container = copy.copy(container)

        for garbage in clean_container.find_all(class_=re.compile(r'a-ad|comment|share|social|p-archiveContent__side|p-archiveFeedback|p-membershipModal|l-breadcrumb|p-rootHeader', re.I)):
            garbage.decompose()

        for h in clean_container.find_all(['h2', 'div'], class_=re.compile(r'comment|author', re.I)):
            h.decompose()

        markdown_text = self.html_to_markdown(clean_container, base_url="https://game8.co")
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text).strip()

        final_md = []
        final_md.append(f"# Guia de Build - {char_name.title()}")
        final_md.append("Dados extraídos do site Game8 (Fallback - KQM não disponível).")
        final_md.append(f"Link oficial: {target_url}")
        final_md.append("")
        final_md.append(markdown_text)

        return "\n".join(final_md)

    def html_to_markdown(self, element, base_url: str = None) -> str:
        """
        Converte recursivamente elementos do BeautifulSoup em Markdown limpo.
        """
        effective_base_url = base_url if base_url else self.base_url

        if isinstance(element, Comment):
            return ""
        if isinstance(element, NavigableString):
            return element.text
        
        tag_name = element.name.lower()
        
        if tag_name in ['script', 'style', 'noscript', 'iframe', 'button', 'input']:
            return ""
            
        # Headers
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            header_text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in element.children).strip()
            header_text = re.sub(r'\s+', ' ', header_text)
            if not header_text:
                return ""
            return f"\n\n{'#' * level} {header_text}\n\n"
            
        # Paragraphs
        if tag_name == 'p':
            p_text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in element.children).strip()
            if not p_text:
                return ""
            return f"\n\n{p_text}\n\n"
            
        # Bold
        if tag_name in ['strong', 'b']:
            text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in element.children).strip()
            if not text:
                return ""
            return f" **{text}** "
            
        # Italics
        if tag_name in ['em', 'i']:
            text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in element.children).strip()
            if not text:
                return ""
            return f" *{text}* "
            
        # Links
        if tag_name == 'a':
            text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in element.children).strip()
            href = element.get('href', '').strip()
            if not href or href.startswith('#') or not text:
                return text
            # Transforma caminhos relativos em absolutos
            if href.startswith('/'):
                href = effective_base_url + href
            return f"[{text}]({href})"
            
        # Unordered Lists
        if tag_name == 'ul':
            items = []
            for child in element.children:
                if child.name and child.name.lower() == 'li':
                    li_text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in child.children).strip()
                    if li_text:
                        li_text = li_text.replace('\n', '\n  ')
                        items.append(f"- {li_text}")
            return "\n" + "\n".join(items) + "\n"
            
        # Ordered Lists
        if tag_name == 'ol':
            items = []
            count = 1
            for child in element.children:
                if child.name and child.name.lower() == 'li':
                    li_text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in child.children).strip()
                    if li_text:
                        li_text = li_text.replace('\n', '\n  ')
                        items.append(f"{count}. {li_text}")
                        count += 1
            return "\n" + "\n".join(items) + "\n"
            
        # Breaks
        if tag_name == 'br':
            return "\n"
            
        # Tables
        if tag_name == 'table':
            markdown_table = []
            rows = element.find_all('tr')
            if not rows:
                return ""
                
            header_row = rows[0]
            cols = header_row.find_all(['th', 'td'])
            header_names = []
            for idx_col, col in enumerate(cols):
                col_text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in col.children).strip()
                col_text = re.sub(r'\s+', ' ', col_text)
                if not col_text and idx_col == 0:
                    col_text = "Rank"
                header_names.append(col_text)
                
            markdown_table.append("| " + " | ".join(header_names) + " |")
            markdown_table.append("| " + " | ".join(["---"] * len(header_names)) + " |")
            
            for row in rows[1:]:
                cols = row.find_all(['th', 'td'])
                row_data = []
                for col in cols:
                    col_text = "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in col.children).strip()
                    col_text = re.sub(r'\s+', ' ', col_text)
                    row_data.append(col_text)
                if row_data and any(row_data):
                    while len(row_data) < len(header_names):
                        row_data.append("")
                    row_data = row_data[:len(header_names)]
                    markdown_table.append("| " + " | ".join(row_data) + " |")
                    
            return "\n\n" + "\n".join(markdown_table) + "\n\n"
            
        # Fallback para tags de agrupamento
        return "".join(self.html_to_markdown(c, base_url=effective_base_url) for c in element.children)

    def get_character_guide(self, char_name: str, logger_cb=None, use_fallback: bool = True) -> str:
        """
        Extrai o guia de um personagem do KQM (Principal) e retorna em formato Markdown limpo.
        Caso o guia no KQM não exista ou seja apenas um placeholder/stub, ativa automaticamente o fallback para o Game8.
        """
        slug = self._normalize_name(char_name)
        
        if slug in self.skip_slugs:
            raise FileNotFoundError(f"Personagem '{char_name}' (slug: {slug}) está listado como ignorado (NPC/Manequim).")

        candidate_urls = [
            f"{self.base_url}/{slug}/",                  # 1. Full Guide Padrão
            f"{self.base_url}/q/{slug}-quickguide/",     # 2. Quick Guide Padrão (ex: /q/shinobu-quickguide/)
            f"{self.base_url}/{slug}-quickguide/",       # 3. Quick Guide sem a subpasta /q/
        ]
        
        response_text = None
        final_url = None
        
        for url in candidate_urls:
            try:
                self._log(f"Testando URL KQM para {char_name}: {url}", "DEBUG", logger_cb)
                r = self.session.get(url, timeout=12)
                if r.status_code == 200:
                    response_text = r.text
                    final_url = url
                    break
            except requests.RequestException as req_err:
                self._log(f"Erro na requisição para {url}: {req_err}", "DEBUG", logger_cb)
                continue
                
        kqm_content = None
        if response_text:
            soup = BeautifulSoup(response_text, 'html.parser')
            entry_content = soup.find('div', class_='entry-content') or soup.find('article')
            
            if entry_content:
                toc = (entry_content.find('div', id='ftoc-wrapper') or 
                       entry_content.find('div', class_='toc') or 
                       entry_content.find('div', id='toc_container') or 
                       entry_content.find('div', class_='ftoc-wrapper'))
                if toc:
                    toc.decompose()
                    
                for trash in entry_content.find_all(class_=re.compile(r'share|social|ads|advertisement|sidebar|modal', re.I)):
                    trash.decompose()
                    
                markdown_text = self.html_to_markdown(entry_content)
                markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text).strip()
                
                final_md = []
                final_md.append(f"# Guia de Build - {char_name.title()}")
                final_md.append("Dados extraídos do site KeqingMains (KQM).")
                final_md.append(f"Link oficial: {final_url}")
                final_md.append("")
                final_md.append(markdown_text)
                
                kqm_content = "\n".join(final_md)

        # Se encontrou um guia no KQM e ele é válido/completo, usa o KQM (Principal)
        if kqm_content and self._is_kqm_guide_valid(kqm_content):
            self._log(f"✅ Guia KQM encontrado com sucesso para {char_name}!", "SUCCESS", logger_cb)
            return kqm_content

        # Se o KQM falhou ou retornou um guia incompleto/stub, aciona o Fallback do Game8
        if use_fallback:
            self._log(f"⚠️ Guia do KQM para '{char_name}' indisponível ou incompleto. Acionando fallback no Game8...", "WARN", logger_cb)
            try:
                game8_content = self.get_game8_guide(char_name, logger_cb)
                if game8_content:
                    self._log(f"✅ Guia de {char_name} obtido com sucesso via Game8 (Fallback)!", "SUCCESS", logger_cb)
                    return game8_content
            except Exception as fallback_err:
                self._log(f"Falha no fallback Game8 para '{char_name}': {fallback_err}", "WARN", logger_cb)

        # Se tiver o conteúdo básico do KQM mesmo imperfeito e o fallback falhar, retorna ele como último recurso
        if kqm_content:
            return kqm_content

        raise FileNotFoundError(f"Guia para {char_name} (slug: {slug}) não foi encontrado nem no KQM nem no Game8.")

    def save_to_markdown(self, char_name: str, content: str) -> str:
        """
        Salva o conteúdo em Markdown na pasta de saída.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        slug = self._normalize_name(char_name)
        filename = f"{slug}.md"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def scrape_all_guides(self, character_list: list, logger_cb=None) -> dict:
        """
        Executa a coleta em lote de uma lista de personagens com delays respeitosos e tratamento de erros (KQM Principal + Game8 Fallback).
        Retorna um dicionário com estatísticas dos guias baixados via KQM e Game8.
        """
        self._log(f"Iniciando coleta em lote de {len(character_list)} personagens no KQM (com Fallback no Game8)...", "INFO", logger_cb)
        success_count = 0
        kqm_guides = []
        game8_guides = []
        total = len(character_list)
        
        for idx, char_name in enumerate(character_list, 1):
            progress_val = idx / total if total > 0 else 1.0
            self._log(f"({idx}/{total}) Coletando guia de {char_name}...", "INFO", logger_cb, progresso=progress_val)
            
            try:
                slug = self._normalize_name(char_name)
                if slug in self.skip_slugs:
                    self._log(f"Pulado: {char_name} (NPC/Manequim detectado).", "WARN", logger_cb, progresso=progress_val)
                    continue
                    
                md_content = self.get_character_guide(char_name, logger_cb, use_fallback=True)
                if md_content:
                    filepath = self.save_to_markdown(char_name, md_content)
                    if filepath:
                        success_count += 1
                        if "Game8 (Fallback" in md_content:
                            game8_guides.append(char_name)
                            self._log(f"Guia de {char_name} salvo com sucesso! (fonte: Game8 Fallback)", "SUCCESS", logger_cb, progresso=progress_val)
                        else:
                            kqm_guides.append(char_name)
                            self._log(f"Guia de {char_name} salvo com sucesso! (fonte: KQM)", "SUCCESS", logger_cb, progresso=progress_val)
                    else:
                        self._log(f"Erro ao salvar arquivo de {char_name}.", "ERROR", logger_cb, progresso=progress_val)
                else:
                    self._log(f"Guia de {char_name} não encontrado.", "WARN", logger_cb, progresso=progress_val)
                    
            except FileNotFoundError as fnf:
                self._log(f"⚠️ {fnf}", "WARN", logger_cb, progresso=progress_val)
            except Exception as e:
                self._log(f"Falha ao obter guia de {char_name}: {e}", "ERROR", logger_cb, progresso=progress_val)
                
            time.sleep(1.0)
            
        self._log(f"Fim da coleta em lote. {success_count} guias obtidos em: {self.output_dir}", "SUCCESS", logger_cb, progresso=1.0)
        
        if kqm_guides:
            self._log(f"✅ Guias obtidos via KQM ({len(kqm_guides)}): {', '.join(kqm_guides)}", "INFO", logger_cb)
        if game8_guides:
            self._log(f"🔄 Guias obtidos via Game8 (Fallback) ({len(game8_guides)}): {', '.join(game8_guides)}", "WARN", logger_cb)
            
        return {
            "total": success_count,
            "kqm": kqm_guides,
            "game8": game8_guides
        }
