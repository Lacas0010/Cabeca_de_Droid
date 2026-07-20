import os
import time
import re
from playwright.sync_api import sync_playwright

def bundle_guides(guias_dir: str, output_file: str, game_title: str) -> str:
    """
    Varre a pasta guias_dir, le o conteudo de todos os arquivos .md e concatena em um unico mestre.
    """
    if not os.path.exists(guias_dir) or not os.path.isdir(guias_dir):
        print(f"Diretório {guias_dir} não encontrado para consolidação.")
        return None
        
    md_files = [f for f in os.listdir(guias_dir) if f.endswith(".md")]
    if not md_files:
        print(f"Nenhum arquivo .md encontrado em {guias_dir}.")
        return None
        
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    
    bundled_lines = []
    # Ordena os arquivos para garantir uma ordem consistente
    for filename in sorted(md_files):
        if filename == os.path.basename(output_file):
            continue
            
        filepath = os.path.join(guias_dir, filename)
        char_name = os.path.splitext(filename)[0].replace('_', ' ').title()
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                bundled_lines.append(f"\n\n---\n\n# Character: {char_name}\n\n{content}")
        except Exception as e:
            print(f"Erro ao ler {filename} para consolidar: {e}")
            
    if bundled_lines:
        full_content = f"# Compilado de Guias e Builds - {game_title}\n" + "".join(bundled_lines)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_content)
        print(f"Guias consolidados com sucesso em: {output_file}")
        return os.path.abspath(output_file)
    return None

class NotebookLMUploader:
    def __init__(self, user_data_dir: str = "./user_data_google"):
        """
        Inicializa o uploader do NotebookLM usando Playwright.
        A pasta de dados do usuário permite manter o login persistente do Google.
        """
        self.user_data_dir = os.path.abspath(user_data_dir)

    def upload_sources(self, notebook_url: str, file_paths: list = None):
        """
        Acessa o NotebookLM, aguarda o login se necessário, clica no botão de adicionar fonte
        e faz o upload dos arquivos fornecidos.
        Se file_paths for nulo ou vazio, realiza varredura automática nos caminhos de cada jogo
        (hsr, genshin e zzz) limitando a até 4 arquivos.
        """
        upload_list = []
        
        if file_paths:
            for f in file_paths:
                if os.path.exists(f):
                    upload_list.append(os.path.abspath(f))
        else:
            # HSR
            for f in ["hsr/roster_hsr.md", "hsr/meta_endgame_hsr.md", "hsr/todos_os_guias_hsr.md"]:
                if os.path.exists(f):
                    upload_list.append(os.path.abspath(f))
            # Genshin
            for f in ["genshin/roster_genshin.md", "genshin/meta_kqm_genshin.md", "genshin/todos_os_guias_genshin.md"]:
                if os.path.exists(f):
                    upload_list.append(os.path.abspath(f))
            # ZZZ
            for f in ["zzz/roster_zzz.md", "zzz/meta_endgame_zzz.md", "zzz/todos_os_guias_zzz.md"]:
                if os.path.exists(f):
                    upload_list.append(os.path.abspath(f))
                    
        # Limita a 4 arquivos por upload
        upload_list = upload_list[:4]
            
        if not upload_list:
            raise Exception("Nenhum arquivo Markdown (.md) para upload foi localizado nos caminhos do projeto.")

        print(f"Iniciando Playwright para upload consolidado de: {upload_list}")
        
        with sync_playwright() as p:
            # Lança o navegador com o contexto persistente
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,  # Headed para permitir login manual inicial
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            page = context.new_page()
            
            print(f"Acessando a URL do notebook: {notebook_url}")
            page.goto(notebook_url)
            
            # 1. Garantir Navegação no Notebook Específico
            print("Aguardando carregamento da área logada do NotebookLM (timeout de até 120s)...")
            start_time = time.time()
            logged_in = False
            
            while time.time() - start_time < 120:
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                
                current_url = page.url
                if "notebooklm.google.com" in current_url:
                    if "notebook/" in current_url:
                        logged_in = True
                        break
                    else:
                        print("Na dashboard do NotebookLM. Forçando navegação direta...")
                        page.goto(notebook_url)
                        time.sleep(3)
                time.sleep(2)
                
            if not logged_in:
                if "notebook/" not in page.url:
                    context.close()
                    raise Exception("Tempo limite esgotado aguardando o carregamento da página do NotebookLM. Por favor, faça login na tela exibida.")
            
            print("Área logada do NotebookLM carregada com sucesso!")
            time.sleep(3)
            
            # 2. Tratar Modais/Overlays Iniciais (Exemplo: boas-vindas ou banners)
            print("Fechando quaisquer overlays/banners pendentes...")
            page.keyboard.press("Escape")
            time.sleep(1)
            page.keyboard.press("Escape")
            time.sleep(1)
            
            try:
                # 3. Localiza e abre o modal de fontes se ele já não estiver aberto
                print("Localizando o botão 'Add Source' no painel lateral...")
                add_btn = page.locator('button[aria-label*="Add"], button[aria-label*="Adicionar"]').first
                if add_btn.is_visible():
                    add_btn.click()
                    page.wait_for_timeout(1000)
                
                # 4. Captura o seletor de arquivos local clicando na zona de upload do modal
                print("Localizando o botão de upload e iniciando o file chooser...")
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    upload_card = page.locator('mat-card, [role="button"], input[type="file"]').filter(has_text=re.compile(r"file|upload|computador|arquivo", re.I)).first
                    upload_card.click(force=True)
                    
                file_chooser = fc_info.value
                print(f"Enviando arquivos para o seletor: {upload_list}")
                file_chooser.set_files(upload_list)
                
                # 5. Aguarda o upload e o processamento inicial
                print("Arquivos enviados! Aguardando o processamento do NotebookLM...")
                try:
                    # Espera a barra de progresso de upload sumir se ela estiver visível
                    progress = page.locator('mat-progress-bar, [role="progressbar"], text="Uploading", text="Processando"')
                    if progress.count() > 0:
                        progress.first.wait_for(state="detached", timeout=30000)
                except Exception:
                    pass
                
                time.sleep(15)
                print("Upload finalizado com sucesso!")
            except Exception as upload_err:
                raise Exception(f"Erro durante o processo de upload no NotebookLM: {upload_err}")
            finally:
                context.close()

    def upload_multiple_games(self, game_uploads: dict):
        """
        Faz o upload sequencial dos arquivos para os respectivos cadernos do NotebookLM,
        reutilizando a mesma sessão do navegador do Playwright.
        """
        if not game_uploads:
            print("Nenhuma tarefa de upload de jogo fornecida.")
            return

        print(f"Iniciando Playwright para upload sequencial de {len(game_uploads)} jogos...")
        
        with sync_playwright() as p:
            # Lança o navegador com o contexto persistente
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,  # Headed para permitir login manual inicial
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            page = context.new_page()
            
            for game_id, data in game_uploads.items():
                notebook_url = data.get("url")
                file_paths = data.get("files", [])
                
                # Transforma caminhos em absolutos
                upload_list = [os.path.abspath(f) for f in file_paths if os.path.exists(f)]
                # Limita a 4 arquivos por upload
                upload_list = upload_list[:4]
                
                if not notebook_url:
                    print(f"[{game_id.upper()}] Ignorado: URL do notebook não configurada.")
                    continue
                    
                if not upload_list:
                    print(f"[{game_id.upper()}] Ignorado: Nenhum arquivo para upload encontrado.")
                    continue
                
                print(f"\n--- [{game_id.upper()}] Navegando para o Notebook: {notebook_url} ---")
                page.goto(notebook_url)
                
                # 1. Garantir Navegação no Notebook Específico
                print(f"[{game_id.upper()}] Aguardando carregamento da área logada (timeout de até 120s)...")
                start_time = time.time()
                logged_in = False
                
                while time.time() - start_time < 120:
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    
                    current_url = page.url
                    if "notebooklm.google.com" in current_url:
                        if "notebook/" in current_url:
                            logged_in = True
                            break
                        else:
                            print(f"[{game_id.upper()}] Na dashboard. Forçando navegação direta...")
                            page.goto(notebook_url)
                            time.sleep(3)
                    time.sleep(2)
                    
                if not logged_in:
                    if "notebook/" not in page.url:
                        context.close()
                        raise Exception(f"[{game_id.upper()}] Tempo limite esgotado aguardando login.")
                
                print(f"[{game_id.upper()}] Área logada carregada com sucesso!")
                time.sleep(3)
                
                # 2. Tratar Modais/Overlays Iniciais
                print(f"[{game_id.upper()}] Fechando overlays/banners pendentes...")
                page.keyboard.press("Escape")
                time.sleep(1)
                page.keyboard.press("Escape")
                time.sleep(1)
                
                try:
                    # 3. Localiza e abre o modal de fontes
                    print(f"[{game_id.upper()}] Localizando o botão 'Add Source'...")
                    add_btn = page.locator('button[aria-label*="Add"], button[aria-label*="Adicionar"]').first
                    if add_btn.is_visible():
                        add_btn.click()
                        page.wait_for_timeout(1000)
                    
                    # 4. Captura o seletor de arquivos local
                    print(f"[{game_id.upper()}] Localizando botão de upload...")
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        upload_card = page.locator('mat-card, [role="button"], input[type="file"]').filter(has_text=re.compile(r"file|upload|computador|arquivo", re.I)).first
                        upload_card.click(force=True)
                        
                    file_chooser = fc_info.value
                    print(f"[{game_id.upper()}] Enviando arquivos: {upload_list}")
                    file_chooser.set_files(upload_list)
                    
                    # 5. Aguarda o upload
                    print(f"[{game_id.upper()}] Aguardando o processamento do upload...")
                    try:
                        progress = page.locator('mat-progress-bar, [role="progressbar"], text="Uploading", text="Processando"')
                        if progress.count() > 0:
                            progress.first.wait_for(state="detached", timeout=30000)
                    except Exception:
                        pass
                    
                    time.sleep(12)
                    print(f"[{game_id.upper()}] Sincronização concluída com sucesso!")
                except Exception as upload_err:
                    print(f"[{game_id.upper()}] Erro durante o upload: {upload_err}")
                    raise upload_err
            
            context.close()
