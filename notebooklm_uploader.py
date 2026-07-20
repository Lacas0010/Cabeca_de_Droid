import os
import time
import re
from playwright.sync_api import sync_playwright

def bundle_prydwen_guides(guias_dir: str, output_file: str = "todos_os_guias_prydwen.md") -> str:
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
        
    bundled_lines = []
    # Ordena os arquivos para garantir uma ordem consistente
    for filename in sorted(md_files):
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
        full_content = "# Compilado de Guias e Builds - Prydwen\n" + "".join(bundled_lines)
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

    def upload_sources(self, notebook_url: str, file_paths: list):
        """
        Acessa o NotebookLM, aguarda o login se necessário, clica no botão de adicionar fonte
        e faz o upload dos arquivos fornecidos (após consolidação).
        """
        # Consolida os guias individuais antes de definir a lista final de upload
        upload_list = []
        for f in ["meus_personagens_hsr.md", "meta_e_tierlists_atual.md", "meta_endgame_report.md"]:
            if os.path.exists(f):
                upload_list.append(os.path.abspath(f))
                
        bundle_path = bundle_prydwen_guides("guias_prydwen", "todos_os_guias_prydwen.md")
        if bundle_path and os.path.exists(bundle_path):
            upload_list.append(bundle_path)
            
        if not upload_list:
            raise Exception("Nenhum arquivo Markdown (.md) para upload foi localizado na raiz do projeto.")

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
