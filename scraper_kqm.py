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
        Inicializa o raspador de guias do KeqingMains (KQM) com Sessão HTTP resiliente.
        """
        self.base_url = "https://keqingmains.com"
        self.output_dir = output_dir
        
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

    def html_to_markdown(self, element) -> str:
        """
        Converte recursivamente elementos do BeautifulSoup em Markdown limpo.
        """
        if isinstance(element, Comment):
            return ""
        if isinstance(element, NavigableString):
            return element.text
        
        tag_name = element.name.lower()
        
        if tag_name in ['script', 'style', 'noscript', 'iframe']:
            return ""
            
        # Headers
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            header_text = "".join(self.html_to_markdown(c) for c in element.children).strip()
            header_text = re.sub(r'\s+', ' ', header_text)
            if not header_text:
                return ""
            return f"\n\n{'#' * level} {header_text}\n\n"
            
        # Paragraphs
        if tag_name == 'p':
            p_text = "".join(self.html_to_markdown(c) for c in element.children).strip()
            if not p_text:
                return ""
            return f"\n\n{p_text}\n\n"
            
        # Bold
        if tag_name in ['strong', 'b']:
            text = "".join(self.html_to_markdown(c) for c in element.children).strip()
            if not text:
                return ""
            return f" **{text}** "
            
        # Italics
        if tag_name in ['em', 'i']:
            text = "".join(self.html_to_markdown(c) for c in element.children).strip()
            if not text:
                return ""
            return f" *{text}* "
            
        # Links
        if tag_name == 'a':
            text = "".join(self.html_to_markdown(c) for c in element.children).strip()
            href = element.get('href', '').strip()
            if not href or href.startswith('#') or not text:
                return text
            # Transforma caminhos relativos em absolutos
            if href.startswith('/'):
                href = self.base_url + href
            return f"[{text}]({href})"
            
        # Unordered Lists
        if tag_name == 'ul':
            items = []
            for child in element.children:
                if child.name and child.name.lower() == 'li':
                    li_text = "".join(self.html_to_markdown(c) for c in child.children).strip()
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
                    li_text = "".join(self.html_to_markdown(c) for c in child.children).strip()
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
            for col in cols:
                col_text = "".join(self.html_to_markdown(c) for c in col.children).strip()
                col_text = re.sub(r'\s+', ' ', col_text)
                header_names.append(col_text)
                
            markdown_table.append("| " + " | ".join(header_names) + " |")
            markdown_table.append("| " + " | ".join(["---"] * len(header_names)) + " |")
            
            for row in rows[1:]:
                cols = row.find_all('td')
                row_data = []
                for col in cols:
                    col_text = "".join(self.html_to_markdown(c) for c in col.children).strip()
                    col_text = re.sub(r'\s+', ' ', col_text)
                    row_data.append(col_text)
                if row_data:
                    while len(row_data) < len(header_names):
                        row_data.append("")
                    row_data = row_data[:len(header_names)]
                    markdown_table.append("| " + " | ".join(row_data) + " |")
                    
            return "\n\n" + "\n".join(markdown_table) + "\n\n"
            
        # Fallback para tags de agrupamento
        return "".join(self.html_to_markdown(c) for c in element.children)

    def get_character_guide(self, char_name: str, logger_cb=None) -> str:
        """
        Extrai o guia de um personagem do KQM e retorna em formato Markdown limpo.
        Tenta diferentes URLs candidatas (Full Guide e Quick Guide) como fallback dinâmico.
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
                self._log(f"Testando URL para {char_name}: {url}", "DEBUG", logger_cb)
                r = self.session.get(url, timeout=12)
                if r.status_code == 200:
                    self._log(f"✅ Guia encontrado em: {url}", "SUCCESS", logger_cb)
                    response_text = r.text
                    final_url = url
                    break
            except requests.RequestException as req_err:
                self._log(f"Erro na requisição para {url}: {req_err}", "DEBUG", logger_cb)
                continue
                
        if not response_text:
            raise FileNotFoundError(f"Guia para {char_name} (slug: {slug}) não encontrado em nenhuma das URLs candidatas do KQM.")
            
        soup = BeautifulSoup(response_text, 'html.parser')
        
        # Encontra a div de conteúdo padrão do WordPress
        entry_content = soup.find('div', class_='entry-content')
        if not entry_content:
            # Tenta encontrar no article principal
            entry_content = soup.find('article')
            
        if not entry_content:
            raise Exception(f"Não foi possível localizar o conteúdo principal da página para {char_name}.")
            
        # Decompõe modais, propagandas, TOC e links sociais
        toc = (entry_content.find('div', id='ftoc-wrapper') or 
               entry_content.find('div', class_='toc') or 
               entry_content.find('div', id='toc_container') or 
               entry_content.find('div', class_='ftoc-wrapper'))
        if toc:
            toc.decompose()
            
        for trash in entry_content.find_all(class_=re.compile(r'share|social|ads|advertisement|sidebar|modal', re.I)):
            trash.decompose()
            
        # Realiza a conversão
        markdown_text = self.html_to_markdown(entry_content)
        
        # Limpa quebras de linhas redundantes
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
        markdown_text = markdown_text.strip()
        
        # Monta a estrutura final
        final_md = []
        final_md.append(f"# Guia de Build - {char_name.title()}")
        final_md.append("Dados extraídos do site KeqingMains (KQM).")
        final_md.append(f"Link oficial: {final_url}")
        final_md.append("")
        final_md.append(markdown_text)
        
        return "\n".join(final_md)

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

    def scrape_all_guides(self, character_list: list, logger_cb=None):
        """
        Executa a coleta em lote de uma lista de personagens com delays respeitosos e tratamento de erros.
        """
        self._log(f"Iniciando coleta em lote de {len(character_list)} personagens no KQM...", "INFO", logger_cb)
        success_count = 0
        total = len(character_list)
        
        for idx, char_name in enumerate(character_list, 1):
            progress_val = idx / total if total > 0 else 1.0
            self._log(f"({idx}/{total}) Coletando guia de {char_name}...", "INFO", logger_cb, progresso=progress_val)
            
            try:
                slug = self._normalize_name(char_name)
                if slug in self.skip_slugs:
                    self._log(f"Pulado: {char_name} (NPC/Manequim detectado).", "WARN", logger_cb, progresso=progress_val)
                    continue
                    
                md_content = self.get_character_guide(char_name, logger_cb)
                if md_content:
                    filepath = self.save_to_markdown(char_name, md_content)
                    if filepath:
                        success_count += 1
                        self._log(f"Guia de {char_name} obtido com sucesso!", "SUCCESS", logger_cb, progresso=progress_val)
                    else:
                        self._log(f"Erro ao salvar arquivo de {char_name}.", "ERROR", logger_cb, progresso=progress_val)
                else:
                    self._log(f"Guia de {char_name} não encontrado no KQM.", "WARN", logger_cb, progresso=progress_val)
                    
            except FileNotFoundError as fnf:
                self._log(f"⚠️ {fnf}", "WARN", logger_cb, progresso=progress_val)
            except Exception as e:
                self._log(f"Falha ao obter guia de {char_name}: {e}", "ERROR", logger_cb, progresso=progress_val)
                
            time.sleep(1.0)
            
        self._log(f"Fim da coleta em lote. {success_count} guias obtidos em: {self.output_dir}", "SUCCESS", logger_cb, progresso=1.0)
