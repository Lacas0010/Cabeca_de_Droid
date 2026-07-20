import os
import re
import sys
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class GenshinMetaScraper:
    def __init__(self, output_path: str = "genshin/meta_kqm_genshin.md"):
        """
        Inicializa o raspador de meta e tier list de Genshin Impact do Game8.
        """
        self.url = "https://game8.co/games/Genshin-Impact/archives/297465" # URL ativa e atualizada para a tier list
        self.output_path = output_path
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    def _log(self, message: str, level: str = "INFO", logger_cb=None):
        """
        Envia logs para o callback (GUI) ou imprime no console caso não fornecido.
        """
        if logger_cb:
            logger_cb(message, level)
        else:
            print(f"[{level}] {message}")

    def scrape_tier_list(self, logger_cb=None) -> dict:
        """
        Acessa o site Game8 usando Playwright, aguarda a renderização do HTML e faz o parse da Tier List.
        Retorna um dicionário estruturado: { role: { rank: [ characters ] } }
        """
        self._log(f"Iniciando navegador Playwright para acessar Game8...", "INFO", logger_cb)
        
        data = {
            "Main DPS": {},
            "Sub-DPS": {},
            "Support": {}
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            try:
                self._log(f"Carregando a página: {self.url}", "INFO", logger_cb)
                # Usamos domcontentloaded para evitar timeouts com carregamento infinito de propagandas
                page.goto(self.url, timeout=40000, wait_until="domcontentloaded")
                
                # Aguarda um pequeno delay para garantir execução do JS básico
                time.sleep(2)
                
                html_content = page.content()
                self._log(f"Página carregada com sucesso ({len(html_content)} bytes). Realizando parsing...", "INFO", logger_cb)
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Scan por cabeçalhos que demarcam ranks e papéis de combate
                # Exemplo de texto de cabeçalho: "SS Rank Main DPS Characters"
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                
                parsed_count = 0
                for h in headings:
                    heading_text = h.text.strip()
                    match = re.match(r'^([A-Z0-9\+]+)\s+Rank\s+(Main DPS|Sub-DPS|Support)\s+Characters', heading_text, re.I)
                    
                    if match:
                        rank = match.group(1).upper()
                        role = match.group(2)
                        
                        table = h.find_next('table')
                        if not table:
                            continue
                            
                        rows = table.find_all('tr')
                        if len(rows) <= 1:
                            continue
                            
                        # Inicializa o dicionário para a função se não existir
                        if role not in data:
                            data[role] = {}
                        if rank not in data[role]:
                            data[role][rank] = []
                            
                        self._log(f"Parseando tabela: {rank} Rank {role}...", "DEBUG", logger_cb)
                        
                        # Processamento estruturado em grupos de 3 linhas (Estrutura Game8)
                        i = 1
                        while i < len(rows):
                            row_a = rows[i]
                            cells_a = row_a.find_all(['td', 'th'])
                            if len(cells_a) >= 3:
                                char_cell = cells_a[0]
                                char_name = char_cell.text.strip()
                                
                                # Limpa o nome usando a tag 'alt' da imagem se possível (evita nomes de arquivos)
                                img = char_cell.find('img')
                                if img and img.get('alt'):
                                    alt = img.get('alt').replace('Genshin Impact - ', '').replace(' Image', '').strip()
                                    if alt:
                                        char_name = alt
                                
                                # Linha B: Armas e Artefatos Recomendados
                                weapon = "N/A"
                                artifact = "N/A"
                                if i + 1 < len(rows):
                                    row_b = rows[i+1]
                                    cells_b = row_b.find_all(['td', 'th'])
                                    if len(cells_b) >= 2:
                                        weapon = cells_b[0].text.strip()
                                        artifact = cells_b[1].text.strip()
                                        # Remove espaços/quebras de linha duplicados
                                        weapon = " ".join(weapon.split())
                                        artifact = " ".join(artifact.split())
                                
                                # Linha C: Resumo / Justificativa de Rank
                                justification = ""
                                if i + 2 < len(rows):
                                    row_c = rows[i+2]
                                    cells_c = row_c.find_all(['td', 'th'])
                                    if len(cells_c) >= 1:
                                        raw_just = cells_c[0].get_text(separator='\n').strip()
                                        lines = [line.strip().lstrip('・') for line in raw_just.split('\n') if line.strip()]
                                        justification = "\n".join(f"- {line}" for line in lines)
                                
                                data[role][rank].append({
                                    "name": char_name,
                                    "weapon": weapon,
                                    "artifact": artifact,
                                    "justification": justification
                                })
                                parsed_count += 1
                                i += 3
                            else:
                                i += 1
                                
                self._log(f"Fim do parsing. Total de {parsed_count} personagens extraídos.", "SUCCESS", logger_cb)
                
            except Exception as e:
                self._log(f"Erro durante a raspagem do Game8: {e}", "ERROR", logger_cb)
                raise e
            finally:
                browser.close()
                
        return data

    def save_to_markdown(self, data: dict, filepath: str = None, logger_cb=None) -> str:
        """
        Gera e salva o relatório estruturado de Tier List e Meta em Markdown limpo para RAG.
        """
        if not filepath:
            filepath = self.output_path
            
        self._log(f"Gerando arquivo Markdown em: {filepath}", "INFO", logger_cb)
        
        lines = []
        lines.append("# Genshin Impact Tier List & Meta Report")
        lines.append(f"Dados atualizados e extraídos diretamente do Game8.co em {time.strftime('%Y-%m-%d %H:%M:%S')}.")
        lines.append("")
        lines.append("Este relatório consolida os personagens recomendados do meta de Genshin Impact divididos por função de combate (Main DPS, Sub-DPS e Support) e ranks de viabilidade (SS, S, A, B, C, D). O conteúdo foi formatado especificamente para servir como base de conhecimento de alta densidade informativa para sistemas de RAG.")
        lines.append("")
        
        # 1. Resumo do Topo do Meta (SS Rank com explicações detalhadas)
        lines.append("## 🏆 Resumo do Topo do Meta (SS Rank)")
        lines.append("Personagens considerados de altíssimo impacto e desempenho excepcional no abismo e conteúdos de endgame na versão atual.")
        lines.append("")
        
        for role in ["Main DPS", "Sub-DPS", "Support"]:
            lines.append(f"### {role} - Top Ranks (SS)")
            ss_chars = data.get(role, {}).get("SS", [])
            if ss_chars:
                for c in ss_chars:
                    lines.append(f"#### ⭐ {c['name']}")
                    lines.append(f"- **Build Recomendada:**")
                    lines.append(f"  - **Arma:** {c['weapon']}")
                    lines.append(f"  - **Artefato:** {c['artifact']}")
                    lines.append(f"- **Análise de Meta:**")
                    # Indenta cada ponto da justificativa
                    just_indented = "\n".join(f"  {line}" for line in c['justification'].split('\n'))
                    lines.append(just_indented)
                    lines.append("")
            else:
                lines.append("Nenhum personagem listado no rank SS.")
                lines.append("")
                
        # 2. Classificação Geral e Tabelas Completas
        lines.append("## 📊 Classificação Completa da Tier List por Categoria")
        lines.append("")
        
        for role in ["Main DPS", "Sub-DPS", "Support"]:
            lines.append(f"### {role}")
            lines.append("")
            
            # Percorre os ranks de forma ordenada
            for rank in ["SS", "S", "A", "B", "C", "D"]:
                chars = data.get(role, {}).get(rank, [])
                if not chars:
                    continue
                    
                lines.append(f"#### Rank {rank}")
                lines.append("")
                
                # Tabela de build recomendada
                lines.append("| Personagem | Arma Recomendada | Artefato Recomendado |")
                lines.append("| --- | --- | --- |")
                for c in chars:
                    lines.append(f"| **{c['name']}** | {c['weapon']} | {c['artifact']} |")
                lines.append("")
                
                # Detalhes de meta de todos os personagens deste rank (importante para RAG)
                lines.append("**Resumos de Meta:**")
                lines.append("")
                for c in chars:
                    lines.append(f"- **{c['name']}:**")
                    just_indented = "\n".join(f"  {line}" for line in c['justification'].split('\n'))
                    lines.append(just_indented)
                lines.append("")
                lines.append("---")
                lines.append("")
                
        # Garante a criação dos diretórios necessários
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        
        # Salva o arquivo final
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        self._log(f"Relatório de meta salvo com sucesso em: {filepath}", "SUCCESS", logger_cb)
        return filepath

    def run(self, logger_cb=None) -> str:
        """
        Executa o processo completo de raspagem e gravação.
        """
        try:
            data = self.scrape_tier_list(logger_cb)
            filepath = self.save_to_markdown(data, logger_cb=logger_cb)
            return filepath
        except Exception as e:
            self._log(f"Falha na execução do scraper de meta: {e}", "ERROR", logger_cb)
            raise e

    def run_full_scrape(self, logger_cb=None) -> str:
        """
        Alias para run() para compatibilidade com o chamador da interface.
        """
        return self.run(logger_cb)

